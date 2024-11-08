"""Scrape a book from https://ncode.syosetu.com/"""

from pathlib import Path

import requests
from bs4 import BeautifulSoup

DOWNLOAD_FOLDER = Path("downloads")

BOOK_ID = "n9636x"  # get this from the url
BOOK_NAME = "syosetu"  # name for the out_folder

FAKE_BROWSER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64)",
    "accept-language": "en-US,en;q=0.9,ja;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}

book_path = DOWNLOAD_FOLDER / BOOK_NAME
Path.mkdir(book_path, parents=True, exist_ok=True)

url = f"https://ncode.syosetu.com/{BOOK_ID}/"
print(f"GET {url}")
res = requests.get(url, headers=FAKE_BROWSER_HEADERS)
soup = BeautifulSoup(res.content, "html.parser")

n_chapters = len(soup.find_all("div", class_="p-eplist__sublist"))
print(f"Found {n_chapters} chapters.")

for chapter_id in range(1, n_chapters + 1):
    url_chapter = f"{url}{chapter_id}/"
    cres = requests.get(url_chapter, headers=FAKE_BROWSER_HEADERS)
    csoup = BeautifulSoup(cres.content, "html.parser")

    chapter_text = csoup.find("div", class_="p-novel__body").text  # type: ignore
    chapter_title = csoup.find("h1", class_="p-novel__title p-novel__title--rensai").text  # type: ignore

    chapter_path = book_path / chapter_title
    with chapter_path.open("w") as f:
        f.write(chapter_text)

print(f"Wrote text at {book_path}")
