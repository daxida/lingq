import asyncio
import re

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.collection_v3 import CollectionLessonResult
from lingq.utils import sort_by_greek_words_impl, timing

ST = tuple[float, ...]
"""Return type of a sorting function."""


def sorting_function(lesson: CollectionLessonResult) -> ST:
    # Implement and replace your sorting logic here
    # return sort_by_reverse_split_numbers(lesson)
    return sort_by_versioned_numbers(lesson)


def sort_by_reverse_split_numbers(lesson: CollectionLessonResult) -> ST:
    # NOTE: I think this is the standard now in LingQ.
    # This assumes that the chapters are labelled with numbers.
    # That is: Chapter1 => 1.txt, Chapter2 => 2.txt etc.
    # 1:1 < 2:1 < 1:2 < 2:2 (the section number goes first).
    title = lesson.title
    if ":" not in title:
        return (float(title), float("inf"))
    else:
        section_num, title = title.split(": ")
        return (float(title), float(section_num))


def sort_by_versioned_numbers(lesson: CollectionLessonResult) -> ST:
    # 1. Title < 1.1 OtherTitle < 1.2. Another < 2. LastTitle < TitleWithoutNumber
    return sort_by_versioned_numbers_impl(lesson.title)


def sort_by_versioned_numbers_impl(word: str) -> ST:
    m = re.findall(r"^[\d.]+", word)
    if m and (trimmed := m[0].strip(".")):
        nums = tuple(float(num) for num in trimmed.split("."))
    else:
        nums = (float("inf"),)

    # Guarantee version comparison finishes first
    key = (*nums, float("-inf"))

    # Tie breaker only if versions are exactly equal
    key += tuple(float(ord(c)) for c in word)
    return key


def sort_by_greek_words(lesson: CollectionLessonResult) -> ST:
    return sort_by_greek_words_impl(lesson.title)


def longest_increasing_subsequence(lst: list[int]) -> list[int]:
    n = len(lst)
    dp = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if lst[j] < lst[i] and dp[i] < dp[j] + 1:
                dp[i] = dp[j] + 1
                prev[i] = j

    max_sz = max(dp)
    solutions = [idx for idx in range(len(dp)) if dp[idx] == max_sz]

    res: list[int] = []
    pos = solutions[0]
    while pos != -1:
        res.append(lst[pos])
        pos = prev[pos]

    return res[::-1]


def get_patch_requests_order_for_ids(
    lessons_ids: list[int], to_reorder: list[int]
) -> list[tuple[int, int]]:
    """This is just a possible solution to the problem. Maybe there is a simpler
    approach that equally finds some requests needed to sort the lessons."""
    fix_members = [0] + [elt for elt in lessons_ids if elt not in to_reorder]
    requests_with_ids: list[tuple[int, int]] = []

    for lesson_id in to_reorder:
        first_bigger_fix_member_idx = len(fix_members)
        for nidx, member in enumerate(fix_members):
            if member > lesson_id:
                first_bigger_fix_member_idx = nidx
                break
        first_bigger_fix_member_idx -= 1

        should_go_after_this = fix_members[first_bigger_fix_member_idx]
        fix_members.insert(first_bigger_fix_member_idx + 1, lesson_id)
        if should_go_after_this in lessons_ids:
            should_go = lessons_ids.index(should_go_after_this) + 1
        else:
            should_go = 0

        lesson_idx = lessons_ids.index(lesson_id)
        lessons_ids.pop(lesson_idx)
        offset = 1 if should_go > lesson_idx else 0
        lessons_ids.insert(should_go - offset, lesson_id)
        requests_with_ids.append((lesson_id, should_go - offset + 1))

    return requests_with_ids


def get_patch_requests_order(
    lessons: list[CollectionLessonResult],
) -> list[tuple[CollectionLessonResult, int]]:
    """Faster (and way more complicated) version to minimize the number of requests.
    Uses a longest increasing subsequence to identify the lessons that should
    not be moved around, then computes some possible requests that sort the lessons."""
    sorted_lessons = sorted(lessons, key=sorting_function)
    sorted_idxs: dict[str, int] = {}
    for idx, sorted_lesson in enumerate(sorted_lessons, 1):
        sorted_idxs[sorted_lesson.title] = idx
    lessons_ids_mapping: dict[int, CollectionLessonResult] = {
        sorted_idxs[lesson.title]: lesson for lesson in lessons
    }
    lessons_ids: list[int] = list(lessons_ids_mapping.keys())

    lis = longest_increasing_subsequence(lessons_ids)
    to_reorder = sorted(lesson_id for lesson_id in lessons_ids if lesson_id not in lis)
    logger.debug(f"We need to reorder '{len(to_reorder)}' lessons.")  # Optimal

    requests_with_ids = get_patch_requests_order_for_ids(lessons_ids, to_reorder)
    requests = [(lessons_ids_mapping[lesson_id], pos) for lesson_id, pos in requests_with_ids]

    return requests


async def sort_lessons_async(lang: str, course_id: int, *, dry_run: bool) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        patch_requests = get_patch_requests_order(lessons)
        if not patch_requests:
            return
        if dry_run:
            msg = "\n".join([str((les.title, pos)) for les, pos in patch_requests])
            logger.debug(f"Sorting requests:\n{msg}")
            return
        for lesson, pos in patch_requests:
            await handler.patch_position(lesson.id, pos)

        # Simple solution. Note that sends a patch request per lesson (too slow).

        # lessons.sort(key=sorting_function)
        # for pos, lesson in enumerate(lessons, 1):
        #     await handler.patch_position(lesson.id, pos)

        logger.success(f"Finished sorting {collection_title}.")


@timing
def sort_lessons(lang: str, course_id: int, *, dry_run: bool = False) -> None:
    """Sort course lessons."""
    asyncio.run(sort_lessons_async(lang, course_id, dry_run=dry_run))


if __name__ == "__main__":
    # Defaults for manually running this script.
    sort_lessons(lang="ja", course_id=537808)
