import json
import re
from pathlib import Path

import requests
from dotenv import dotenv_values, find_dotenv

API_KEY = dotenv_values(find_dotenv())["APIKEY"]
HEADERS = {"Authorization": f"Token {API_KEY}"}
LC_PATTERN = r"https://www.lingq.com/api/v3/[a-z]{2}/([a-z]+)/"
FIXTURES_PATH = Path("tests/models/models_fixtures")


def get_and_write_url(url: str, title: str) -> None:
    data = requests.get(url, headers=HEADERS).json()
    mtch = re.match(LC_PATTERN, url)
    assert not mtch is None
    url_type = mtch.group(1)
    folder_path = FIXTURES_PATH / url_type
    Path.mkdir(folder_path, parents=True, exist_ok=True)
    file_path = folder_path / f"{title}.json"
    with file_path.open("w") as json_file:
        json.dump(data, json_file, indent=4)


def make_model_fixtures() -> None:
    collection_urls = [
        ("https://www.lingq.com/api/v3/ja/collections/537808/", "ja"),
        ("https://www.lingq.com/api/v3/el/collections/1070313/", "el"),
        ("https://www.lingq.com/api/v3/de/collections/600154/", "de"),
        ("https://www.lingq.com/api/v3/fr/collections/51271/", "fr"),
        ("https://www.lingq.com/api/v3/es/collections/51748/", "es"),
        ("https://www.lingq.com/api/v3/en/collections/636814/", "en"),
        ("https://www.lingq.com/api/v3/it/collections/48487/", "it"),
        ("https://www.lingq.com/api/v3/pt/collections/979632/", "pt"),
        ("https://www.lingq.com/api/v3/el/collections/730129/", "el2"),
        ("https://www.lingq.com/api/v3/el/collections/1691611/", "el3"),
    ]

    lesson_urls = [
        ("https://www.lingq.com/api/v3/ja/lessons/34955431/", "ja"),
        ("https://www.lingq.com/api/v3/el/lessons/5897069/", "el"),
        ("https://www.lingq.com/api/v3/de/lessons/35536/", "de"),
        ("https://www.lingq.com/api/v3/fr/lessons/95641/", "fr"),
        ("https://www.lingq.com/api/v3/es/lessons/100342/", "es"),
        ("https://www.lingq.com/api/v3/en/lessons/4195540/", "en"),
        ("https://www.lingq.com/api/v3/it/lessons/82921/", "it"),
        ("https://www.lingq.com/api/v3/pt/lessons/10047283/", "pt"),
        ("https://www.lingq.com/api/v3/el/lessons/5879887/", "el2"),
        ("https://www.lingq.com/api/v3/ja/lessons/6916156/", "ja2"),
    ]

    for url, title in lesson_urls:
        get_and_write_url(url, title)
    for url, title in collection_urls:
        get_and_write_url(url, title)


if __name__ == "__main__":
    make_model_fixtures()
