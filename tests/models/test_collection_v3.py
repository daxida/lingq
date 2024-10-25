import json
from pathlib import Path

from models.collection_v3 import CollectionV3


def make_test_collection_v3(language_code: str):
    fixture_folder_path = Path("tests/models/models_fixtures/collections")
    fixture_path = fixture_folder_path / f"{language_code}.json"
    with fixture_path.open("r") as json_file:
        data = json.load(json_file)
        CollectionV3.model_validate(data)


def test_collection_v3_ja():
    make_test_collection_v3("ja")


def test_collection_v3_el():
    make_test_collection_v3("el")


def test_collection_v3_de():
    make_test_collection_v3("de")


def test_collection_v3_fr():
    make_test_collection_v3("fr")


def test_collection_v3_es():
    make_test_collection_v3("es")


def test_collection_v3_en():
    make_test_collection_v3("en")


def test_collection_v3_it():
    make_test_collection_v3("it")


def test_collection_v3_pt():
    make_test_collection_v3("pt")
