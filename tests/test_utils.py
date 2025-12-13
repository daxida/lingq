from lingq.commands.sort import sort_by_versioned_numbers_impl
from lingq.utils import get_sorting_fn, greek_sorting_fn, roman_sorting_fn, sort_by_greek_words_impl


def test_greek_sorting_fn() -> None:
    entries = [
        "Ι'. Η μάχη",  # 10
        "Α'. Η αρχή",  # 1
        "Δ'. Η εκδίκηση",  # 4
        "ΙΣΤ'. Η πτώση",  # 16
        "Ζ'. Το ταξίδι",  # 7
    ]
    expected = [
        "Α'. Η αρχή",  # 1
        "Δ'. Η εκδίκηση",  # 4
        "Ζ'. Το ταξίδι",  # 7
        "Ι'. Η μάχη",  # 10
        "ΙΣΤ'. Η πτώση",  # 16
    ]

    assert greek_sorting_fn == get_sorting_fn("greek")
    sorted_entries = sorted(entries, key=greek_sorting_fn)
    assert sorted_entries == expected


def test_roman_sorting_fn() -> None:
    entries = [
        "Chapitre IX.mp3",  # 9
        "Chapitre I.mp3",  # 1
        "Chapitre V.mp3",  # 5
        "Chapitre X.mp3",  # 10
        "Chapitre III.mp3",  # 3
    ]
    expected = [
        "Chapitre I.mp3",  # 1
        "Chapitre III.mp3",  # 3
        "Chapitre V.mp3",  # 5
        "Chapitre IX.mp3",  # 9
        "Chapitre X.mp3",  # 10
    ]

    assert roman_sorting_fn == get_sorting_fn("roman")
    sorted_entries = sorted(entries, key=roman_sorting_fn)
    assert sorted_entries == expected


def test_os_sorting_fn() -> None:
    entries = [
        "1. One",
        "2. Two",
        "10. Ten",
        "100. Hundred",
        "01. ZeroOne",
    ]
    expected = [
        "100. Hundred",
        "01. ZeroOne",
        "10. Ten",
        "1. One",
        "2. Two",
    ]

    sorting_fn = get_sorting_fn("os")
    sorted_entries = sorted(entries, key=sorting_fn)
    assert sorted_entries == expected


def test_human_sorting_fn() -> None:
    entries = [
        "1. One",
        "2. Two",
        "10. Ten",
        "100. Hundred",
        "01. ZeroOne",
    ]
    expected = [
        "1. One",
        "01. ZeroOne",
        "2. Two",
        "10. Ten",
        "100. Hundred",
    ]

    sorting_fn = get_sorting_fn("human")
    sorted_entries = sorted(entries, key=sorting_fn)
    assert sorted_entries == expected


def test_sort_by_greek_words_impl() -> None:
    entries = ["Βελάκι", "άλφα", "αλφάδι", "Άρτεμις", "Άλφα", "αλεπού"]
    expected = ["αλεπού", "άλφα", "Άλφα", "αλφάδι", "Άρτεμις", "Βελάκι"]
    sorted_entries = sorted(entries, key=sort_by_greek_words_impl)
    assert sorted_entries == expected


def test_version_sorting() -> None:
    entries = [
        "1.1.宿命 死なない 蛸 -萩原 朔 太郎",
        "1.がちょ う の たんじょうび -新美南吉",
    ]
    expected = [
        "1.がちょ う の たんじょうび -新美南吉",
        "1.1.宿命 死なない 蛸 -萩原 朔 太郎",
    ]
    sorted_entries = sorted(entries, key=sort_by_versioned_numbers_impl)
    assert sorted_entries == expected
