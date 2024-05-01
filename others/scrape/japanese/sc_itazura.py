"""Scrape a book from https://itazuranekoyomi.neocities.org/library/shousetu/shouall"""

import os
from typing import Any

import requests
from bs4 import BeautifulSoup

BOOK_ID = "satu000987/satu000987"
BOOK_NAME = "かがみの孤城"  # name for the out_folder
# Inspect and find the first section after contents, pictures etc.
# The download will start from this section (included) onwards.
FIRST_RELEVANT_SECTION = "39"


def filter_sections(sections: Any) -> Any:
    # Remove useless starting sections
    idx_relevant = 0
    for idx, section in enumerate(sections):
        section_id = section.get("id")
        if section_id and FIRST_RELEVANT_SECTION in section_id:
            idx_relevant = idx
            break
    sections = sections[idx_relevant:]
    # Remove sections with no text (pictures etc.)
    sections = [s for s in sections if s.text.strip()]
    return sections


def remove_ruby(section: Any) -> Any:
    for ruby in section.find_all("ruby"):
        ruby.replace_with(ruby.text)
    for element in section.find_all("p"):
        element.string = element.get_text(strip=True)


os.makedirs(BOOK_NAME, exist_ok=True)

res = None
for mirror in range(1, 4):
    url = f"https://itazuranekoyomi{mirror}.neocities.org/library/shousetu/volume/{BOOK_ID}"
    res = requests.get(url)
    if res.status_code == 200:
        break
assert res is not None, "Could not find the book in itazura."

soup = BeautifulSoup(res.content, "html.parser")
body = soup.find("div", {"class": "bodymargin"})
sections = body.find_all("div", id=lambda x: x and "calibre" in x)  # type: ignore
chapters = filter_sections(sections)

for idx, chapter in enumerate(chapters, 1):
    remove_ruby(chapter)

    # chapter_title = f"{idx} {chapter.get('id')}"
    chapter_title = str(idx)
    chapter_text = chapter.text.strip()

    chapter_path = f"{BOOK_NAME}/{chapter_title}"
    with open(chapter_path, "w") as f:
        f.write(chapter_text)
