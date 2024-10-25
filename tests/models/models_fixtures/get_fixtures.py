import json
import re
from pathlib import Path

import requests
from dotenv import dotenv_values, find_dotenv

API_KEY = dotenv_values(find_dotenv())["APIKEY"]
HEADERS = {"Authorization": f"Token {API_KEY}"}
LC_PATTERN = r"https://www.lingq.com/api/v3/([a-z]{2})/([a-z]+)/"
FIXTURES_PATH = Path("tests/models/models_fixtures")


def get_and_write_url(url: str) -> None:
    data = requests.get(url, headers=HEADERS).json()
    mtch = re.match(LC_PATTERN, url)
    assert not mtch is None
    language_code = mtch.group(1)
    url_type = mtch.group(2)
    folder_path = FIXTURES_PATH / url_type
    Path.mkdir(folder_path, parents=True, exist_ok=True)
    file_path = folder_path / f"{language_code}.json"
    with file_path.open("w") as json_file:
        json.dump(data, json_file, indent=4)


def make_model_fixtures() -> None:
    collection_urls = [
        "https://www.lingq.com/api/v3/ja/collections/537808/",
        "https://www.lingq.com/api/v3/el/collections/1070313/",
        "https://www.lingq.com/api/v3/de/collections/600154/",
        "https://www.lingq.com/api/v3/fr/collections/51271/",
        "https://www.lingq.com/api/v3/es/collections/51748/",
        "https://www.lingq.com/api/v3/en/collections/636814/",
        "https://www.lingq.com/api/v3/it/collections/48487/",
        "https://www.lingq.com/api/v3/pt/collections/979632/",
    ]
    lesson_urls = [
        "https://www.lingq.com/api/v3/ja/lessons/34955431/",
        "https://www.lingq.com/api/v3/el/lessons/5897069/",
        "https://www.lingq.com/api/v3/de/lessons/35536/",
        "https://www.lingq.com/api/v3/fr/lessons/95641/",
        "https://www.lingq.com/api/v3/es/lessons/100342/",
        "https://www.lingq.com/api/v3/en/lessons/4195540/",
        "https://www.lingq.com/api/v3/it/lessons/82921/",
        "https://www.lingq.com/api/v3/pt/lessons/10047283/",
    ]

    for url in lesson_urls:
        get_and_write_url(url)
    for url in collection_urls:
        get_and_write_url(url)


if __name__ == "__main__":
    make_model_fixtures()
