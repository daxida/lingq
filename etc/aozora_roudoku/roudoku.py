"""Sync 5mins' readings course with Aozora Roudoku/Bunko.

Course:
* 4-5mins
https://www.lingq.com/es/learn/ja/web/library/course/793510
* 6-7mins
https://www.lingq.com/es/learn/ja/web/library/course/800766

Roudoku:
https://aozoraroudoku.jp/kensaku/kensaku-05.html
"""

import sys
from pathlib import Path
from typing import TypedDict
from unicodedata import normalize

import Levenshtein

# The 45.txt and 67.txt files are copy pastes of their respective sections:
# https://aozoraroudoku.jp/kensaku/kensaku-05.html
PATH_NAME_TO_COURSE_ID = {
    "45": 793510,
    "67": 800766,
}


class Entry(TypedDict):
    title: str
    author: str
    raw: str
    idx: int  # starts at 1


def cmp_normalized(s1: str, s2: str) -> bool:
    norm_s1 = normalize("NFC", s1)
    norm_s2 = normalize("NFC", s2)
    return Levenshtein.distance(norm_s1, norm_s2) < 3


def remove_whitespace(s: str) -> str:
    """Remove whitespace.

    This allows comparison, even with different word segmentations.
    """
    return s.strip().replace(" ", "").replace("　", "")


def get_entry(title: str, author: str, raw: str, idx: int) -> Entry:
    return {
        "idx": idx,  # starts at 1
        "title": remove_whitespace(title),
        "author": remove_whitespace(author),
        "raw": raw,
    }


def get_roudoku_entries(raw_text: str) -> list[Entry]:
    entries = raw_text.strip().split("\n\n")
    roudoku_entries: list[Entry] = []
    for idx, entry in enumerate(entries, 1):
        lines = entry.split("\n")
        # This only happens once in the 67.txt file:
        # 苦楽
        # ある人の問いに答えてー絵を作る時の作家の心境について私はこう考えています。
        # 著者：上村 松園　読み手：青木 みな子　時間：6分30秒
        # > Just delete the 苦楽 part
        if len(lines) == 3:
            del lines[0]
        title = lines[0].strip()
        info = lines[1]
        assert "著者" in info, f"The line {entry}\nwith info\n{info}\nhas no author?"
        author = info.split("著者：")[1].split("　")[0]
        entry = get_entry(title, author, f"{title} - {author}", idx)
        roudoku_entries.append(entry)
    return roudoku_entries


def get_lingq_entries(ipath: Path) -> list[Entry]:
    """Get lingq entries from the output of the "show" command.

    Created with: lingq show course ja 793510 > course.txt

    Looks like:
    01: 1. がちょう の たんじょうび - 新美南吉
    02: 1.1. 宿命 死なない 蛸 - 萩原 朔 太郎
    03: 2. 皇帝の使者 - Kafka
    04: 2.1. もぐら と コスモス - 原 民 喜
    05: 3. 梅 の におい - 夢野 久作
    06: 4. 最初の 悲哀 - 竹久 夢二
    """
    lingq_path = ipath.with_stem(f"{ipath.stem}_lingq")
    if not lingq_path.exists():
        course_id = PATH_NAME_TO_COURSE_ID[ipath.stem]
        cmd = f"lingq show course ja {course_id} > {lingq_path}"
        print(f"{lingq_path} not found. Run this command:\n{cmd}")
        sys.exit(1)
    lingq_entries: list[Entry] = []
    sep = "-"
    with lingq_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            *_, title = line.split(".")  # remove idx
            # There may be multiple " - " in the line but we assume that
            # it is the last one that separates title and author.
            #
            # I fixed everything in LingQ but I leave this in case I make
            # the same mistake in the future.
            *title, author = title.split(sep)
            if len(title) > 1:
                print(f"[WARNING] Multiple '{sep}' in line {line}")
            title = sep.join(title)
            # Remove non-japanese part: 星の銀貨,DIESTERNTALER > 星の銀貨
            title = title.split(",")[0]
            entry = get_entry(title, author, line, idx)
            lingq_entries.append(entry)
    return lingq_entries


def check_gaps(roudoku_entries: list[Entry], lingq_entries: list[Entry]) -> None:
    """Print the first difference and exit.

    Only titles are compared. Author's names could vary.
    We may want to change them, latinize them, or truncate them
    due to LingQ's title size limit.
    """
    idx_roudoku = 0
    padding = len(str(len(lingq_entries)))

    if len(lingq_entries) != len(roudoku_entries):
        print(
            f"⚠️ There are {len(lingq_entries)} lingq entries "
            f"and {len(roudoku_entries)} roudoku entries"
        )

    for idx, lingq_entry in enumerate(lingq_entries, 1):
        lingq_title = lingq_entry["title"]

        while idx_roudoku < len(roudoku_entries):
            roudoku_entry = roudoku_entries[idx_roudoku]
            roudoku_title = roudoku_entry["title"]
            idx_roudoku += 1

            if cmp_normalized(lingq_title, roudoku_title):
                print(f"✅ {idx:0{padding}d}", flush=True, end="\r")
                break

            print(
                f"❌ {idx:0{padding}d} @lingq: '{lingq_title.strip()}'\n"
                f"@lingq:   {lingq_entry}\n@roudoku: {roudoku_entry}",
            )
            if idx > 0:
                print(f"📌 Add roudoku '{roudoku_title}' before '{lingq_entry['raw'].strip()}'")
                # May give wrong suggestions if there are consecutive holes
                hole_idx = int(lingq_entry["raw"].split()[1][:-1])
                suggested_idx = f"{(hole_idx - 1):0{padding}d}.1"
                print(f"📌 Suggested title: {suggested_idx}{roudoku_entry['raw']}")
                if any(suggested_idx in entry["raw"] for entry in lingq_entries):
                    print(f"⚠️ The suggested idx '{suggested_idx}' is already in use")

            # Stop at first
            return

        if idx_roudoku == len(roudoku_entries):
            print("No more roudoku entries")
            return


def main() -> None:
    ipath = Path("etc/aozora_roudoku/45.txt")
    assert ipath.stem in ("45", "67")
    with ipath.open() as f:
        raw_text = f.read()
    roudoku_entries = get_roudoku_entries(raw_text)
    lingq_entries = get_lingq_entries(ipath)
    check_gaps(roudoku_entries, lingq_entries)


if __name__ == "__main__":
    main()
