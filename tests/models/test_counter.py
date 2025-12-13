from lingq.models.counter import Counter


def test_model_counter_for_empty_collection() -> None:
    data_counter = {
        "cardsCount": 0,
        "hasFlags": False,
        "knownWordsCount": 0,
        "totalWordsCount": 0,
        "roseGiven": False,
        "rosesCount": 0,
        "lessonsCount": 0,
        "difficulty": 0,
        "isTaken": False,
        "newWordsCount": 0,
        "pk": 1497642,
        "progress": None,
        "isCompletelyTaken": True,
        "uniqueWordsCount": 0,
    }
    Counter.model_validate(data_counter)
