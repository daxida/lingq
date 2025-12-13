import json
import zipfile
from pathlib import Path

from lingq.commands.mk_yomitan import YomitanDictTy, get_dictionary_title, yomitan


def rewrite_json_with_first_n_entries(json_file_path: Path, n: int = 5) -> None:
    with json_file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        first_ten_entries = data[:n]
    with json_file_path.open("w", encoding="utf-8") as f:
        json.dump(first_ten_entries, f, ensure_ascii=False, indent=4)


LANG = "el"
FIXTURE_DIR = Path("tests/fixtures/lingqs")
DICT_TITLE = get_dictionary_title("el", dict_ty="normal")


def path_zip(dict_ty: YomitanDictTy) -> Path:
    dict_title = get_dictionary_title("el", dict_ty)
    return FIXTURE_DIR / LANG / f"{dict_title}.zip"


def test_yomitan_structure() -> None:
    """Test that the yomitan function does not crash."""
    assert (FIXTURE_DIR / LANG).exists()

    dict_ty = "normal"
    pz = path_zip(dict_ty)
    assert not pz.exists()

    yomitan([LANG], FIXTURE_DIR, dict_ty=dict_ty)
    assert pz.exists()

    pz.unlink()
    assert not pz.exists()


def test_make_yomitan_card() -> None:
    """Check for expected files, then generate a dictionary to compare via git --diff.

    Any changes to the yomitan dictionary will show as changes to the committed files.
    """
    for dict_ty in ("normal", "simple"):
        pz = path_zip(dict_ty)
        yomitan([LANG], FIXTURE_DIR, dict_ty=dict_ty)

        with zipfile.ZipFile(pz, "r") as zf:
            names = zf.namelist()
            assert all(f in names for f in ("index.json", "term_bank_1.json", "styles.css"))
            with zf.open("term_bank_1.json") as f:
                content = f.read().decode("utf-8")
                data = json.loads(content)
                first_entry = data[0]
                # print(json.dumps(first_entry, indent=2))
                with pz.with_name(f"{dict_ty}.json").open("w") as of:
                    json.dump(first_entry, of, indent=2, ensure_ascii=False)

        pz.unlink()


if __name__ == "__main__":
    # Generate fixture
    # json_file = Path(f"downloads/lingqs/{LANG}/lingqs.json")
    # rewrite_json_with_first_n_entries(json_file)
    pass
