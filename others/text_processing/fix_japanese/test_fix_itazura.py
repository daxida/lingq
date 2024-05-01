from others.text_processing.fix_japanese.fix_itazura import *


def test_fix_vertical_characters():
    wrong_text = "︱︶︵﹁﹂﹃﹄"
    expected = "ー)(「」『』"
    received = fix_vertical_characters(wrong_text)
    assert received == expected


def test_fix_paragraph_jumps():
    text = "ちいさなせかい\n\nディズニーランドの"
    expected = "ちいさなせかい\n--\nディズニーランドの"
    received = fix_paragraph_jumps(text)
    assert received == expected
