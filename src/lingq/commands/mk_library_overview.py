# Script by @bamboozled
# https://forum.lingq.com/t/export-your-lingq-text-content-as-a-tree-of-files-to-google-drive/164914/9

import asyncio
import csv
from pathlib import Path
from typing import Any

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.collection_v3 import SearchCollectionResult, SearchCollections

BASE_URL = "https://www.lingq.com"


async def fetch_and_save_to_csv(lang: str) -> None:
    library = await fetch_library(lang)
    simple_library = [process_json_entry(lang, sres) for sres in library]
    simple_library.sort(key=lambda x: x["roses"], reverse=True)
    write_to_csv(lang, simple_library)


async def fetch_library(lang: str) -> list[SearchCollectionResult]:
    library: list[SearchCollectionResult] = []

    async with LingqHandler(lang) as handler:
        page = 1
        while True:
            search: SearchCollections = await handler.search(
                {
                    "type": "collection",
                    "sortBy": "mostLiked",
                    "page": page,
                    "level": [1, 2, 3, 4, 5, 6],
                }
            )

            results = search.results
            logger.info(f"Got page {page}")
            library.extend(results)
            page += 1
            if not search.next:
                break

    return library


def process_json_entry(lang: str, sres: SearchCollectionResult) -> dict[str, str]:
    return {
        "link": f"{BASE_URL}/uni/learn/{lang}/web/library/course/{sres.id}",
        "title": sres.title,
        "level": sres.level or "-1",
        "lessonsCount": str(sres.lessons_count),
        "duration": str(sres.duration),
        "roses": str(sres.roses_count),
        "shared_by": sres.shared_by_name,
        "sharer_role": sres.shared_by_role or "",
        "tags": ", ".join(sres.tags),
        "status": sres.status,
    }


def write_to_csv(lang: str, data_list: list[Any]) -> None:
    output_filename = Path(f"{lang}_library.csv")

    with output_filename.open("w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "link",
            "title",
            "level",
            "lessonsCount",
            "duration",
            "roses",
            "shared_by",
            "sharer_role",
            "tags",
            "status",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for data in data_list:
            writer.writerow(data)

    logger.success(f"Data saved to {output_filename}.")


def overview(lang: str) -> None:
    """Make a library overview."""
    asyncio.run(fetch_and_save_to_csv(lang))


if __name__ == "__main__":
    # Defaults for manually running this script.
    overview(lang="el")
