"""Scrape a book from https://www.sosekiproject.org/"""

from pathlib import Path

import requests
from bs4 import BeautifulSoup

BOOK_NAME = "botchan"

DOWNLOAD_FOLDER = Path("downloads")
book_path = DOWNLOAD_FOLDER / BOOK_NAME
tpath = book_path / "texts"
apath = book_path / "audios"
Path.mkdir(tpath, parents=True, exist_ok=True)
Path.mkdir(apath, parents=True, exist_ok=True)

BASE_URL = "https://www.sosekiproject.org"
book_url = f"{BASE_URL}/{BOOK_NAME}"

for chapter in range(1, 999):
    chapter_url = f"{book_url}/{BOOK_NAME}chapter{chapter:02d}.html"
    print(f"GET {chapter_url}")
    res = requests.get(chapter_url)
    if res.status_code == 404:
        print(f"Could not find chapter {chapter}. Stopping.")
        break
    soup = BeautifulSoup(res.content, "html.parser")

    # The html is structured as:
    # <ul class="section_break"> etc. </ul> <- contains audio
    # <p  class="japanese"> etc. </p>       <- section paragraph
    # <p  class="japanese"> etc. </p>
    # <ul class="section_break"> etc. </ul>
    # <p  class="japanese"> etc. </p>
    # <p  class="japanese"> etc. </p>
    # <p  class="japanese"> etc. </p>
    # etc.
    elmts = soup.find_all(
        lambda tag: (
            (tag.name == "ul" and "section_break" in tag.get("class", []))
            or (tag.name == "p" and "japanese" in tag.get("class", []))
        )
    )
    sections = []
    section = {}

    for element in elmts:
        if element.name == "ul":
            if section:
                sections.append(section)
            title, _, source = element.find_all("li")
            source = source.find("source")["src"]
            audio_url = f"{book_url}/{source}"
            section = {"title": title.text, "audio_url": audio_url, "text": []}
        elif element.name == "p":
            for vocabdef in element.find_all("span", class_="vocabdef"):
                vocabdef.replaceWith("")
            section["text"].append(element.text + "\n")

    if section:
        sections.append(section)

    # Writing text and audio
    for section in sections:
        sidx = int(section["title"].split()[1])
        title = f"C{chapter:03d}-S{sidx:03d}"
        with (tpath / f"{title}.txt").open("w") as f:
            f.writelines(section["text"])

        audio = requests.get(section["audio_url"])
        with (apath / f"{title}.mp3").open("wb") as f:
            f.write(audio.content)
