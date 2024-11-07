import json
from pathlib import Path

from commands.yomitan import yomitan


def rewrite_json_with_first_n_entries(json_file_path: Path, n: int = 5) -> None:
    with json_file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        first_ten_entries = data[:n]
    with json_file_path.open("w", encoding="utf-8") as f:
        json.dump(first_ten_entries, f, ensure_ascii=False, indent=4)


def test_yomitan() -> None:
    """Simply test that the yomitan function does not crash."""
    fixture_path = Path("tests/fixtures/lingqs")
    assert (fixture_path / "pt").exists()

    zip_file_path = fixture_path / "pt" / "lingqs-pt.zip"
    assert not zip_file_path.exists()

    yomitan(["pt"], fixture_path)
    assert zip_file_path.exists()

    zip_file_path.unlink()
    assert not zip_file_path.exists()


if __name__ == "__main__":
    # Generate fixture
    json_file = Path("downloads/lingqs/pt/lingqs.json")
    rewrite_json_with_first_n_entries(json_file)
