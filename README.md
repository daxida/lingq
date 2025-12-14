# LingQ

[![GitHub](https://img.shields.io/badge/-black?logo=github)](https://github.com/daxida/lingq)
[![image](https://img.shields.io/pypi/v/lingq.svg)](https://pypi.python.org/pypi/lingq)
[![image](https://img.shields.io/pypi/l/lingq.svg)](https://github.com/daxida/lingq/blob/main/LICENSE)

Command line utilities and scripts for interacting with [LingQ](https://www.lingq.com/)'s API.

You will need a LingQ API key. You can get it from [here](https://www.lingq.com/en/accounts/apikey/).

## Installation

```
pip install lingq
```

Then run:

```
lingq setup yourLingqApiKey
```

## Usage

```
# Upload a YouTube playlist to a Greek course
lingq postyt el 129129 "https://www.youtube.com/@awesomeyoutuber"

# Bulk upload a book split by chapters
lingq post el 129139 -t "example/texts" -a "example/audios" --pairing-strategy zip

# Add timestamps to a German course
lingq timestamp de 129129
```

The full set of commands can be found with `lingq --help`.
Per command information uses again the help flag: `lingq timestamp --help`.

See the [documentation](https://daxida.github.io/lingq/) for more information.

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

- A [repo](https://github.com/daxida/lingq-fa) for LingQ-compatible forced alignment.
- Legacy (v1.0 and v2.0) LingQ's API [documentation](https://www.lingq.com/apidocs/index.html).
- A [repo](https://github.com/paulywill/lingq_upload) to upload content to LingQ (may be outdated).
- A [repo](https://github.com/justbrendo/lingq-yt) to upload YouTube playlists to LingQ with Whisper subtitles.
- A [repo](https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04) to split downloaded audio from YouTube.
- A [repo](https://github.com/evizitei/lingq) for an API wrapper in ruby.
