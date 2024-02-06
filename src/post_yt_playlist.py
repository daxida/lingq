import time

import yt_dlp
from requests_toolbelt.multipart.encoder import MultipartEncoder
from utils import LingqHandler, timing

LANGUAGE_CODE = "ja"
SLEEP_SECONDS = 5
COURSE_ID = "537808"

# To download a whole channel with yt-dlp, try:
# https://www.youtube.com/@{userName}/videos
PLAYLIST_URL = "https://www.youtube.com/watch?v=gLq7vKsvu9E&list=PLINFE8v4DOhsXKG7KSrbeMt-0EVK3OxAM"
PLAYLIST_URL = "https://www.youtube.com/@mikurealjapanese/videos"

# The script will upload "at most" MAX_UPLOADS videos to LingQ
MAX_UPLOADS = 200

# If true, skip videos without Closed Captions in the desired language.
# (ISSUE ?) LANGUAGE_CODE (the LingQ argument) is used for checking suitability in yt-dlp
# (WARNING) Setting this to true will make the yt-dlp part of the script quite slower
#           since it also has to download the subtitles.
SKIP_WITHOUT_CC = False

# If true, skip videos already imported to the course (if false, overwrite existing ones)
SKIP_ALREADY_UPLOADED = True

# fmt: off
RED    = "\033[31m"  # Error
GREEN  = "\033[32m"  # Success
YELLOW = "\033[33m"  # Skips
CYAN   = "\033[36m"  # Timings
RESET  = "\033[0m"
# fmt: on


def filter_playlist_entries(handler: LingqHandler, playlist_entries):
    if SKIP_WITHOUT_CC:
        filtered_playlist_entries = list()
        for entry in playlist_entries:
            title = entry["title"]
            if "subtitles" in entry and LANGUAGE_CODE in entry["subtitles"]:
                filtered_playlist_entries.append(entry)
            else:
                print(f"{YELLOW}[skip: no CC]{RESET} {title}")
        playlist_entries = filtered_playlist_entries

    if SKIP_ALREADY_UPLOADED:
        collection = handler.get_collection_from_id(LANGUAGE_CODE, COURSE_ID)
        lessons = collection["lessons"]
        lessons_urls = [lesson["originalUrl"] for lesson in lessons]
        lessons_urls = set(lessons_urls)

        filtered_playlist_entries = list()
        for entry in playlist_entries:
            title = entry["title"]
            url = entry["original_url" if SKIP_WITHOUT_CC else "url"]
            if url not in lessons_urls:
                filtered_playlist_entries.append(entry)
            else:
                print(f"{YELLOW}[skip: already uploaded]{RESET} {title}")
        playlist_entries = filtered_playlist_entries

    skipped = len(playlist_entries) - len(filtered_playlist_entries)
    print(f"Skipped {skipped} videos")

    return playlist_entries


@timing
def process_playlist_entries(handler: LingqHandler, playlist_entries, max_iterations=10):
    playlist_entries = filter_playlist_entries(handler, playlist_entries)

    n_entries = len(playlist_entries)
    max_entries = min(n_entries, max_iterations)
    pad = len(str(max_entries))
    print(f"Uploading {max_entries} videos (from {n_entries} available)")

    for i, entry in enumerate(playlist_entries):
        if i >= max_iterations:
            break

        title = entry["title"]
        # url = entry["url"] # assumes "extract_flat": "in_playlist"
        url = entry["original_url" if SKIP_WITHOUT_CC else "url"]

        m = MultipartEncoder(
            [
                ("title", title),
                ("url", url),
                ("collection", COURSE_ID),
                ("source", "Firefox"),
                ("save", "true"),
            ]
        )

        response = handler.post_from_multiencoded_data(LANGUAGE_CODE, m)

        if response.status_code == 201:
            padded_idx = f"{i + 1}".zfill(pad)
            progress_msg = f"{GREEN}[{padded_idx}/{max_entries}]{RESET}"
            print(f"{progress_msg} Uploaded successfully: {title}")
        else:
            print(f"{RED}[Failed to upload]{RESET} {title}.")
            print(f"Response code: {response.status_code}")
            if response.status_code == 524:
                print("Cloudflare timeout (> 100 secs).")
            else:
                print(f"Response text: {response.text}")
            print(f"url: {url}")

        if i < n_entries - 1:
            time.sleep(SLEEP_SECONDS)


@timing
def get_playlist(URL, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)
        sanitized = ydl.sanitize_info(info)
        # print(json.dumps(sanitized, indent=2)) # DEBUG

        return sanitized


@timing
def main():
    handler = LingqHandler()

    ydl_opts = {
        # Set title language "extractor_args": {"youtube": {"lang": ["zh-TW"]}},
        # "forceprint": {"video": ["title", "url"]}, # DEBUG
        "quiet": False,
        # "simulate": True, # not needed if .extract_info(download=False)
        "ignoreerrors": False,
        "verbose": False,
    }

    # If we don't want to filter by CC, just bulk download the urls (faster).
    if not SKIP_WITHOUT_CC:
        ydl_opts.update({"extract_flat": "in_playlist"})

    playlist_data = get_playlist(PLAYLIST_URL, ydl_opts)

    if "entries" in playlist_data:
        process_playlist_entries(handler, playlist_data["entries"], MAX_UPLOADS)

    print("Finished!")


if __name__ == "__main__":
    main()
