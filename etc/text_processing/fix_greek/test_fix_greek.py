from etc.text_processing.fix_greek.fix_greek import fix


def test_latin_capitals():
    expected = "Αα Άα Βα Εα Έα Ηα Ια Ία Κα Μα Να Οα Όα Ρα Τα Χα Υα".split()
    received = "Aα Áα Bα Eα Éα Hα Iα Íα Kα Mα Nα Oα Óα Pα Tα Xα Yα".split()
    assert len(expected) == len(received)
    for e, w in zip(expected, received):
        assert fix(w.strip()) == e.strip()
