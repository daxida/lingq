from etc.text_processing.fix_greek.fix_greek import fix_latin_letters


def _test_latin_letters_helper(received: str, expected: str):
    received_lines = received.split()
    expected_lines = expected.split()

    assert len(expected_lines) == len(received_lines)
    for exp, rec in zip(expected_lines, received_lines):
        assert exp.strip() == fix_latin_letters(rec.strip())


def test_latin_letters_uppercase():
    _test_latin_letters_helper(
        received="Aα Áα Bα Eα Éα Hα Iα Íα Kα Mα Nα Oα Óα Pα Tα Xα Yα",
        expected="Αα Άα Βα Εα Έα Ηα Ια Ία Κα Μα Να Οα Όα Ρα Τα Χα Υα",
    )


def test_latin_letters_lowercase():
    _test_latin_letters_helper(
        received="μέvω",
        expected="μένω",
    )


def test_latin_letters():
    _test_latin_letters_helper(
        received="7 Eναντίoν μoυ ψιθυρίζoυν μαζί όλoι εκείνoι πoυ με μισoύν· εναντίoν μoυ συλλογίζoνται με κακία, λέγoντας but not this!",
        expected="7 Εναντίον μου ψιθυρίζουν μαζί όλοι εκείνοι που με μισούν· εναντίον μου συλλογίζονται με κακία, λέγοντας but not this!",
    )


def test_latin_letters_error_at_word_end():
    _test_latin_letters_helper(
        received="Eναντίo μou",
        expected="Εναντίο μου",
    )


def test_latin_letters_only_latin():
    # Should not fix actual latin words
    text = "Ο Μικελάντζελο ντι Λοντοβίκο Μπουοναρότι Σιμόνι (Michelangelo di Lodovico Buonarroti Simoni, 6 Μαρτίου 1475 – 18 Φεβρουαρίου 1564)"
    _test_latin_letters_helper(text, text)
