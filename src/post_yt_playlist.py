import asyncio
from typing import Any, Dict, List

import yt_dlp  # type: ignore
from lingqhandler import LingqHandler
from utils import timing  # type: ignore

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"

# To download a whole channel with yt-dlp, try:
# https://www.youtube.com/@{userName}/videos
# PLAYLIST_URL = "https://www.youtube.com/watch?v=gLq7vKsvu9E&list=PLINFE8v4DOhsXKG7KSrbeMt-0EVK3OxAM"
PLAYLIST_URL = "https://www.youtube.com/@mikurealjapanese/videos"

# The script will upload "at most" MAX_UPLOADS videos to LingQ
MAX_UPLOADS = 50

# If true, skip videos already imported to the course (if false, overwrite existing ones)
SKIP_UPLOADED = True

# NOTE: This will make the script considerably slower but it's required for generating subtitles
DOWNLOAD_AUDIO = False

# If true, skip videos without Closed Captions (CC) in the desired language.
SKIP_WITHOUT_CC = False  # requires DOWNLOAD_AUDIO to be True


# fmt: off
RED    = "\033[31m"  # Error
GREEN  = "\033[32m"  # Success
YELLOW = "\033[33m"  # Skips
CYAN   = "\033[36m"  # Timings
RESET  = "\033[0m"
# fmt: on

# Until we find something better
Playlist = List[Any]


def has_closed_captions(entry: Any) -> bool:
    return "subtitles" in entry and LANGUAGE_CODE in entry["subtitles"]


async def filter_playlist(handler: LingqHandler, playlist: Playlist) -> Playlist:
    # First filter 'None's that may result from downloading errors.
    playlist = [entry for entry in playlist if entry is not None]
    initial_size = len(playlist)

    if DOWNLOAD_AUDIO:
        filtered_playlist: Playlist = list()
        for entry in playlist:
            title = entry["title"]
            if SKIP_WITHOUT_CC and not has_closed_captions(entry):
                print(f"{YELLOW}[skip: no CC]{RESET} {title}")
            else:
                filtered_playlist.append(entry)

        playlist = filtered_playlist

    if SKIP_UPLOADED:
        collection = await handler.get_collection_json_from_id(COURSE_ID)
        assert collection is not None
        lessons = collection["lessons"]
        lessons_urls = [lesson["originalUrl"] for lesson in lessons]
        lessons_urls = set(lessons_urls)

        filtered_playlist = list()
        for entry in playlist:
            title = entry["title"]
            url = entry["original_url" if DOWNLOAD_AUDIO else "url"]
            if url not in lessons_urls:
                filtered_playlist.append(entry)
            else:
                print(f"{YELLOW}[skip: already uploaded]{RESET} {title}")
        playlist = filtered_playlist

    skipped = initial_size - len(playlist)
    print(f"Skipped {skipped} videos")

    return playlist


async def post_playlist_entry(
    handler: LingqHandler, entry: Any, idx: int, max_entries: int
) -> None:
    """
    Request that only sends the url of the youtube video to LingQ.
    They do the subtitle generation when needed (that is, when there are no CC).
    """
    title = entry["title"]
    # assert len(title) < 60  # Max allowed
    # url = entry["url"] # assumes "extract_flat": "in_playlist"
    url = entry["original_url" if DOWNLOAD_AUDIO else "url"]
    data = {
        "title": title,
        "url": url,
        "collection": COURSE_ID,
        "save": "true",
    }

    response = await handler.post_from_multipart(data)

    if response.status == 201:
        padded_idx = f"{idx + 1}".zfill(len(str(max_entries)))
        progress_msg = f"{GREEN}[{padded_idx}/{max_entries}]{RESET}"
        cc_msg = "(cc)" if has_closed_captions(entry) else "(whisper)"
        print(f"{progress_msg} Uploaded successfully: {title} {cc_msg}")
    else:
        print(f"{RED}[Failed to upload]{RESET} {title}.")
        exit(0)


async def post_playlist(handler: LingqHandler, playlist: Playlist, max_entries: int) -> None:
    for idx, entry in enumerate(playlist):
        await post_playlist_entry(handler, entry, idx, max_entries)


async def post_playlist_fully_async(
    handler: LingqHandler, playlist: Playlist, max_entries: int
) -> None:
    """Faster version if you don't care about the order in which the lessons are posted."""
    tasks = [
        post_playlist_entry(handler, entry, idx, max_entries) for idx, entry in enumerate(playlist)
    ]
    await asyncio.gather(*tasks)


@timing
def get_playlist(url: str, ydl_opts: Dict[str, Any]) -> Any:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info: Any = ydl.extract_info(url, download=False)  # type: ignore
        sanitized: Any = ydl.sanitize_info(info)  # type: ignore
        # import json
        # print(json.dumps(sanitized, indent=2))  # DEBUG

        return sanitized


async def post_yt_playlist():
    ydl_opts = {
        # Set title language "extractor_args": {"youtube": {"lang": ["zh-TW"]}},
        # "forceprint": {"video": ["title", "url"]}, # DEBUG
        "quiet": True,
        # "simulate": True, # not needed if .extract_info(download=False)
        # If a playlist has private videos, '"ignoreerrors": True' will crash the whole
        # program. If you know it hasn't, you would probably want this set to 'False'.
        "ignoreerrors": True,
        "verbose": False,
    }

    # Just bulk download the urls (faster).
    if not DOWNLOAD_AUDIO:
        ydl_opts.update({"extract_flat": "in_playlist"})  # type: ignore

    playlist_data = get_playlist(PLAYLIST_URL, ydl_opts)

    if "entries" in playlist_data:
        async with LingqHandler(LANGUAGE_CODE) as handler:
            playlist = playlist_data["entries"]
            playlist = await filter_playlist(handler, playlist)

            n_entries = len(playlist)
            max_entries = min(n_entries, MAX_UPLOADS)
            print(f"Uploading {max_entries} videos (from {n_entries} available)")
            playlist = playlist[:MAX_UPLOADS]

            await post_playlist(handler, playlist, max_entries)

    print("Finished!")


@timing
def main():
    asyncio.run(post_yt_playlist())


if __name__ == "__main__":
    main()
