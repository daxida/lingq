"""Scrape a book from https://ncode.syosetu.com/"""

import os

import requests
from bs4 import BeautifulSoup

BOOK_ID = "n9636x"
BOOK_NAME = "book"  # name for the out_folder

FAKE_BROWSER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
    "accept-language": "en-US,en;q=0.9,ja;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}

os.makedirs(BOOK_NAME, exist_ok=True)

url = f"https://ncode.syosetu.com/{BOOK_ID}/"
res = requests.get(url, headers=FAKE_BROWSER_HEADERS)
soup = BeautifulSoup(res.content, "html.parser")
n_chapters = len(soup.find_all("dl"))

for chapter_id in range(1, n_chapters + 1):
    url_chapter = f"{url}{chapter_id}/"
    cres = requests.get(url_chapter, headers=FAKE_BROWSER_HEADERS)
    csoup = BeautifulSoup(cres.content, "html.parser")

    chapter_text = csoup.find("div", {"id": "novel_honbun"}).text  # type: ignore
    chapter_title = csoup.find("p", {"class": "novel_subtitle"}).text  # type: ignore

    chapter_path = f"{BOOK_NAME}/{chapter_title}"
    with open(chapter_path, "w") as f:
        f.write(chapter_text)
