from pathlib import Path

import requests
from bs4 import BeautifulSoup


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    response.encoding = "utf-8"
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_short_stories_urls() -> None | list[str]:
    """Get all urls for diigimata."""
    url = "https://www.papadiamantis.net/aleksandros-papadiamantis/syggrafiko-ergo/diigimata"
    soup = get_soup(url)

    div = soup.find("div", class_="uk-column-1-3")
    story_urls = []
    for li in div.find_all("li"):
        a_tag = li.find("a")
        if a_tag and "href" in a_tag.attrs:
            story_url = a_tag["href"]
            story_urls.append(f"https://www.papadiamantis.net/{story_url}")

    return story_urls


def get_short_story(url: str) -> tuple[str, str]:
    """Get a short story (diigima)."""
    soup = get_soup(url)

    div = soup.find("div", class_="uk-width-3-4@m")
    title = div.find("h1").get_text(strip=True)
    text_div = soup.find("div", class_="uk-panel uk-margin")
    paragraphs = []
    for paragraph in text_div.find_all("p"):
        ptext = paragraph.text.replace("\n", " ")
        ptext = paragraph.text.replace("\u2009", "")
        paragraphs.append(ptext)

    text = f"{title}\n\n{"\n".join(paragraphs)}"
    return title, text


def write_all_short_stories() -> None:
    opath = Path("stories")
    opath.mkdir(exist_ok=True)

    for url in get_short_stories_urls():
        print(f"Getting: {url}")
        title, text = get_short_story(url)
        story_opath = opath / f"{title}.txt"
        with story_opath.open("w", encoding="utf-8") as f:
            f.write(text)


def write_long_story(url: str) -> None:
    """Write a long story (mythistorima)."""
    soup = get_soup(url)

    book_div = soup.find("div", class_="uk-width-3-4@m")
    book_title = book_div.find("h1").get_text(strip=True)

    _section_div = book_div.find_all("h2", class_=["uk-heading-bullet"])
    section_titles = [s.get_text() for s in _section_div]

    book: dict[str, dict[str, str]] = {}

    section_div = book_div.find_all("div", class_="accordion")
    for sidx, section in enumerate(section_div):
        stitle = section_titles[sidx]
        book[stitle] = {}
        chapters_div = section.find_all("div", class_="accordion-group")

        for chapter_div in chapters_div:
            chapter_heading = chapter_div.find("div", class_="accordion-heading")
            ctitle = chapter_heading.get_text(strip=True)

            text_div = chapter_div.find("div", class_="accordion-inner")
            paragraphs = []
            for paragraph in text_div.find_all("p"):
                ptext = paragraph.text.replace("\n", " ")
                ptext = paragraph.text.replace("\u2009", "")
                paragraphs.append(ptext)

            text = f"{ctitle}\n\n{"\n".join(paragraphs)}"
            book[stitle][ctitle] = text

    opath = Path(book_title)
    for sidx, (stitle, section) in enumerate(book.items(), 1):
        section_opath = opath / f"{sidx:02d}. {stitle}"
        section_opath.mkdir(parents=True, exist_ok=True)

        for cidx, (ctitle, chapter) in enumerate(section.items(), 1):
            chapter_opath = section_opath / f"{cidx:02d}. {ctitle}.txt"
            with chapter_opath.open("w", encoding="utf-8") as f:
                f.write(chapter)


LONG_STORIES_URLS = [
    "https://www.papadiamantis.net/aleksandros-papadiamantis/syggrafiko-ergo/mythistorimata/389-metanastis-1879",
    "https://www.papadiamantis.net/aleksandros-papadiamantis/syggrafiko-ergo/mythistorimata/390-o-mporoi-t-n-thn-n-1882",
    "https://www.papadiamantis.net/aleksandros-papadiamantis/syggrafiko-ergo/mythistorimata/387-gyftopoyla-meros-i-1884",
    "https://www.papadiamantis.net/aleksandros-papadiamantis/syggrafiko-ergo/mythistorimata/388-gyftopoyla-meros-ii-1884",
]


def main() -> None:
    # write_all_short_stories()

    for url in LONG_STORIES_URLS:
        write_long_story(url)


if __name__ == "__main__":
    main()
