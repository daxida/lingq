import unittest
import re
from main import fix
from functools import partialmethod


ABSOLUTE = "/Users/rafa/Desktop/fix_text/tests/"

paths = [
    ("problematic_chars_test", "problematic_chars_expected"),

]


def init_tests():
    # FIX THE VARIABLE NAMES

    pairs = []
    for test, expected in paths:
        test = ABSOLUTE + test
        expected = ABSOLUTE + expected
        try:
            with open(f"{test}.txt", "r") as source:
                test = source.readlines()
            with open(f"{expected}.txt", "r") as expected:
                expected = expected.readlines()
            pairs.append(zip(test, expected))
        except FileNotFoundError as e:
            print(e)

    return pairs


tests_pairs = init_tests()


def remove_ponctuation(line):
    return re.sub(r"['᾿]", "", line)


def test_builder(self, idx):
    ''' Compares sentence by sentence for easier visualization '''
    for source, expected in tests_pairs[idx]:
        lines = zip(source.split("."), expected.split("."))
        for source_line, expected_line in lines:
            source_line = remove_ponctuation(source_line).strip()
            expected_line = remove_ponctuation(expected_line).strip()

            result = fix(source_line)
            self.assertEqual(result, expected_line)


class TestPoly(unittest.TestCase):

    maxDiff = None
    amount_tests = len(tests_pairs)

    # This makes so each pair counts as a separate test
    for n in range(amount_tests):
        locals()[f'test_{n}'] = partialmethod(test_builder, idx=n)


if __name__ == '__main__':
    unittest.main()
