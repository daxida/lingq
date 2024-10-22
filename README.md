# LingQ

Command line utilities and scripts for interacting with [LingQ's](https://www.lingq.com/) API.

You will need a LingQ API key. You can get it from [here](https://www.lingq.com/en/accounts/apikey/).

## Installation

(Optional) Create a virtual environment: `python3 -m venv venv` and activate it.

Then either directly:
```
pip install git+https://github.com/daxida/lingq
```
Or clone the repository:
```
git clone https://github.com/daxida/lingq
cd lingq
pip install .
```

Finally, create an `.env` file in the root directory with the following format:
```
APIKEY='yourLingqApiKey'
```

## How to use

Some examples:
```
# Upload a playlist to a greek course.
lingq postyt el 129129 "https://www.youtube.com/@awesomeyoutuber"

# Bulk upload a book split by chapters.
lingq post el 129139 "example/texts" -a "example/audios" --pairing_strategy zip

# Timestamp an entire german course.
lingq timestamp de 129129
```

The full set of commands can be found with `lingq --help`. 
Per command information uses again the help flag: `lingq timestamp --help`.

A command tree made with [this](https://github.com/whwright/click-command-tree):
```
cli - Lingq command line scripts.
├── get - Get commands.
│   ├── courses - Get every course from a list of languages.
│   ├── lessons - Get every lesson from a course id.
│   └── pictures - Get pictures.
├── markdown - Generate markdown files for the given language codes.
├── overview - Library overview.
├── patch - Patch commands.
│   ├── audios - Patch commands.
│   └── texts - Not implemented.
├── post - Post command.
├── postyt - Post youtube playlist.
├── resplit - Resplit a course (only for japanese).
├── sort - Sort all lessons from a course.
├── timestamp - Generate timestamps for a course.
```

## Etc.

Mainly undocumented scripts to scrape, process text and audio, and to manually use whisper.

If you want to use some of it:

```
git clone https://github.com/daxida/lingq
cd lingq
pip install .[etc]
# And for example
python3 etc/scrape/japanese/sc_itazura.py
```

## Links

- Legacy (v1.0 and v2.0) LingQ's API [documentation](https://www.lingq.com/apidocs/index.html).
- A miniminalist [script](https://github.com/paulywill/lingq_upload) to upload content to LingQ. May not be up to date.
- A [script](https://github.com/justbrendo/lingq-yt) to upload youtube playlists to LingQ with Whisper generated subtitles.
- For [splitting](https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04) downloaded audio from youtube.
- Another API wrapper in [ruby](https://github.com/evizitei/lingq)
