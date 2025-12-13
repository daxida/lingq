"""Instructions.

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
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TypedDict, get_args

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.cards import Card

YomitanIndex = dict[str, int | str | bool]
YomitanDictTy = Literal["simple", "normal"]
"""The type of the Yomitan dictionary."""

YOMITAN_DICT_CHOICES: list[YomitanDictTy] = list(get_args(YomitanDictTy))

Definition = Any


class YomitanEntryModel(TypedDict):
    term: str
    readings: str
    definition_tags: str
    rule_identifiers: str
    score: int
    definitions_list: list[Definition]
    sequence_number: int
    term_tags: str


YomitanEntry = list[str | int | list[Definition]]
YomitanDict = list[YomitanEntry]


def get_dictionary_title(lang: str, dict_ty: YomitanDictTy) -> str:
    match dict_ty:
        case "normal":
            return f"lingq-{lang}"
        case "simple":
            return f"lingq-{lang}-simple"


def get_dictionary_index(lang: str, dict_ty: YomitanDictTy) -> YomitanIndex:
    """Make a yomitan dictionary index.

    Roughly based on: https://github.com/yomidevs/kaikki-to-yomitan/blob/master/downloads.md
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
        "sourceLanguage": lang,
        "targetLanguage": "en",
        "title": get_dictionary_title(lang, dict_ty),
    }


def get_styles_css() -> str:
    """Add a minimal palette for word status and aligns the backlink.

    * https://github.com/daxida/kty/blob/master/assets/styles.css
    * src/models/cards.py

    1 - #fbe493 (LingQ colour)
    2 - #fff2c5 (LingQ colour)
    3 - #fff7db (LingQ colour)
    4 - #a8e6a3 (clear green)
    5 - #28a745 (strong green)
    """
    return """

.tag[data-details='1'] .tag-label {
  color: black;
  background-color: #fbe493;
}

.tag[data-details='2'] .tag-label {
  color: black;
  background-color: #fff2c5;
}

.tag[data-details='3'] .tag-label {
  color: black;
  background-color: #fff7db;
}

.tag[data-details='4'] .tag-label {
  color: black;
  background-color: #a8e6a3;
}

.tag[data-details='5'] .tag-label {
  color: black;
  background-color: #28a745;
}

/* https://github.com/daxida/kty/blob/master/assets/styles.css */

div[data-sc-content="extra-info"] {
    margin-left: 0.5em;
}

div[data-sc-content="backlink"] {
    font-size: 0.7em;
    text-align: right;
}

/* experiment */

details[data-sc-content^="details-entry"] {
  border: 1px solid var(--border-color, #ccc);
  border-radius: 0.5em;
  padding: 0.8em;
  margin: 0.6em 0;
}

/* remove native triangle and summary indicator */
summary[data-sc-content="summary-entry"] {
  list-style: none;
  cursor: pointer;
  padding: 0.2em 0.4em;
  font-weight: bold;
  color: var(--text-color);
}

/* hide default marker */
summary[data-sc-content="summary-entry"]::-webkit-details-marker,
summary[data-sc-content="summary-entry"]::marker {
  display: none;
}

/* spacing between header and content */
summary + * {
  margin-top: 0.6em;
}

""".strip()


