# Script by @bamboozled
# https://forum.lingq.com/t/export-your-lingq-text-content-as-a-tree-of-files-to-google-drive/164914/9

import asyncio
import csv
from typing import Any, Dict, List

from lingqhandler import LingqHandler

LANGUAGE_CODE = "el"
BASE_URL = "https://www.lingq.com"


async def fetch_and_save_to_csv() -> None:
    library_data_list = await fetch_library()
    data_list = [process_json_entry(entry) for entry in library_data_list]
    data_list.sort(key=lambda x: x["roses"], reverse=True)
    write_to_csv(data_list)


async def fetch_library() -> List[Any]:
    async with LingqHandler("Filler") as handler:
        library_data_list: List[Any] = []
        page = 1
        while True:
            library_url = f"{BASE_URL}/api/v3/{LANGUAGE_CODE}/search/?level=1&level=2&level=3&level=4&level=5&level=6&sortBy=mostLiked&type=collection&page={page}"
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


def process_json_entry(entry: Any) -> Dict[str, str]:
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
        "link": f"{BASE_URL}/uni/learn/{LANGUAGE_CODE}/web/library/course/{id_value}",
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


def write_to_csv(data_list: List[Any]) -> None:
    output_filename = f"{LANGUAGE_CODE}_library.csv"

    with open(output_filename, "w", newline="", encoding="utf-8") as csv_file:
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


def main():
    asyncio.run(fetch_and_save_to_csv())


if __name__ == "__main__":
    main()
