"""Scrape a book from greek-language.

https://www.greek-language.gr/
https://www.greek-language.gr/digitalResources/ancient_greek/library/index.html
"""

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DOWNLOAD_FOLDER = Path("downloads")


def download_book_from_text_id(
    text_id: str,
    text_name: str,
    author_name: str,
    *,
    fr_page: int = 1,
    to_page: int = 999,
    # Set this to True when downloading theatrical texts.
    fmt_theater: bool = True,
) -> None:
    """Scrape a book given its id.

    The book id is found as `text_id=number` in the url.
    """
    if author_name:
        subpath = Path(author_name) / text_name
    else:
        subpath = Path(text_name)

    path = DOWNLOAD_FOLDER / subpath
    path.mkdir(parents=True, exist_ok=True)
    print(f"Writing at {path}")

    for page in range(fr_page, to_page):
        url = f"https://www.greek-language.gr/digitalResources/ancient_greek/library/browse.html?text_id={text_id}&page={page}"
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")

        page_text_res = soup.find("div", {"id": "translation_text"})
        if page_text_res is None:
            break  # The book is over

        if fmt_theater:
            process_html(page_text_res)

        page_text = page_text_res.text
        page_title = soup.find("div", {"class": "part-header"}).find("h3").text  # type: ignore
        out_page_title = f"{page:03d}. {page_title}.txt"
        opath = path / out_page_title
        with opath.open("w") as f:
            f.write(page_text)


def process_html(soup) -> None:  # noqa: ANN001
    """Clean up the html for theatrical texts."""
    for names in soup.find_all("span", class_="name"):
        names.replace_with(f"\n[{names.string.strip()}]")

    for numbers in soup.find_all("span", class_="numbering"):
        numbers.replace_with("")

    for italics in soup.find_all("i"):
        italics.replace_with(f"({italics.string})")


def download_books_from_author_id(author_id: str, *, fmt_theater: bool = False) -> None:
    """Scrape all books from an author id.

    The author id is found as `author_id=number` in the url.
    """
    url = f"https://www.greek-language.gr/digitalResources/ancient_greek/library/index.html?start=0&author_id={author_id}"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")

    author_name = soup.find("h1", {"class": "author"}).text  # type: ignore
    range_info = soup.find("div", {"class": "pull-left"}).text  # type: ignore
    n_books, _, _ = re.findall(r"\d+", range_info)
    print(f"Found {n_books} books available.")

    for _ in range(10):  # safety upper bound
        range_info = soup.find("div", {"class": "pull-left"}).text  # type: ignore
        _, fr, to = re.findall(r"\d+", range_info)
        print(f"Downloading books from {fr} to {to}")

        for well in soup.find_all("div", {"class": "well"}):
            if info := well.find("h2"):
                link = info.find("a")
                text_name = link.text
                text_id = link["href"].split("=")[-1]
                print(f"Downloading {text_name} ({author_name})")
                download_book_from_text_id(text_id, text_name, author_name, fmt_theater=fmt_theater)

        # Go to next range
        if to == n_books:  # reached the last book
            break
        url = f"https://www.greek-language.gr/digitalResources/ancient_greek/library/index.html?start={to}&author_id={author_id}"
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")


if __name__ == "__main__":
    # download_book_from_text_id(
    #     text_id="108", text_name="test", author_name="plato", fmt_theater=True
    # )
    download_books_from_author_id(author_id="199", fmt_theater=True)
