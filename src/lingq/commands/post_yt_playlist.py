"""Use yt-dlp to scan a youtube playlist.

- Identifies if a lesson has Captions / Auto-generated subtitles / None
- Downloads the Auto-generated subtitles there are no captions

With the recent LingQ changes, it only works with videos that have closed
captions. Auto-generated subtitles or none of them will result in failure.
"""

import asyncio
from typing import Any

import yt_dlp  # type: ignore

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.utils import timing

# Until we find something better
OldPlaylist = list[Any]


def has_closed_captions(lang: str, entry: Any) -> bool:
    return "subtitles" in entry and lang in entry["subtitles"]


async def filter_playlist(
    handler: LingqHandler,
    course_id: int,
    playlist: OldPlaylist,
    skip_uploaded: bool,
    skip_no_cc: bool,
) -> OldPlaylist:
    # First filter 'None's that may result from downloading errors.
    playlist = [entry for entry in playlist if entry is not None]
    initial_size = len(playlist)

    if skip_no_cc:
        filtered_playlist: OldPlaylist = []
        for entry in playlist:
            title = entry["title"]
            if not has_closed_captions(handler.lang, entry):
                logger.info(f"[skip: no CC] {title}")
            else:
                filtered_playlist.append(entry)

        playlist = filtered_playlist

    if skip_uploaded:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        lesson_urls = {lesson.video_url for lesson in lessons}

        filtered_playlist = []
        for entry in playlist:
            title = entry["title"]
            url = entry["original_url" if skip_no_cc else "url"]
            if url not in lesson_urls:
                filtered_playlist.append(entry)
            else:
                logger.info(f"[skip: already uploaded] {title}")
        playlist = filtered_playlist

    skipped = initial_size - len(playlist)
    logger.debug(f"Skipped {skipped} videos.")

    return playlist


async def post_playlist_entry(
    handler: LingqHandler,
    course_id: int,
    entry: Any,
    idx: int,
    playlist_size: int,
    skip_no_cc: bool,
) -> None:
    """Request that only sends the url of the youtube video to LingQ.
    They do the subtitle generation when needed (that is, when there are no CC).
    """
    title = entry["title"]
    lang = handler.lang
    # logger.critical(entry.get("subtitles", "NSUB"))
    if not has_closed_captions(lang, entry):
        logger.warning(f"No closed captions: skipping {title}.")
        return

    # assert len(title) < 60  # Max allowed
    # url = entry["url"] # assumes "extract_flat": "in_playlist"
    url = entry["original_url" if skip_no_cc else "url"]
    data: dict[str, str] = {
        "title": title,
        "url": url,
        "collection": str(course_id),
        "save": "true",
    }

    response = await handler.post_from_data_dict(data, raw=True)

    if response.status == 201:
        padded_idx = f"{idx + 1}".zfill(len(str(playlist_size)))
        progress_msg = f"[{padded_idx}/{playlist_size}]"
        logger.success(f"{progress_msg} Uploaded: {title}")


async def post_playlist(
    handler: LingqHandler,
    course_id: int,
    playlist: OldPlaylist,
    skip_no_cc: bool,
) -> None:
    for idx, entry in enumerate(playlist):
        await post_playlist_entry(handler, course_id, entry, idx, len(playlist), skip_no_cc)


async def post_playlist_fully_async(
    handler: LingqHandler,
    course_id: int,
    playlist: OldPlaylist,
    download_audio_info: bool,
) -> None:
    """Faster version if you don't care about the order in which the lessons are posted."""
    tasks = [
        post_playlist_entry(handler, course_id, entry, idx, len(playlist), download_audio_info)
        for idx, entry in enumerate(playlist)
    ]
    await asyncio.gather(*tasks)


@timing
def get_playlist(url: str, ydl_opts: dict[str, Any]) -> Any:
    logger.info("Downloading playlist info")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info: Any = ydl.extract_info(url, download=False)  # type: ignore
        sanitized: Any = ydl.sanitize_info(info)  # type: ignore
        # import json
        # print(json.dumps(sanitized, indent=2))  # DEBUG

        return sanitized


async def post_yt_playlist_async(
    lang: str,
    course_id: int,
    playlist_url: str,
    skip_uploaded: bool,
    skip_no_cc: bool,
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
        "extractor_args": {"youtube": {"lang": [lang]}},
    }

    # Just bulk download the urls (faster but contains no sub info).
    if not skip_no_cc:
        ydl_opts.update({"extract_flat": "in_playlist"})  # type: ignore

    playlist_data = get_playlist(playlist_url, ydl_opts)

    if "entries" in playlist_data:
        async with LingqHandler(lang) as handler:
            playlist = playlist_data["entries"]
            playlist = await filter_playlist(
                handler, course_id, playlist, skip_uploaded, skip_no_cc
            )
            logger.info(f"Uploading {len(playlist)} video(s).")
            await post_playlist(handler, course_id, playlist, skip_no_cc)


@timing
def post_yt_playlist(
    lang: str,
    course_id: int,
    playlist_url: str,
    *,
    skip_uploaded: bool,
    skip_no_cc: bool = True,
) -> None:
    """Main function to download and upload videos from a YouTube playlist to LingQ.

    Args:
        lang (str): The language code for the course.
        course_id (int): The ID of the course to which videos will be uploaded.
        playlist_url (str): The URL of the YouTube playlist or channel to download videos from.
        skip_uploaded (bool): If True, skip videos already uploaded to the course.
            If False, overwrite existing ones.
        skip_no_cc (bool): If True, skip videos without Closed Captions (CC).
            Requires download_audio_info to be true in order to get the necessary information.
    """
    asyncio.run(
        post_yt_playlist_async(
            lang,
            course_id,
            playlist_url,
            skip_uploaded,
            skip_no_cc,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    # NOTE: To download a whole channel with yt-dlp, try:
    # https://www.youtube.com/@{userName}/videos
    PLAYLIST_URL = "https://www.youtube.com/@mikurealjapanese/videos"

    post_yt_playlist(
        lang="ja",
        course_id=537808,
        playlist_url=PLAYLIST_URL,
        skip_uploaded=True,
        skip_no_cc=True,
    )
