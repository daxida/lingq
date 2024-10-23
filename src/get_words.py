import asyncio
import json
import os
from math import ceil
from typing import Any

from lingqhandler import LingqHandler
from models.cards import Card, Cards
from utils import timing

# List of JSON-like dumps of the Word model
WordDump = list[dict[str, Any]]


async def _get_words_for_language(language_code: str, page_size: int = 500) -> WordDump:
    """
    Get all LingQs for the given language.

    The LingQ API throttles downloads:
        - The API default page_size is 100 (with a max of 1000 words per page).
    """
    assert page_size <= 1000  # The API itself clamps it to 1000 anyway

    async with LingqHandler(language_code) as handler:
        url = f"https://www.lingq.com/api/v3/{language_code}/cards/"
        next_url = f"{url}?page=1&page_size={page_size}"
        words: list[Card] = []
        step = 1
        total_pages = None

        while next_url:
            async with handler.session.get(next_url, headers=handler.config.headers) as response:
                cards_json = await response.json()
                cards = Cards.model_validate(cards_json)

            if step == 1:
                print(f"Getting {cards.count} lingqs for {language_code}...")
                total_pages = ceil(cards.count / page_size)

            words.extend(cards.results)
            print(f"Progress: {step}/{total_pages} pages")
            # print(next_url)
            # print(len(words))

            next_url = cards.next
            step += 1
            # await asyncio.sleep(1)

        dump = [word.model_dump() for word in words]
        return dump


def write_words_for_language(language_code: str, download_folder: str, dump: WordDump) -> None:
    """Write the word dump for a specific language."""
    dump_path = os.path.join(download_folder, language_code)
    os.makedirs(dump_path, exist_ok=True)
    lingq_json_path = os.path.join(dump_path, "lingqs.json")
    with open(lingq_json_path, "w") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2)


async def _get_words(language_codes: list[str], download_folder: str) -> None:
    for language_code in language_codes:
        dump = await _get_words_for_language(language_code)
        write_words_for_language(language_code, download_folder, dump)


@timing
def get_words(language_codes: list[str], download_folder: str) -> None:
    """
    Get my words (LingQs) from a language.
    If no language codes are given, use all languages.
    """
    if not language_codes:
        language_codes = LingqHandler.get_user_language_codes()
    print(f"Getting words for languages: {', '.join(language_codes)}")
    asyncio.run(_get_words(language_codes, download_folder))


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_words(
        language_codes=["de"],
        download_folder="downloads/lingqs",
    )
