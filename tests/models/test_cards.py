from models.cards import Card, Cards, Readings, Transliteration


def test_model_cards() -> None:
    # From LingQ. Note the camelcase in gTags.
    data_cards = {  # type: ignore
        "count": 2203,
        "next": "https://www.lingq.com/api/v3/de/cards/?page=2&page_size=200",
        "previous": None,
        "results": [
            {
                "pk": 164939101,
                "url": "https://www.lingq.com/api/v3/de/cards/164939101/",
                "term": "bald",
                "fragment": "…aber man versöhnt sich bald- sonst verdirbt es den…",
                "importance": 3,
                "status": 0,
                "extended_status": None,
                "last_reviewed_correct": None,
                "srs_due_date": "2020-03-26T16:57:01.295881",
                "notes": "",
                "audio": None,
                "words": ["bald"],
                "tags": [],
                "hints": [
                    {
                        "id": 35877,
                        "locale": "en",
                        "text": "soon",
                        "term": "Bald",
                        "popularity": 43,
                        "is_google_translate": True,
                        "flagged": True,
                    }
                ],
                "transliteration": {},
                "gTags": ["Adjektiv", "Adverb"],
                "wordTags": ["Adjektiv", "Adverb"],
                "readings": {},
                "writings": ["bald"],
            },
            {
                "pk": 152113487,
                "url": "https://www.lingq.com/api/v3/de/cards/152113487/",
                "term": "bereichern",
                "fragment": "...müssen Ihre neue Sprache bereichern.",
                "importance": 0,
                "status": 0,
                "extended_status": None,
                "last_reviewed_correct": None,
                "srs_due_date": "2020-01-02T04:28:20.400167",
                "notes": "",
                "audio": None,
                "words": ["bereichern"],
                "tags": ["verb", "präsens", "wir"],
                "hints": [
                    {
                        "id": 40534,
                        "locale": "en",
                        "text": "enrich, improve, make better",
                        "term": "bereichern",
                        "popularity": 1303,
                        "is_google_translate": False,
                        "flagged": False,
                    }
                ],
                "transliteration": {},
                "gTags": ["verb", "präsens", "wir"],
                "wordTags": ["verb", "präsens", "wir"],
                "readings": {},
                "writings": ["bereichern"],
            },
        ],
    }

    Cards.model_validate(data_cards)


def test_model_card() -> None:
    # When it is read it becomes snake_case
    data_card = {
        "pk": 459243703,
        "term": "εκφώνησής",
        "fragment": "διαδικασία προγραμματισμού της εκφώνησής σας, να",
        "importance": 0,
        "status": 0,
        "notes": "",
        "audio": None,
        "words": ["εκφώνησής"],
        "tags": [],
        "hints": [
            {
                "id": 129173102,
                "locale": "en",
                "text": "of reading (aloud)",
                "term": "εκφώνησής",
                "popularity": 2,
                "is_google_translate": True,
                "flagged": False,
            }
        ],
        "transliteration": {"latin": ["ekfonisis"]},
        "g_tags": [],
        "word_tags": [],
        "readings": {},
        "writings": ["εκφώνησής", "εκφωνησης"],
    }

    Card.model_validate(data_card)


def test_model_readings() -> None:
    readings_data = {
        "hiragana": ["ゆうしょう しゃ", "ゆう しょうしゃ"],
        "romaji": ["yuushousha", "yuushousha"],
    }

    Readings.model_validate(readings_data)


def test_model_empty_readings() -> None:
    Readings.model_validate({})


def test_model_transliteration_ja() -> None:
    transliteration_data = {
        "hiragana": ["りっきょう"],
        "furigana": [{"陸橋": "りっきょう"}],
        "romaji": ["rikkyou"],
    }
    Transliteration.model_validate(transliteration_data)


def test_model_transliteration_el() -> None:
    transliteration_data = {"latin": ["ekfonisis"]}
    Transliteration.model_validate(transliteration_data)


def test_mode_empty_transliteration() -> None:
    Transliteration.model_validate({})
