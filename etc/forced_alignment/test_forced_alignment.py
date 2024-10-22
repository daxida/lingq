import pytest

try:
    import aeneas

    AENEAS_AVAILABLE = True
except ImportError:
    AENEAS_AVAILABLE = False


def test_simple():
    if not AENEAS_AVAILABLE:
        pytest.skip("Aeneas is not installed")

    from forced_alignment import TimedText, split_audio

    fragments = [
        {
            "begin": "0.000",
            "children": [],
            "end": "2.240",
            "id": "f000001",
            "language": "ell",
            "lines": ["(A2) 7. Το δελφίνι"],
        },
        {
            "begin": "2.240",
            "children": [],
            "end": "2.680",
            "id": "f000002",
            "language": "ell",
            "lines": ["Το δελφίνι"],
        },
        {
            "begin": "2.680",
            "children": [],
            "end": "18.320",
            "id": "f000003",
            "language": "ell",
            "lines": [
                "Θα μπορούσε κανείς να το πει «άλογο της θάλασσας». Και γρήγορο σαν άλογο είναι και στην ανάσα το άλογο θυμίζει. Φρρ! κάνει δυνατά κάθε φορά, που βγαίνει επάνω, και σαν άλογο προσφέρεται για… ιππασία."
            ],
        },
        {
            "begin": "18.320",
            "children": [],
            "end": "44.240",
            "id": "f000004",
            "language": "ell",
            "lines": [
                "(…) Οι ναυτικοί τα καμαρώνουν. Περνούν την ώρα μαζί τους. Τους αρέσει πολύ αυτό το θαλασσινό ζώο, γιατί δεν πειράζει τον άνθρωπο ποτέ. Κολυμπά σαν γοργόνα, τρελαίνεται για τη μουσική. Μα οι ψαράδες για το δελφίνι έχουν γνώμη διαφορετική, εντελώς αντίθετη. Γι' αυτούς είναι ένας φαγάς διάσημος, ένας επικίνδυνος εχθρός."
            ],
        },
        {
            "begin": "44.240",
            "children": [],
            "end": "44.240",
            "id": "f000005",
            "language": "ell",
            "lines": [""],
        },
        {
            "begin": "44.240",
            "children": [],
            "end": "74.520",
            "id": "f000006",
            "language": "ell",
            "lines": [
                "Μην τους μιλάτε για μουσική, για ποίηση, για… θαλασσινές ιπποδρομίες. Μετρείστε καλύτερα τα ψάρια, που τους κλέβει ο μεγάλος φαγάς! Ψάρια για ψάρια δεν αφήνει. Κι όταν δεν βρει ψάρια, τρώει τα χταπόδια και τα καβούρια. Διακόσια δόντια έχει. Κι όλα πρέπει να δουλέψουν. Πάλι καλά που γεννάει ένα μικρό κάθε ένα με δύο χρόνια. Αλλιώς τα ψάρια θα τα βλέπαμε μόνο στο ζωολογικό κήπο."
            ],
        },
    ]
    text_files = [
        [
            "(A2) 7. Το δελφίνι",
            "Το δελφίνι",
            "Θα μπορούσε κανείς να το πει «άλογο της θάλασσας». Και γρήγορο σαν άλογο είναι και στην ανάσα το άλογο θυμίζει. Φρρ! κάνει δυνατά κάθε φορά, που βγαίνει επάνω, και σαν άλογο προσφέρεται για… ιππασία.",
        ],
        [
            "(…) Οι ναυτικοί τα καμαρώνουν. Περνούν την ώρα μαζί τους. Τους αρέσει πολύ αυτό το θαλασσινό ζώο, γιατί δεν πειράζει τον άνθρωπο ποτέ. Κολυμπά σαν γοργόνα, τρελαίνεται για τη μουσική. Μα οι ψαράδες για το δελφίνι έχουν γνώμη διαφορετική, εντελώς αντίθετη. Γι' αυτούς είναι ένας φαγάς διάσημος, ένας επικίνδυνος εχθρός."
        ],
        [
            "Μην τους μιλάτε για μουσική, για ποίηση, για… θαλασσινές ιπποδρομίες. Μετρείστε καλύτερα τα ψάρια, που τους κλέβει ο μεγάλος φαγάς! Ψάρια για ψάρια δεν αφήνει. Κι όταν δεν βρει ψάρια, τρώει τα χταπόδια και τα καβούρια. Διακόσια δόντια έχει. Κι όλα πρέπει να δουλέψουν. Πάλι καλά που γεννάει ένα μικρό κάθε ένα με δύο χρόνια. Αλλιώς τα ψάρια θα τα βλέπαμε μόνο στο ζωολογικό κήπο."
        ],
    ]

    expected = [
        TimedText(
            begin="0.000",
            end="18.320",
            text="(A2) 7. Το δελφίνι\nΤο δελφίνι\nΘα μπορούσε κανείς να το πει «άλογο της θάλασσας». Και γρήγορο σαν άλογο είναι και στην ανάσα το άλογο θυμίζει. Φρρ! κάνει δυνατά κάθε φορά, που βγαίνει επάνω, και σαν άλογο προσφέρεται για… ιππασία.",
        ),
        TimedText(
            begin="18.320",
            end="44.240",
            text="(…) Οι ναυτικοί τα καμαρώνουν. Περνούν την ώρα μαζί τους. Τους αρέσει πολύ αυτό το θαλασσινό ζώο, γιατί δεν πειράζει τον άνθρωπο ποτέ. Κολυμπά σαν γοργόνα, τρελαίνεται για τη μουσική. Μα οι ψαράδες για το δελφίνι έχουν γνώμη διαφορετική, εντελώς αντίθετη. Γι' αυτούς είναι ένας φαγάς διάσημος, ένας επικίνδυνος εχθρός.",
        ),
        TimedText(
            begin="44.240",
            end="74.520",
            text="\nΜην τους μιλάτε για μουσική, για ποίηση, για… θαλασσινές ιπποδρομίες. Μετρείστε καλύτερα τα ψάρια, που τους κλέβει ο μεγάλος φαγάς! Ψάρια για ψάρια δεν αφήνει. Κι όταν δεν βρει ψάρια, τρώει τα χταπόδια και τα καβούρια. Διακόσια δόντια έχει. Κι όλα πρέπει να δουλέψουν. Πάλι καλά που γεννάει ένα μικρό κάθε ένα με δύο χρόνια. Αλλιώς τα ψάρια θα τα βλέπαμε μόνο στο ζωολογικό κήπο.",
        ),
    ]

    timed_texts = split_audio(fragments, text_files, 0)
    assert timed_texts == expected

    timed_texts = split_audio(fragments, text_files, 10)
    assert timed_texts == expected
