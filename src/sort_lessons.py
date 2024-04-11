import asyncio
import re
from typing import Any, List, Tuple, Dict

from lingqhandler import LingqHandler
from utils import timing  # type: ignore

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"


def sorting_function(lesson: Any):
    # Implement and replace your sorting logic here
    return sort_by_versioned_numbers(lesson)


def sort_by_versioned_numbers(lesson: Any):
    # 1. Title < 1.1 OtherTitle < 1.2. Another < 2. LastTitle < TitleWithoutNumber
    title = lesson["title"]
    m = re.findall(r"^[\d.]+", title)
    if m:
        trimmed = m[0].strip(".")
        nums = trimmed.split(".")
        starting_number = tuple(int(num) for num in nums)
    else:
        starting_number = 1e9
    return (starting_number, title)


def longest_increasing_subsequence(lst: List[int]) -> List[int]:
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

    res: List[int] = list()
    pos = solutions[0]
    while pos != -1:
        res.append(lst[pos])
        pos = prev[pos]

    return res[::-1]


def get_patch_requests_order_for_ids(
    lessons_ids: List[int], to_reorder: List[int]
) -> List[Tuple[int, int]]:
    """This is just a possible solution to the problem. Maybe there is a simpler
    approach that equally finds some requests needed to sort the lessons."""
    fix_members = [0] + [elt for elt in lessons_ids if elt not in to_reorder]
    requests_with_ids: List[Tuple[int, int]] = list()

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


def get_patch_requests_order(lessons: List[Any]) -> List[Tuple[Any, int]]:
    """Faster (and way more complicated) version to minimize the number of requests.
    Uses a longest increasing subsequence to identify the lessons that should
    not be moved around, then computes some possible requests that sort the lessons."""
    sorted_lessons = sorted(lessons, key=sorting_function)
    sorted_idxs: Dict[str, int] = dict()
    for idx, sorted_lesson in enumerate(sorted_lessons, 1):
        sorted_idxs[sorted_lesson["title"]] = idx
    lessons_ids_mapping: Dict[int, Any] = {
        sorted_idxs[lesson["title"]]: lesson for lesson in lessons
    }
    lessons_ids: List[int] = list(lessons_ids_mapping.keys())

    lis = longest_increasing_subsequence(lessons_ids)
    to_reorder = sorted(lesson_id for lesson_id in lessons_ids if lesson_id not in lis)
    print(f"We need to reorder '{len(to_reorder)}' lessons.")  # Optimal

    requests_with_ids = get_patch_requests_order_for_ids(lessons_ids, to_reorder)
    requests = [(lessons_ids_mapping[lesson_id], pos) for lesson_id, pos in requests_with_ids]

    return requests


async def sort_lessons(language_code: str, course_id: str):
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        lessons = collection_json["lessons"]
        patch_requests = get_patch_requests_order(lessons)
        for lesson, pos in patch_requests:
            # print(f"Sent: {lesson['title']} {pos}")
            await handler.patch(lesson, {"pos": pos})

        # Simple solution. NOTE: sends a patch request per lesson (too slow).
        # lessons.sort(key=sorting_function)
        # for pos, lesson in enumerate(lessons, 1):
        #     payload = {"pos": pos}
        #     await handler.patch(lesson, payload)

        print(f"Finished sorting {collection_json['title']}")


@timing
def main():
    asyncio.run(sort_lessons(LANGUAGE_CODE, COURSE_ID))


if __name__ == "__main__":
    main()
