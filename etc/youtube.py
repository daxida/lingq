"""Download a youtube playlist in a LingQ compatible structure."""

from pathlib import Path

import requests
import yt_dlp
from defusedxml import ElementTree

TEST_URL = "https://www.youtube.com/playlist?list=PLRaS49ob6Wpnu3pRU_w99w_PPoiQQny15"
# URLS = ["D8A2q3awnsU", "5kmyOfvucp8", "GUqFU5u7rLQ"]
TMP_FOLDER = Path("playlist")
TTML_URL = "{http://www.w3.org/ns/ttml}p"


def fetch(url: str) -> str:
    return requests.get(url, timeout=5).text


def ttml_to_txt(ttml_content: str) -> tuple[str, str]:
    root = ElementTree.fromstring(ttml_content)
    out = []

    for p in root.iter(TTML_URL):
        text = "".join(p.itertext())
        out.append(text)

    return "\n".join(out), "txt"


def ttml_to_vtt(ttml_content: str) -> tuple[str, str]:
    root = ElementTree.fromstring(ttml_content)
    vtt_output = ["WEBVTT\n"]

    for p in root.iter(TTML_URL):
        begin = p.attrib.get("begin")
        end = p.attrib.get("end")
        text = "".join(p.itertext())

        vtt_output.extend((f"{begin} --> {end}", text, ""))

    return "\n".join(vtt_output), "vtt"


def postformat(text: str, ext: str) -> tuple[str, str]:
    return ttml_to_vtt(text)
    return text, ext


def save_to_disk(content: str, opath: Path) -> None:
    with opath.open("w", encoding="utf-8") as subtitle_file:
        subtitle_file.write(content)
    print(f"Subtitle saved to {opath}")


def main(
    playlist_url: str = TEST_URL,
    lang: str = "ja",
    text_ext: str = "ttml",
    audios_ext: str = "mp3",
) -> None:
    texts_folder = TMP_FOLDER / "texts"
    audios_folder = TMP_FOLDER / "audios"
    texts_folder.mkdir(parents=True, exist_ok=True)
    audios_folder.mkdir(parents=True, exist_ok=True)

    # Using the title in the template may lead to cases where
    # %(title)s is different from entry["title"], effectively messing
    # the pairing later on.
    # I've seen entry["title"] contain a ? while the template had ？
    ydl_opts = {
        "outtmpl": f"{audios_folder}/%(title)s",
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audios_ext,
            },
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)
        if result is None:
            print("Could not extract info. Exiting.")
            return

        print(f"Start download of {result["title"]}")

        # import json
        # with open(Path("dump.json"), "w", encoding="utf-8") as json_file:
        #     json.dump(result, json_file, ensure_ascii=False, indent=4)
        entries = result["entries"]

        for entry in entries:
            ident = entry["title"]

            if subs := entry["subtitles"]:
                print(f"Video {ident}: has manually added captions.")
                subslang = subs[lang]
                ext = next(x for x in subslang if x["ext"] == text_ext)
                url = ext["url"]
                out = fetch(url)
                out, new_ext = postformat(out, text_ext)
                # opath = texts_folder / Path(f"{ident}-cc.{new_ext}")
                opath = texts_folder / Path(f"{ident}.{new_ext}")
                save_to_disk(out, opath)
            elif subs := entry["automatic_captions"]:
                print(f"Video {ident}: has auto-generated captions.")
                subslang = subs[lang]
                ext = next(x for x in subslang if x["ext"] == text_ext)
                url = ext["url"]
                out = fetch(url)
                out, new_ext = postformat(out, text_ext)
                # opath = texts_folder / Path(f"{ident}-auto.{new_ext}")
                opath = texts_folder / Path(f"{ident}.{new_ext}")
                save_to_disk(out, opath)
                print("Automatic captions found, downloading MP3...")
                opath = audios_folder / ident
                opath = opath.with_suffix(f".{audios_ext}")
                if opath.exists():
                    print("Already downloaded audio")
                else:
                    ydl.download([entry["webpage_url"]])
            else:
                print(f"Video {ident}: has no subtitles available.")


if __name__ == "__main__":
    main()
