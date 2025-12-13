import asyncio
import json
from math import ceil
from pathlib import Path
from typing import Any

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.cards import Card, Cards
from lingq.utils import timing

# List of JSON-like dumps of the Word model
WordDump = list[dict[str, Any]]


async def get_words_for_language_async(lang: str, page_size: int = 500) -> WordDump:
    """Get all LingQs for the given language.

    The LingQ API clamps page size:
        - The API default page_size is 100 (with a clamped max of 1000 words per page).
    """
    async with LingqHandler(lang) as handler:
        url = f"https://www.lingq.com/api/v3/{lang}/cards/"
        cur_url = f"{url}?page=1&page_size={page_size}"
        words: list[Card] = []
        step = 1
        total_pages = None

        while cur_url:
            async with handler.session.get(cur_url, headers=handler.config.headers) as response:
                cards_json = await response.json()
                cards = Cards.model_validate(cards_json)

            if step == 1:
                logger.info(f"Getting {cards.count} lingqs for {lang}...")
                total_pages = ceil(cards.count / page_size)

            words.extend(cards.results)
            logger.info(f"Progress: {step}/{total_pages} pages")
            logger.trace(cur_url)

            cur_url = cards.next
            step += 1
            # await asyncio.sleep(1)

        dump = [word.model_dump() for word in words]
        return dump


def write_words_for_language(lang: str, opath: Path, dump: WordDump) -> None:
    """Write the word dump for a specific language."""
    dump_folder_path = opath / "lingqs" / lang
    Path.mkdir(dump_folder_path, parents=True, exist_ok=True)
    dump_path = dump_folder_path / "lingqs.json"
    with dump_path.open("w") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2)
    logger.success(f"Wrote words at {dump_path}")


async def get_words_async(langs: list[str], opath: Path) -> None:
    for lang in langs:
        dump = await get_words_for_language_async(lang)
        write_words_for_language(lang, opath, dump)


@timing
def get_words(langs: list[str], opath: Path) -> None:
    """Get all words (LingQs) for the given languages.

    If no language codes are given, use all languages.
    """
    if not langs:
        langs = LingqHandler.get_user_langs()
    logger.info(f"Getting words for languages: {', '.join(langs)}")
    asyncio.run(get_words_async(langs, opath))


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_words(
        langs=["pt"],
        opath=Path("downloads/lingqs"),
    )