def card_to_yomitan_entry(card: Card) -> YomitanEntry:
    """Convert the Card model to a dictionary entry.

    Cf. https://github.com/daxida/kty

    Discussion about the structure:
    https://github.com/themoeway/kaikki-to-yomitan/issues/55

    Examples used as references:
    https://github.com/themoeway/jmdict-yomitan?tab=readme-ov-file#jmdict-for-yomitan-1

    More examples can be found in the fixtures folder.
    """

    glosses_content = []
    for hint in card.hints:
        hint_fmt = {
            "tag": "li",
            "content": [
                {
                    "tag": "div",
                    "content": [hint.text],
                },
            ],
        }
        glosses_content.append(hint_fmt)
    glossary = {
        "tag": "ol",
        "data": {"content": "glosses"},
        "content": glosses_content,
    }

    # INVARIANT: we expect one and only one example (read, fragment)
    example_content = [
        {
            "tag": "li",
            "content": card.fragment,
        }
    ]

    example = {
        "tag": "div",
        "data": {"content": "extra-info"},
        "content": {
            "tag": "div",
            "data": {"content": "example-sentence"},
            "content": example_content,
            "style": {"fontStyle": "italic"},
        },
    }

    notes = []
    if card.notes:
        # To open/close notes (which can be quite large)
        summary = {
            "tag": "summary",
            "data": {"content": "summary-entry"},
            "content": "Notes",
        }
        notes_inner = {
            "tag": "div",
            "content": [
                {
                    "tag": "li",
                    "data": {"content": "extra-info"},  # Remove this?
                    "content": card.notes,
                }
            ],
        }
        notes = [
            {
                "tag": "details",
                "data": {"content": "details-entry-examples"},
                "content": [summary, notes_inner],
            }
        ]

    # We add the status at the very beginning.
    # Tags have to be space-separated.
    tags_items = [str(card.displayed_status()), *card.tags]
    tags = " ".join(tags_items)

    # Backlink to the API to visualize the JSON.
    # I don't think it is possible to send to the edit interface.
    url = f"https://www.lingq.com/api/v3/el/cards/{card.pk}/"
    backlink = {
        "tag": "div",
        "data": {"content": "backlink"},
        "content": [
            {
                "tag": "a",
                "href": url,
                "content": "API",
            }
        ],
    }

    # But we could put links to edit the card status!

    # Actually only notes can be None
    definitions_contents = [glossary, example, *notes, backlink]
    definitions_contents = [glossary, *notes, backlink]
    definitions: list[Definition] = [
        {"type": "structured-content", "content": definitions_contents}
    ]

    # The keys are only for validation and documentation.
    # It is immediately converted to a list.
    model_entry: YomitanEntryModel = {
        "term": card.term,
        "readings": "",  # card.transliteration.get("latin", ""),
        # Abbreviations expanded in tag_bank_1.json
        # (LINGQ) A grammar tag is a tag that appear both in tags and g_tags
        "definition_tags": tags,
        "rule_identifiers": "",
        "score": 0,
        # Can do this for a minimal version: [hint.text for hint in card.hints]
        "definitions_list": definitions,
        "sequence_number": 0,  # ignore
        "term_tags": "",
    }
    entry: YomitanEntry = list(model_entry.values())  # type: ignore
    return entry


def card_to_yomitan_entry_simple(card: Card) -> YomitanEntry:
    """Minimal yomitan entry.

    Contains only the terms, tags (coloured) and hints with no format.
    """
    tags_items = [str(card.status), *card.tags]
    tags = " ".join(tags_items)

    entry: YomitanEntry = [
        card.term,
        "",
        tags,
        "",
        0,
        [hint.text for hint in card.hints],
        0,
        "",
    ]
    return entry


def yomitan_for_language(dump_path: Path, lang: str, dict_ty: YomitanDictTy) -> YomitanDict:
    """Read and convert the JSON obtained from LingQ.

    There is no need to split the dictionary into smaller jsons. It should be small enough.
    """
    lingq_json_path = dump_path / "lingqs.json"
    if not lingq_json_path.exists():
        logger.error(f"Dump not found at {lingq_json_path}.")
        logger.error(f"First run the following command: lingq get words {lang}")
        sys.exit(1)

    with lingq_json_path.open("r", encoding="utf-8") as f:
        words = json.load(f)
        words = [Card.model_validate(word) for word in words]

    match dict_ty:
        case "normal":
            fn = card_to_yomitan_entry
        case "simple":
            fn = card_to_yomitan_entry_simple

    yomitan_dict = [fn(card) for card in words]

    return yomitan_dict


def write_yomitan_dict(
    lang: str, out_path: Path, yomitan_dict: YomitanDict, dict_ty: YomitanDictTy
) -> None:
    """Write the zipped yomitan dict."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        index = get_dictionary_index(lang, dict_ty)
        zipf.writestr("index.json", json.dumps(index, indent=2, ensure_ascii=False))
        styles = get_styles_css()
        zipf.writestr("styles.css", styles)
        # No need to split the banks, the files are small
        zipf.writestr("term_bank_1.json", json.dumps(yomitan_dict, indent=2, ensure_ascii=False))

    with out_path.open("wb") as f:
        f.write(zip_buffer.getvalue())


def yomitan(
    langs: list[str],
    opath: Path,
    *,
    dict_ty: YomitanDictTy = "normal",
) -> None:
    """Make a Yomitan dictionary from the result of 'lingq get words'.

    If no language codes are given, use all languages.
    """
    if not langs:
        langs = LingqHandler.get_user_langs()

    logger.debug(f"Chosen dictionary type: {dict_ty}")

    for lang in langs:
        dump_path = opath / lang
        logger.info(f"Converting to yomitan format for {lang}...")
        yomitan_dict = yomitan_for_language(dump_path, lang, dict_ty)
        yomitan_dict_title = get_dictionary_title(lang, dict_ty)
        out_path = dump_path / f"{yomitan_dict_title}.zip"
        logger.info("Writing dictionary...")
        write_yomitan_dict(lang, out_path, yomitan_dict, dict_ty)
        logger.success(f"Finished dictionary for {lang} at: {out_path}")
