"""Get all Kathimerini (newspaper) articles from a given author.

Should work even with their annoying pay-me popup.
"""

from pathlib import Path

import requests
from bs4 import BeautifulSoup

url = "https://www.kathimerini.gr/author/marialena-spyropoyloy/"
ofolder = Path("marialena")
ofolder.mkdir(parents=True, exist_ok=True)


def get_all_article_urls_at_page(author_url: str, page: int) -> list[str]:
    assert 0 < page
    author_url = url if page == 1 else f"{url}/page/{page}/"
    response = requests.get(author_url)
    response.raise_for_status()
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")

    links = []
    for a_tag in soup.find_all("a", href=True):
        link = a_tag["href"]
        if link not in links:
            links.append(link)

    correct_prefixes = [
        "https://www.kathimerini.gr/culture",
        "https://www.kathimerini.gr/opinion",
    ]
    # Naive filter
    links = [link for link in links if any(link.startswith(pref) for pref in correct_prefixes)]
    links = links[4:]
    return links


def get_article(article_url: str) -> str:
    response = requests.get(article_url)
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    return "\n".join(paragraphs)


def write_article(opath: Path, article: str) -> None:
    with opath.open("w") as f:
        f.write(article)


for page in range(1, 3):
    links = get_all_article_urls_at_page(url, page)
    print(f"Getting all articles ({len(links)}) at page {page}")
    for link in links:
        title = link.split("/")[-2]
        article = get_article(link)
        opath = ofolder / f"{title}.txt"
        write_article(opath, article)
print(f"Wrote articles at {ofolder}")
