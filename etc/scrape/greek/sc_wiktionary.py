from pathlib import Path

import requests
from bs4 import BeautifulSoup

DOWNLOAD_FOLDER = Path("book/texts")
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

base_url = "https://el.wikisource.org/wiki/Τον_καιρό_του_Βουλγαροκτόνου/Κεφάλαιο_"
numerals = "Α Β Γ Δ Ε ΣΤ Ζ Η Θ Ι ΙΑ ΙΒ ΙΓ ΙΔ ΙΕ ΙΣΤ ΙΖ ΙΗ ΙΘ Κ ΚΑ ΚΒ ΚΓ ΚΔ ΚΕ ΚΣΤ ΚΖ ΚΗ ΚΘ".split()


def get_chapter(chapter_number: str) -> tuple[str, str] | None:
    url = f"{base_url}{chapter_number}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve chapter {chapter_number}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    div = soup.find("div", class_="mw-parser-output")
    if not div:
        print(f"Content not found for chapter {chapter_number}")
        return None

    _header = div.find("span", id="ws-chapter")
    header = _header.get_text() if _header else "No header found"

    paragraphs = []
    for paragraph in div.find_all("p"):
        # This is an error on wiktionary's side. There should be
        # no newlines inside a paragraph, except at final position.
        ptext = paragraph.text.replace("\n", " ")
        paragraphs.append(ptext)
    chapter_text = "\n".join(paragraphs)

    return header, chapter_text


def main() -> None:
    for idx, chapter_number in enumerate(numerals, start=1):
        res = get_chapter(chapter_number)

        if res:
            header, chapter_text = res
            chapter_file = DOWNLOAD_FOLDER / f"{idx:02d}. {header}.txt"
            with chapter_file.open("w", encoding="utf-8") as f:
                # This adds the title on top of the text
                # f.write(f"{header}\n{chapter_text}")
                f.write(chapter_text)
            print(f"{idx:02d}: '{header}' saved to ==> {chapter_file}")
        else:
            print(f"Skipping chapter {chapter_number}")


if __name__ == "__main__":
    main()
