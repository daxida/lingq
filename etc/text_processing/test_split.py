from split import separate

TEXT_SEPARATE = """
    Heading1
    Subheading1
    Sentence 1. Sentence 2.
    Sentence 3.
    Subheading2
    Sentence 4.
    Heading2
    Subheading3
    Sentence 5. Sentence 6.
    Heading3
    Sentence 7.
"""
LINES = [line.strip() for line in TEXT_SEPARATE.split("\n")]
HEADINGS_1 = [
    ("Title1", "Heading1"),
    ("Title2", "Heading2"),
    ("Heading3", "Heading3"),
]
HEADINGS_2 = [
    ("Subtitle1", "Subheading1"),
    ("Subheading2", "Subheading2"),
    ("Subheading3", "Subheading3"),
]


def test_separate_no_headings() -> None:
    ranked_headings = []
    received = separate(LINES, ranked_headings)
    expected = [
        "",
        "Heading1",
        "Subheading1",
        "Sentence 1. Sentence 2.",
        "Sentence 3.",
        "Subheading2",
        "Sentence 4.",
        "Heading2",
        "Subheading3",
        "Sentence 5. Sentence 6.",
        "Heading3",
        "Sentence 7.",
        "",
    ]
    assert received == expected


def test_separate_one_level() -> None:
    ranked_headings = [HEADINGS_1]
    received = separate(LINES, ranked_headings)
    expected = {
        "Title1": [
            "Subheading1",
            "Sentence 1. Sentence 2.",
            "Sentence 3.",
            "Subheading2",
            "Sentence 4.",
        ],
        "Title2": ["Subheading3", "Sentence 5. Sentence 6."],
        "Heading3": ["Sentence 7.", ""],
    }
    assert received == expected


def test_separate_two_levels() -> None:
    ranked_headings = [HEADINGS_1, HEADINGS_2]
    received = separate(LINES, ranked_headings)
    expected = {
        "Title1": {
            "Subtitle1": ["Sentence 1. Sentence 2.", "Sentence 3."],
            "Subheading2": ["Sentence 4."],
        },
        "Title2": ["Subheading3", "Sentence 5. Sentence 6."],
        "Heading3": ["Sentence 7.", ""],
    }

    assert received == expected
