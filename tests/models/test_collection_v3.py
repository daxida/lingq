import json
from pathlib import Path

from models.collection_v3 import CollectionV3


def make_test_collection_v3(language_code: str) -> None:
    fixture_folder_path = Path("tests/models/models_fixtures/collections")
    fixture_path = fixture_folder_path / f"{language_code}.json"
    with fixture_path.open("r") as json_file:
        data = json.load(json_file)
        CollectionV3.model_validate(data)


def test_collection_v3_ja() -> None:
    make_test_collection_v3("ja")


def test_collection_v3_el() -> None:
    make_test_collection_v3("el")


def test_collection_v3_el2() -> None:
    make_test_collection_v3("el2")


def test_collection_v3_el3() -> None:
    make_test_collection_v3("el3")


def test_collection_v3_de() -> None:
    make_test_collection_v3("de")


def test_collection_v3_fr() -> None:
    make_test_collection_v3("fr")


def test_collection_v3_es() -> None:
    make_test_collection_v3("es")


def test_collection_v3_en() -> None:
    make_test_collection_v3("en")


def test_collection_v3_it() -> None:
    make_test_collection_v3("it")


def test_collection_v3_pt() -> None:
    make_test_collection_v3("pt")
