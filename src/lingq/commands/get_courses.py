import asyncio
from pathlib import Path

from lingq.commands.get_lessons import get_lessons_async
from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.utils import double_check, timing


async def get_lessons_async_rate_limited(
    semaphore: asyncio.Semaphore,
    *args,  # noqa: ANN002
    **kwargs,  # noqa: ANN003
) -> None:
    async with semaphore:
        await get_lessons_async(*args, **kwargs)


async def get_courses_for_language_async(
    lang: str,
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    batch_size: int,
) -> None:
    # Number of courses to download in batch
    semaphore = asyncio.Semaphore(batch_size)

    async with LingqHandler(lang) as handler:
        # This is only for the courses ID.
        # To get the text we need to do yet another request.
        my_collections = await handler.get_my_collections()
        logger.info(f"Found {my_collections.count} courses in language: {lang}")

        # Async fetching of courses is too fast for the API...
        # for res in my_collections.results:
        #     await get_lessons_async(
        #         lang,
        #         res.id,
        #         skip_already_downloaded=False,
        #         download_audio=download_audio,
        #         download_timestamps=download_timestamps,
        #         opath=opath,
        #         write=True,
        #         handler=handler,
        #     )

        await asyncio.gather(
            *(
                get_lessons_async_rate_limited(
                    semaphore,
                    lang,
                    res.id,
                    skip_downloaded=skip_downloaded,
                    download_audio=download_audio,
                    download_timestamps=download_timestamps,
                    opath=opath,
                    write=True,
                    with_index=False,
                )
                for res in my_collections.results
            ),
        )


async def get_courses_async(
    langs: list[str],
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    batch_size: int,
    assume_yes: bool,
) -> None:
    logger.info(f"Getting courses for languages: {', '.join(langs)}")
    double_check("CAREFUL: This reorders your 'Continue studying' shelf.", assume_yes)
    for lang in langs:
        await get_courses_for_language_async(
            lang,
            opath,
            download_audio=download_audio,
            download_timestamps=download_timestamps,
            skip_downloaded=skip_downloaded,
            batch_size=batch_size,
        )
        await asyncio.sleep(2)


@timing
def get_courses(
    langs: list[str],
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    batch_size: int = 1,
    assume_yes: bool = False,
) -> None:
    """Get all courses for the given languages.

    CAREFUL: This reorders your 'Continue studying' shelf.

    If no language codes are given, use all languages.
    """
    if not langs:
        langs = LingqHandler.get_user_langs()
    asyncio.run(
        get_courses_async(
            langs,
            opath,
            download_audio=download_audio,
            download_timestamps=download_timestamps,
            skip_downloaded=skip_downloaded,
            batch_size=batch_size,
            assume_yes=assume_yes,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_courses(
        langs=["ja"],
        download_audio=False,
        download_timestamps=False,
        skip_downloaded=False,
        opath=Path(),
    )
