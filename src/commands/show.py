import asyncio

from lingqhandler import LingqHandler
from models.collection_v3 import CollectionLessonResult
from models.counter import Counter


async def get_my_collections_titles_async(
    lang: str, shared: bool, codes: bool, verbose: bool = True
) -> list[str]:
    async with LingqHandler(lang) as handler:
        if shared:
            collections = await handler.get_my_collections_shared()
        else:
            my_collections = await handler.get_my_collections()
            collections = my_collections.results

        if verbose:
            collection_ids = [c.id for c in collections]
            counters = await handler.counters(collection_ids)

        titles = []
        for collection in collections:
            if codes:
                title = f"{collection.id:>7} {collection.title}"
            else:
                title = collection.title

            if verbose:
                counter = counters[str(collection.id)]  # type: ignore
                prefix = get_emojis_for_collection(counter)
                reader_url = (
                    f"https://www.lingq.com/uni/learn/{lang}/web/library/course/{collection.id}"
                )
                title = f"{prefix} {title} \033[93m{reader_url}\033[0m"

            titles.append(title)

        return titles


def get_emojis_for_collection(counter: Counter) -> str:
    none_emoji = "⬛"
    emojis = [
        "✅" if counter.progress == 100.0 else none_emoji,
    ]
    return "".join(emojis)


async def get_course_titles_async(
    lang: str,
    course_id: int,
    shared: bool,
    codes: bool,
    verbose: bool,
) -> list[str]:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)

        titles = []
        for lesson in lessons:
            if shared and lesson.status != "shared":
                continue

            if codes:
                title = f"{lesson.id:>7} {lesson.title}"
            else:
                title = lesson.title

            if verbose:
                prefix = get_emojis_for_lesson(lesson)
                reader_url = f"https://www.lingq.com/uni/learn/{lang}/web/reader/{lesson.id}"
                title = f"{prefix} {title} \033[93m{reader_url}\033[0m"

            titles.append(title)

        return titles


def get_emojis_for_lesson(lesson: CollectionLessonResult) -> str:
    none_emoji = "⬛"
    emojis = [
        "✅" if lesson.percent_completed == 100.0 else none_emoji,
        "🔈" if lesson.audio else none_emoji,
        "🔄" if lesson.status == "shared" else none_emoji,
    ]
    return "".join(emojis)


def show_my(
    lang: str,
    *,
    shared: bool,
    codes: bool,
    verbose: bool,
) -> None:
    """Show my collections in a given language."""
    titles = asyncio.run(get_my_collections_titles_async(lang, shared, codes, verbose))
    for idx, title in enumerate(titles, 1):
        print(f"{idx:02}: {title}")


def show_course(
    lang: str,
    course_id: int,
    *,
    shared: bool,
    codes: bool,
    verbose: bool,
) -> None:
    """Show lessons in a course."""
    titles = asyncio.run(get_course_titles_async(lang, course_id, shared, codes, verbose))
    for idx, title in enumerate(titles, 1):
        print(f"{idx:02}: {title}")


if __name__ == "__main__":
    show_my(lang="de", shared=False, codes=True, verbose=True)
    # show_course(
    #     lang="de",
    #     course_id=600154,
    #     shared=False,
    #     codes=False,
    #     verbose=True,
    # )
