from fix_utils.el.fix_greek import fix_latin_letters


def make_test_latin_letters(received: str, expected: str):
    received_lines = received.split()
    expected_lines = expected.split()

    assert len(expected_lines) == len(received_lines)
    for exp, rec in zip(expected_lines, received_lines):
        assert exp.strip() == fix_latin_letters(rec.strip())


def test_latin_letters_uppercase():
    make_test_latin_letters(
        received="Aα Áα Bα Eα Éα Hα Iα Íα Kα Mα Nα Oα Óα Pα Tα Xα Yα",
        expected="Αα Άα Βα Εα Έα Ηα Ια Ία Κα Μα Να Οα Όα Ρα Τα Χα Υα",
    )


def test_latin_letters_lowercase():
    make_test_latin_letters(
        received="μέvω",
        expected="μένω",
    )


def test_latin_letters():
    make_test_latin_letters(
        received="7 Eναντίoν μoυ ψιθυρίζoυν μαζί όλoι εκείνoι πoυ με μισoύν· εναντίoν μoυ συλλογίζoνται με κακία, λέγoντας but not this!",
        expected="7 Εναντίον μου ψιθυρίζουν μαζί όλοι εκείνοι που με μισούν· εναντίον μου συλλογίζονται με κακία, λέγοντας but not this!",
    )


def test_latin_letters_error_at_word_end():
    make_test_latin_letters(
        received="Eναντίo μou",
        expected="Εναντίο μου",
    )


def test_latin_letters_only_latin():
    # Should not fix actual latin words
    text = "Ο Μικελάντζελο ντι Λοντοβίκο Μπουοναρότι Σιμόνι (Michelangelo di Lodovico Buonarroti Simoni, 6 Μαρτίου 1475 – 18 Φεβρουαρίου 1564)"
    make_test_latin_letters(text, text)
