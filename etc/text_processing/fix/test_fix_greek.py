from el.fix_greek import fix_latin_letters, fix_textstring, standarize_punctuation


def make_test_latin_letters(received: str, expected: str) -> None:
    received_lines = received.split()
    expected_lines = expected.split()

    assert len(expected_lines) == len(received_lines)
    for exp, rec in zip(expected_lines, received_lines):
        assert exp.strip() == fix_latin_letters(rec.strip())


def test_latin_letters_uppercase() -> None:
    make_test_latin_letters(
        received="Aα Áα Bα Eα Éα Hα Iα Íα Kα Mα Nα Oα Óα Pα Tα Xα Yα",
        expected="Αα Άα Βα Εα Έα Ηα Ια Ία Κα Μα Να Οα Όα Ρα Τα Χα Υα",
    )


def test_latin_letters_lowercase() -> None:
    make_test_latin_letters(
        received="μέvω",
        expected="μένω",
    )


def test_latin_letters_one() -> None:
    make_test_latin_letters(
        received="7 Eναντίoν μoυ ψιθυρίζoυν μαζί όλoι εκείνoι πoυ με μισoύν",
        expected="7 Εναντίον μου ψιθυρίζουν μαζί όλοι εκείνοι που με μισούν",
    )


def test_latin_letters_two() -> None:
    make_test_latin_letters(
        received="εναντίoν μoυ συλλογίζoνται με κακία, λέγoντας but not this!",
        expected="εναντίον μου συλλογίζονται με κακία, λέγοντας but not this!",
    )


def test_latin_letters_error_at_word_end() -> None:
    make_test_latin_letters(
        received="Eναντίo μou",
        expected="Εναντίο μου",
    )


def test_latin_letters_only_latin() -> None:
    # Should not fix actual latin words
    text = (
        "Ο Μικελάντζελο ντι Λοντοβίκο Μπουοναρότι Σιμόνι "
        "(Michelangelo di Lodovico Buonarroti Simoni, 6 Μαρτίου 1475 – 18 Φεβρουαρίου 1564)"
    )
    make_test_latin_letters(text, text)


"""
Punctuation reference:
http://ebooks.edu.gr/ebooks/v/html/8547/2334/Grammatiki-Neas-Ellinikis-Glossas_A-B-G-Gymnasiou_html-apli/index_B_03.html
"""


def test_correctly_fixes_ellipsis() -> None:
    text = "«Ν.Ο.Α....;»"
    expected = "«Ν.Ο.Α.…;»"
    assert standarize_punctuation(text) == expected


def test_should_not_enforce_capital_after_exclamation_mark() -> None:
    text = "Τρέχα! Πρόφθασε! Φθάσε! απάντησε λαχανιασμένος ..."
    assert fix_textstring(text) == text


def test_should_not_enforce_capital_after_question_mark() -> None:
    text = "Ο γιός μου! Πού είναι ο Ασώτης; φώναξε ..."
    assert fix_textstring(text) == text


def test_should_delete_boundary_hyphens() -> None:
    text = "χα-\nρά χα- \nρά χα-\n ρά χα - \nρά"
    expected = "χαρά χαρά χαρά χαρά"
    assert fix_textstring(text) == expected


def test_should_not_delete_correct_hyphens() -> None:
    text = "χτύπησε ένα-δυο άλλους"
    assert fix_textstring(text) == text


def test_should_not_change_oti() -> None:
    text = "ό,τι Ό,τι"
    assert fix_textstring(text) == text


def test_should_not_add_space_in_punctuation_pair_one() -> None:
    text = "Πατέρα, εσύ!… επανέλαβε πιο σιγά. Και ο σύντροφος σου ποιος είναι;… Ρωμανέ"
    assert fix_textstring(text) == text


def test_should_not_add_space_in_punctuation_pair_two() -> None:
    text = "«Φύγε να πας εκεί που ξέρεις. Το θέλω.» "
    assert fix_textstring(text) == text
