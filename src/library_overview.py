# Script by @bamboozled
# https://forum.lingq.com/t/export-your-lingq-text-content-as-a-tree-of-files-to-google-drive/164914/9

import asyncio
import csv
from pathlib import Path
from typing import Any

from lingqhandler import LingqHandler

BASE_URL = "https://www.lingq.com"


async def fetch_and_save_to_csv(language_code: str) -> None:
    library_data_list = await fetch_library(language_code)
    data_list = [process_json_entry(language_code, entry) for entry in library_data_list]
    data_list.sort(key=lambda x: x["roses"], reverse=True)
    write_to_csv(language_code, data_list)


async def fetch_library(language_code: str) -> list[Any]:
    async with LingqHandler("Filler") as handler:
        library_data_list: list[Any] = []
        page = 1
        while True:
            library_url = f"{BASE_URL}/api/v3/{language_code}/search/?level=1&level=2&level=3&level=4&level=5&level=6&sortBy=mostLiked&type=collection&page={page}"
            library_response = await handler.session.get(
                library_url, headers=handler.config.headers
            )

            if library_response.status != 200:
                print(f"Failed to fetch data from page {page}.")
                print(f"Status code: {library_response.status}.")
                break

            library_data = await library_response.json()
            results = library_data.get("results", [])
            library_data_list.extend(results)

            next_url = library_data.get("next")
            if not next_url:
                print("No further pages")
                break
            else:
                page += 1
                print("going to page: ", page)

    return library_data_list


def process_json_entry(language_code: str, entry: Any) -> dict[str, str]:
    id_value = entry.get("id")
    title = entry.get("title")
    lessons_count = entry.get("lessonsCount")
    duration = entry.get("duration")
    level = entry.get("level")
    roses = entry.get("rosesCount")
    shared_by = entry.get("sharedByName")
    sharer_role = entry.get("sharedByRole")
    tags = entry.get("tags", "")
    status = entry.get("status", "")

    return {
        "link": f"{BASE_URL}/uni/learn/{language_code}/web/library/course/{id_value}",
        "title": title,
        "level": level,
        "lessonsCount": lessons_count,
        "duration": duration,
        "roses": roses,
        "shared_by": shared_by,
        "sharer_role": sharer_role,
        "tags": tags,
        "status": status,
    }


def write_to_csv(language_code: str, data_list: list[Any]) -> None:
    output_filename = Path(f"{language_code}_library.csv")

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

    print(f"Data saved to {output_filename}.")


def overview(language_code: str):
    asyncio.run(fetch_and_save_to_csv(language_code))


if __name__ == "__main__":
    # Defaults for manually running this script.
    overview(language_code="el")
