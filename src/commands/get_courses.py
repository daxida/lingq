import asyncio
from pathlib import Path

from commands.get_lessons import get_lessons_async
from lingqhandler import LingqHandler
from log import logger
from utils import double_check, timing


async def get_lessons_async_rate_limited(
    semaphore: asyncio.Semaphore,
    *args,  # noqa: ANN002
    **kwargs,  # noqa: ANN003
) -> None:
    async with semaphore:
        await get_lessons_async(*args, **kwargs)


async def get_courses_for_language_async(
    language_code: str,
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    batch_size: int,
) -> None:
    # Number of courses to download in batch
    semaphore = asyncio.Semaphore(batch_size)

    async with LingqHandler(language_code) as handler:
        # This is only for the courses ID.
        # To get the text we need to do yet another request.
        my_collections = await handler.get_my_collections()
        logger.info(f"Found {my_collections.count} courses in language: {language_code}")

        # Async fetching of courses is too fast for the API...
        # for res in my_collections.results:
        #     await get_lessons_async(
        #         language_code,
        #         res.id,
        #         skip_already_downloaded=False,
        #         download_audio=download_audio,
        #         download_timestamps=download_timestamps,
        #         opath=opath,
        #         write=True,
        #         verbose=False,
        #         handler=handler,
        #     )

        await asyncio.gather(
            *(
                get_lessons_async_rate_limited(
                    semaphore,
                    language_code,
                    res.id,
                    skip_downloaded=skip_downloaded,
                    download_audio=download_audio,
                    download_timestamps=download_timestamps,
                    opath=opath,
                    write=True,
                    verbose=False,
                )
                for res in my_collections.results
            ),
        )


async def get_courses_async(
    language_codes: list[str],
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    batch_size: int,
) -> None:
    logger.info(f"Getting courses for languages: {', '.join(language_codes)}")
    double_check("CAREFUL: This reorders your 'Continue studying' shelf.")
    for language_code in language_codes:
        await get_courses_for_language_async(
            language_code,
            opath,
            download_audio=download_audio,
            download_timestamps=download_timestamps,
            skip_downloaded=skip_downloaded,
            batch_size=batch_size,
        )
        await asyncio.sleep(2)


@timing
def get_courses(
    language_codes: list[str],
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    batch_size: int = 1,
) -> None:
    """Get every course from a list of languages.

    CAREFUL: This reorders your 'Continue studying' shelf.
    """
    # If no language codes are given, use all languages.
    if not language_codes:
        language_codes = LingqHandler.get_user_language_codes()
    asyncio.run(
        get_courses_async(
            language_codes,
            opath,
            download_audio=download_audio,
            download_timestamps=download_timestamps,
            skip_downloaded=skip_downloaded,
            batch_size=batch_size,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_courses(
        language_codes=["ja"],
        download_audio=False,
        download_timestamps=False,
        skip_downloaded=False,
        opath=Path(),
    )
