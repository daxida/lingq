# LingQ

Scripts for basic interactions with [LingQ's](https://www.lingq.com/) API.

## How to use

1. (Optional) Create a virtual environment: `python3 -m venv venv`.
2. Install the required packages: `pip install -r requirements.txt`.
3. Get your API key from [here](https://www.lingq.com/en/accounts/apikey/).
4. Create a `.env` file in the root directory with the following format:
   <br>`APIKEY="your-lingq-api-key"`.
5. Run your desired script:
   ```
   # Modify the parameters in post_yt_playlist.py and...
   python3 post_yt_playlist.py
   ```

## Description

- **Get** (download lessons): 
  - **get_lessons**: download audio/text from a course.
  - **get_courses**: download audio/text from all the courses in a/every language 
    (NOTE: This reorders your 'Continue studying' shelf).
  - **get_pictures**: download pictures from a course.

- **Post** (upload lessons):
  - **post**: Upload text or text with audio.
  - **post_yt_playlist**: Upload an entire youtube playlist.

- **Patch** (fix or complete lessons): 
  - Bulk upload audio to a collection with only text. 
  - Can be used to overwrite text, and to bypass word limit (not recommended).

- **Other scripts**:
  - **Make markdown**: create a markdown of courses.
  - **Library overview**: get an overview of the library in a language.
  - **Generate timestamps**: generate timestamps for a course.
  - **Sort lessons**: sort your lessons according to some criteria.
  - **Whisper**: Download a youtube playlist in a LingQ friendly format (to use together with `post`).
  - **Processing text**: A bunch of ad-hoc scripts.
  - **Processing audio**: uses [this](https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04) to split the timestamps if the original video didn't have them and you wanted to do it manually.

## Links

- A miniminalist [script](https://github.com/paulywill/lingq_upload) to upload content to LingQ. May not be up to date.
- A [script](https://github.com/justbrendo/lingq-yt) to upload youtube playlists to LingQ with Whisper generated subtitles.
- For [splitting](https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04) downloaded audio from youtube.