from utils import greek_sorting_fn, roman_sorting_fn


def test_greek_sorting_fn():
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

    sorted_entries = sorted(entries, key=greek_sorting_fn)
    assert sorted_entries == expected


def test_roman_sorting_fn():
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

    sorted_entries = sorted(entries, key=roman_sorting_fn)
    assert sorted_entries == expected
