"""
What to do once you managed to create a yomitan dictionary:

(1) Install yomitan if you haven't: https://github.com/yomidevs/yomitan
(2) Click the settings cog.
(3) Preferably create a new profile:
    - Click "Configure profiles", then add.
    - Choose a meaningful name like "lingq-your-language".
(4) Set the profile as "Default" and "Editing" if they are not already.
(5) Set the language in "General".
(6) Click "Configure installed and enabled dictionaries".
    - Click import
    - Drag the zipped dictionary (do not unzip it).
    - Select it to be used.
(7) That is all. If you want to further customize Yomitan check their guides.
"""

import io
import json
import os
import sys
import zipfile
from datetime import datetime
from typing import Any

from lingqhandler import LingqHandler
from models.cards import Card

# TODO: fix this type. Use pydantic if possible.
YomitanDict = Any


def get_dictionary_index(language_code: str) -> dict[str, Any]:
    """
    Make a yomitan dictionary index.

    Roughly based on the index from the Kaikki-to-yomitan downloads page:
    https://github.com/yomidevs/kaikki-to-yomitan/blob/master/downloads.md
    """
    return {
        "format": 3,
        "revision": datetime.now().strftime("%Y.%m.%d"),
        "sequenced": True,
        # Change this if necessary
        "author": "https://github.com/daxida",
        "url": "https://github.com/daxida/lingq",
        "description": "Dictionary generated from LingQ data.",
        # Change these two if necessary
        "sourceLanguage": language_code,
        "targetLanguage": "en",
        "title": f"lingq-{language_code}",
    }


def words_to_yomitan(words: list[Card]) -> YomitanDict:
    """
    Convert the Card model to yomitan.

    Discussion about the structure:
    https://github.com/themoeway/kaikki-to-yomitan/issues/55

    Examples used as references:
    https://github.com/themoeway/kaikki-to-yomitan/blob/433636cf74cb530a241f9c4c3842a2c11dd3b084/data/test/dict/fr/en/term_bank_1.json#L1
    https://github.com/themoeway/jmdict-yomitan?tab=readme-ov-file#jmdict-for-yomitan-1
    """

    yomitan_dict: YomitanDict = []
    for card in words:
        glossary_content = []
        for hint in card.hints:
            fmt_hint = {"content": hint.text, "tag": "li"}
            glossary_content.append(fmt_hint)
        glossary = {"content": glossary_content, "data": {"content": "glossary"}, "tag": "ul"}

        if card.notes:
            notes_content = [{"content": card.notes, "tag": "li"}]
            notes = {"content": notes_content, "data": {"content": "notes"}, "tag": "ul"}
        else:
            notes = None

        example_content = [{"content": card.fragment, "tag": "li"}]
        example = {
            "content": example_content,
            "style": {"fontStyle": "italic"},
            "data": {"content": "example"},
            "tag": "ul",
        }

        # Actually only notes can be None
        definitions_contents = [x for x in (glossary, example, notes) if x is not None]
        definitions = [{"type": "structured-content", "content": definitions_contents}]

        # The keys are only for documentation. It is immediately converted to a list.
        entry = {
            "term": card.term,
            "readings": "",  # card.transliteration.get("latin", ""),
            # Abbreviations expanded in tag_bank_1.json
            # (LINGQ) A grammar tag is a tag that appear both in tags and g_tags
            "definition_tags": " ".join(card.tags),  # space separated
            "rule_identifiers": "",
            "score": 0,
            # Can do this for a minimal version: [hint.text for hint in card.hints]
            "definitions_list": definitions,
            "sequence_number": 0,  # ignore
            "term_tags": "",
        }
        yomitan_dict.append(list(entry.values()))

    return yomitan_dict


def words_to_yomitan_simple(words: list[Card]) -> YomitanDict:
    """
    Convert the Card model to yomitan.

    Minimal yomitan dictionary.
    Contains only the terms, tags and hints with no format.
    """
    yomitan_dict: YomitanDict = []
    for card in words:
        entry = [
            card.term,
            "",
            " ".join(card.tags),
            "",
            0,
            [hint.text for hint in card.hints],
            0,
            "",
        ]
        yomitan_dict.append(entry)

    return yomitan_dict


def _into_yomitan_for_language(language_code: str, dump_path: str) -> None:
    """Read and convert the JSON obtained from LingQ."""
    # TODO: split the dict into manageable jsons
    # TODO: make a different entry per hint

    # Look for the dump
    lingq_json_path = os.path.join(dump_path, "lingqs.json")
    if not os.path.exists(lingq_json_path):
        print(f"Could not find the dump at {lingq_json_path}")
        print(f"Exiting.")
        sys.exit(1)

    # Load the dump
    with open(lingq_json_path, "r", encoding="utf-8") as f:
        words = json.load(f)
        words = [Card.model_validate(word) for word in words]

    # Convert to Yomitan
    yomitan_dict = words_to_yomitan_simple(words)

    return yomitan_dict


def write_yomitan_dict(language_code: str, out_path: str, yomitan_dict: YomitanDict) -> None:
    """Write the zipped yomitan dict."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        zipf.writestr(
            "index.json",
            json.dumps(get_dictionary_index(language_code), indent=2, ensure_ascii=False),
        )
        # TODO: I'm not sure what is the correct size to split
        zipf.writestr("term_bank_1.json", json.dumps(yomitan_dict, indent=2, ensure_ascii=False))

    with open(out_path, "wb") as f:
        f.write(zip_buffer.getvalue())


def _into_yomitan(language_codes: list[str], download_folder: str) -> None:
    for language_code in language_codes:
        dump_path = os.path.join(download_folder, language_code)
        yomitan_dict = _into_yomitan_for_language(language_code, dump_path)
        out_path = os.path.join(dump_path, f"lingqs-{language_code}.zip")
        write_yomitan_dict(language_code, out_path, yomitan_dict)
        print(f"Finished dictionary for {language_code}.")
        print(f"It can be found at: {out_path}")


def yomitan(language_codes: list[str], download_folder: str) -> None:
    """
    Make a Yomitan dictionary from a LingQ JSON dump generated through get_words.

    If no language codes are given, use all languages.
    """
    if not language_codes:
        language_codes = LingqHandler.get_all_user_languages_codes()
    _into_yomitan(language_codes, download_folder)


if __name__ == "__main__":
    # Defaults for manually running this script.
    yomitan(
        language_codes=["el"],
        download_folder="downloads/lingqs",
    )
