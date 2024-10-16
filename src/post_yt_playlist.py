import asyncio
from typing import Any

import yt_dlp  # type: ignore
from lingqhandler import LingqHandler
from utils import Colors, timing  # type: ignore

# Until we find something better
Playlist = list[Any]


def has_closed_captions(language_code: str, entry: Any) -> bool:
    return "subtitles" in entry and language_code in entry["subtitles"]


async def filter_playlist(
    handler: LingqHandler,
    course_id: str,
    playlist: Playlist,
    skip_uploaded: bool,
    download_audio: bool,
    skip_without_cc: bool,
) -> Playlist:
    # First filter 'None's that may result from downloading errors.
    playlist = [entry for entry in playlist if entry is not None]
    initial_size = len(playlist)

    if download_audio:
        filtered_playlist: Playlist = list()
        for entry in playlist:
            title = entry["title"]
            if skip_without_cc and not has_closed_captions(handler.language_code, entry):
                print(f"{Colors.SKIP}[skip: no CC]{Colors.END} {title}")
            else:
                filtered_playlist.append(entry)

        playlist = filtered_playlist

    if skip_uploaded:
        collection = await handler.get_collection_json_from_id(course_id)
        lessons = collection["lessons"]
        lessons_urls = [lesson["originalUrl"] for lesson in lessons]
        lessons_urls = set(lessons_urls)

        filtered_playlist = list()
        for entry in playlist:
            title = entry["title"]
            url = entry["original_url" if download_audio else "url"]
            if url not in lessons_urls:
                filtered_playlist.append(entry)
            else:
                print(f"{Colors.SKIP}[skip: already uploaded]{Colors.END} {title}")
        playlist = filtered_playlist

    skipped = initial_size - len(playlist)
    print(f"Skipped {skipped} videos.")

    return playlist


async def post_playlist_entry(
    handler: LingqHandler,
    course_id: str,
    entry: Any,
    idx: int,
    playlist_size: int,
    download_audio: bool,
) -> None:
    """
    Request that only sends the url of the youtube video to LingQ.
    They do the subtitle generation when needed (that is, when there are no CC).
    """
    title = entry["title"]
    # assert len(title) < 60  # Max allowed
    # url = entry["url"] # assumes "extract_flat": "in_playlist"
    url = entry["original_url" if download_audio else "url"]
    data = {
        "title": title,
        "url": url,
        "collection": course_id,
        "save": "true",
    }

    response = await handler.post_from_multipart(data)

    if response.status == 201:
        padded_idx = f"{idx + 1}".zfill(len(str(playlist_size)))
        progress_msg = f"{Colors.OK}[{padded_idx}/{playlist_size}]{Colors.END}"
        cc_msg = "(cc)" if has_closed_captions(handler.language_code, entry) else "(whisper)"
        print(f"{progress_msg} Uploaded successfully: {title} {cc_msg}")
    else:
        print(f"{Colors.FAIL}[Failed to upload]{Colors.END} {title}.")
        exit(0)


async def post_playlist(
    handler: LingqHandler,
    course_id: str,
    playlist: Playlist,
    download_audio: bool,
) -> None:
    for idx, entry in enumerate(playlist):
        await post_playlist_entry(handler, course_id, entry, idx, len(playlist), download_audio)


async def post_playlist_fully_async(
    handler: LingqHandler,
    course_id: str,
    playlist: Playlist,
    download_audio: bool,
) -> None:
    """Faster version if you don't care about the order in which the lessons are posted."""
    tasks = [
        post_playlist_entry(handler, course_id, entry, idx, len(playlist), download_audio)
        for idx, entry in enumerate(playlist)
    ]
    await asyncio.gather(*tasks)


@timing
def get_playlist(url: str, ydl_opts: dict[str, Any]) -> Any:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info: Any = ydl.extract_info(url, download=False)  # type: ignore
        sanitized: Any = ydl.sanitize_info(info)  # type: ignore
        # import json
        # print(json.dumps(sanitized, indent=2))  # DEBUG

        return sanitized


async def _post_yt_playlist(
    language_code: str,
    course_id: str,
    playlist_url: str,
    skip_uploaded: bool,
    download_audio: bool,
    skip_without_cc: bool,
) -> None:
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
    if not download_audio:
        ydl_opts.update({"extract_flat": "in_playlist"})  # type: ignore

    playlist_data = get_playlist(playlist_url, ydl_opts)

    if "entries" in playlist_data:
        async with LingqHandler(language_code) as handler:
            playlist = playlist_data["entries"]
            playlist = await filter_playlist(
                handler, course_id, playlist, skip_uploaded, download_audio, skip_without_cc
            )
            print(f"Uploading {len(playlist)} videos.")
            await post_playlist(handler, course_id, playlist, download_audio)

    print("Finished!")


@timing
def post_yt_playlist(
    language_code: str,
    course_id: str,
    playlist_url: str,
    skip_uploaded: bool,
    download_audio: bool,
    skip_without_cc: bool,
) -> None:
    """
    Main function to download and upload videos from a YouTube playlist to LingQ.

    Args:
        language_code (str): The language code for the course.
        course_id (str): The ID of the course to which videos will be uploaded.
        playlist_url (str): The URL of the YouTube playlist or channel to download videos from.
        skip_uploaded (bool): If True, skip videos already uploaded to the course.
            If False, overwrite existing ones.
        download_audio (bool): If True, download audio for the videos.
            Setting this to true will make the script considerably slower.
            It is required for generating subtitles.
        skip_without_cc (bool): If True, skip videos without Closed Captions (CC).
            Requires download_audio to be true in order to get the necessary information.
    """
    asyncio.run(
        _post_yt_playlist(
            language_code,
            course_id,
            playlist_url,
            skip_uploaded,
            download_audio,
            skip_without_cc,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    # NOTE: To download a whole channel with yt-dlp, try:
    # https://www.youtube.com/@{userName}/videos
    PLAYLIST_URL = "https://www.youtube.com/@mikurealjapanese/videos"

    post_yt_playlist(
        language_code="ja",
        course_id="537808",
        playlist_url=PLAYLIST_URL,
        skip_uploaded=True,
        download_audio=False,
        skip_without_cc=False,
    )
