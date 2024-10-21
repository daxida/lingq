import asyncio

from get_lessons import _get_lessons
from lingqhandler import LingqHandler
from utils import double_check, timing  # type: ignore


async def _get_courses_for_language(
    language_code: str, download_audio: bool, sleep_time: int, download_folder: str
) -> None:
    async with LingqHandler(language_code) as handler:
        # This is only for the courses ID, since in order to get the text we need
        # to do yet another request handled through `get_collection_from_id`
        collections_json = await handler.get_my_collections()
        print(f"Found {len(collections_json)} courses in language: {language_code}")

        # Async fetching of courses is too fast for the API...
        for collection_json in collections_json:
            await _get_lessons(
                language_code,
                collection_json["id"],
                skip_already_downloaded=False,
                download_audio=download_audio,
                download_folder=download_folder,
                write=True,
                verbose=False,
            )
        await asyncio.sleep(sleep_time)


async def _get_courses(
    language_codes: list[str], download_audio: bool, sleep_time: int, download_folder: str
) -> None:
    print(f"Getting courses for languages: {', '.join(language_codes)}")
    double_check("CAREFUL: This reorders your 'Continue studying' shelf.")
    for language_code in language_codes:
        await _get_courses_for_language(language_code, download_audio, sleep_time, download_folder)
        await asyncio.sleep(sleep_time)


@timing
def get_courses(
    language_codes: list[str], download_audio: bool, sleep_time: int, download_folder: str
) -> None:
    """
    Get every course from a list of languages.

    CAREFUL: This reorders your 'Continue studying' shelf.

    Args:
        language_codes (list[str]): List of language codes to process.
            If no language codes are given, use all languages.
        download_audio (bool): If True, downloads audio files for the courses.
        sleep_time (int): The sleep time between requests to prevent timeouts.

    NOTE: 'Attempt to decode JSON with unexpected mimetype: text/html; charset=utf-8'
          is probably a timeout issue. Try to slow down the requests by increasing sleep time.
          (RARE) It can also be due to a 500 error: Internal server error.
          You should check the lesson itself to see if you can open it in the browser.
    """
    # If no language codes are given, use all languages.
    if not language_codes:
        language_codes = LingqHandler.get_user_language_codes()
    asyncio.run(_get_courses(language_codes, download_audio, sleep_time, download_folder))


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_courses(language_codes=["ja"], download_audio=False, sleep_time=2, download_folder=".")
