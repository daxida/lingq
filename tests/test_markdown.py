from make_markdown import format_markdown
from models.collection import Collection

COLLECTION_LIST = [
    Collection(
        _id=693846,
        title="Quick Imports",
        language_code="fr",
        course_url="https://www.lingq.com/en/learn/fr/web/library/course/693846",
        level="-",
        has_audio=True,
        is_shared=False,
        first_update="2023-05-05",
        last_update="2023-05-05",
        amount_lessons=1,
        views_count=0,
    ),
    Collection(
        _id=518792,
        title="La Dame aux Camélias - Dumas Fils",
        language_code="fr",
        course_url="https://www.lingq.com/en/learn/fr/web/library/course/518792",
        level="C1",
        has_audio=True,
        is_shared=True,
        first_update="2022-01-01",
        last_update="2022-09-03",
        amount_lessons=47,
        views_count=1573,
    ),
    Collection(
        _id=1133996,
        title="Le laboureur et les mangeurs de vent - Boris Cyrulnik",
        language_code="fr",
        course_url="https://www.lingq.com/en/learn/fr/web/library/course/1133996",
        level="C2",
        has_audio=True,
        is_shared=False,
        first_update="2022-08-30",
        last_update="2022-08-30",
        amount_lessons=38,
        views_count=192,
    ),
]


def test_markdown_with_views():
    expected_lines = [
        "|Status| |Title|Views|Lessons|Created&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|Updated&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|",
        "|-|-|-|-|-|-|-|",
        "|private|-|[Quick Imports](https://www.lingq.com/en/learn/fr/web/library/course/693846)|-|1|2023-05-05|2023-05-05",
        "|shared|C1|[La Dame aux Camélias - Dumas Fils](https://www.lingq.com/en/learn/fr/web/library/course/518792)|1573|47|2022-01-01|2022-09-03",
        "|private|C2|[Le laboureur et les mangeurs de vent - Boris Cyrulnik](https://www.lingq.com/en/learn/fr/web/library/course/1133996)|192|38|2022-08-30|2022-08-30",
        "",
    ]
    expected = "\n".join(expected_lines)
    markdown = format_markdown(COLLECTION_LIST, include_views=True)
    assert markdown == expected


def test_markdown_without_views():
    expected_lines = [
        "|Status| |Title|Lessons|Created&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|Updated&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|",
        "|-|-|-|-|-|-|",
        "|private|-|[Quick Imports](https://www.lingq.com/en/learn/fr/web/library/course/693846)|1|2023-05-05|2023-05-05",
        "|shared|C1|[La Dame aux Camélias - Dumas Fils](https://www.lingq.com/en/learn/fr/web/library/course/518792)|47|2022-01-01|2022-09-03",
        "|private|C2|[Le laboureur et les mangeurs de vent - Boris Cyrulnik](https://www.lingq.com/en/learn/fr/web/library/course/1133996)|38|2022-08-30|2022-08-30",
        "",
    ]
    expected = "\n".join(expected_lines)
    markdown = format_markdown(COLLECTION_LIST, include_views=False)
    assert markdown == expected
