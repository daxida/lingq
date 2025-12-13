# Commands Overview

The LingQ CLI provides a comprehensive set of commands for managing your LingQ content. This page provides an overview of all available commands.

!!! tip "Getting Help"
    Use `--help` with any command to see detailed usage information:
    ```bash
    lingq --help              # Show all commands
    lingq post --help         # Show help for post command
    lingq get courses --help  # Show help for get courses command
    ```

## Command Structure

Commands are organized into logical groups:

```
lingq [GROUP] [COMMAND] [OPTIONS]
```

## Setup

### `lingq setup`

Creates or updates the configuration file with your LingQ API key.

```bash
lingq setup yourLingqApiKey
```

**Arguments:**
- `api_key`: Your LingQ API key from https://www.lingq.com/en/accounts/apikey/

## Get Commands

Download content from LingQ.

### `lingq get courses`

Get every course from a list of languages.

```bash
lingq get courses en de ja
```

**Arguments:**
- `language_codes`: Space-separated list of language codes (e.g., en, de, ja, el)

**Options:**
- `--owned`: Get only courses you own (default: all courses)

### `lingq get lesson`

Get a single lesson by its ID.

```bash
lingq get lesson 12345678
```

**Arguments:**
- `lesson_id`: The ID of the lesson to retrieve

### `lingq get lessons`

Get all lessons from a course.

```bash
lingq get lessons en 129129
```

**Arguments:**
- `language_code`: Language code (e.g., en, de, ja)
- `course_id`: The ID of the course (find it with `lingq show my <language_code>` or from the course URL)

!!! info "How to Find Course IDs"
    - Run `lingq show my en` to see all your English courses with their IDs
    - Or get the ID from the URL: `https://www.lingq.com/.../course/129129` → 129129

### `lingq get words`

Export your vocabulary (LingQs) for a language.

```bash
lingq get words ja
```

**Arguments:**
- `language_code`: Language code to export words from

**Options:**
- `--status`: Filter by status (0=new, 1=recognized, 2=familiar, 3=learned, 4=known)

### `lingq get images`

Download images from lessons.

```bash
lingq get images en 129129
```

**Arguments:**
- `language_code`: Language code
- `course_id`: Course ID

## Post Commands

Upload content to LingQ.

### `lingq post`

Upload lessons with text and optional audio files.

```bash
lingq post en 129129 "texts/" -a "audios/" --pairing-strategy zip
```

**Arguments:**
- `language_code`: Target language code
- `course_id`: Target course ID
- `texts_path`: Path to directory containing text files

**Options:**
- `-a, --audios-path`: Path to directory containing audio files
- `-c, --collection-title`: Create new course with this title
- `--pairing-strategy`: How to match text and audio files:
    - `exact`: Exact filename match (default)
    - `fuzzy`: Fuzzy matching using Levenshtein distance
    - `zip`: Match files by alphabetical order
    - `zipsort`: Match using natural sorting

**Example with new course:**
```bash
lingq post ja -c "My Japanese Book" "chapters/" -a "audio/" --pairing-strategy zip
```

### `lingq postyt`

Upload a YouTube playlist to a course.

```bash
lingq postyt en 129129 "https://www.youtube.com/@channel"
```

**Arguments:**
- `language_code`: Target language code
- `course_id`: Target course ID (or use `-c` for new course)
- `url`: YouTube playlist or channel URL

**Options:**
- `-c, --collection-title`: Create new course with this title
- `--caption-language`: Language code for captions (defaults to target language)

**Features:**
- Automatically downloads captions if available
- Extracts audio from videos
- Creates lessons with synchronized text and audio

## Timestamp

Generate timestamps for lessons with audio.

### `lingq timestamp`

Automatically generate timestamps for a course.

```bash
lingq timestamp de 129129
```

**Arguments:**
- `language_code`: Language code
- `course_id`: Course ID

**Options:**
- `--lesson-ids`: Process specific lessons only (space-separated IDs)

**How it works:**
- Uses audio duration and text length to generate proportional timestamps
- Adds timestamps to lessons that don't have them
- Skips lessons that already have timestamps

## Patch Commands

Update existing content.

### `lingq patch audios`

Replace or add audio to existing lessons.

```bash
lingq patch audios en 129129 "new_audio/"
```

**Arguments:**
- `language_code`: Language code
- `course_id`: Course ID
- `audios_path`: Path to directory containing new audio files

**Options:**
- `--pairing-strategy`: Matching strategy (exact, fuzzy, zip, zipsort)

## Sort Commands

### `lingq sort`

Sort lessons in a course using various sorting strategies.

```bash
lingq sort en 129129 --sort-key natural
```

**Arguments:**
- `language_code`: Language code
- `course_id`: Course ID

**Options:**
- `--sort-key`: Sorting strategy:
    - `natural`: Natural sorting (handles numbers correctly)
    - `greek`: Greek alphabet order
    - `roman`: Roman numeral order
    - `versioned`: Version number sorting (e.g., 1.1, 1.2, 2.1)

## Resplit

### `lingq resplit`

Resplit Japanese lessons using updated tokenization.

```bash
lingq resplit ja 129129
```

**Arguments:**
- `language_code`: Must be `ja` (Japanese only)
- `course_id`: Course ID

**Use case:**
- Updates word segmentation in Japanese lessons
- Useful when LingQ updates their tokenization algorithm

## Markdown

### `lingq markdown`

Generate markdown documentation of your courses.

```bash
lingq markdown en ja --no-views
```

**Arguments:**
- `language_codes`: Space-separated list of language codes

**Options:**
- `--no-views`: Exclude view counts from generated markdown
- `--mine`: Only include courses you own
- `--shared`: Only include shared courses

**Output:**
- Creates markdown files in `etc/markdowns/` directory
- Includes course structure, lesson titles, and statistics

## Yomitan

### `lingq yomitan`

Create a Yomitan dictionary from exported LingQs.

```bash
lingq get words ja  # First export words
lingq yomitan ja
```

**Arguments:**
- `language_code`: Language code

**Requirements:**
- Must first run `lingq get words` to create the dump file
- Currently supports Japanese best

**Use case:**
- Import your LingQ vocabulary into the Yomitan browser extension
- Study with flashcards in your browser

## Show Commands

Display information about your library.

### `lingq show my`

Show all your collections in a language.

```bash
lingq show my en
```

**Arguments:**
- `language_code`: Language code

**Output:**
- Lists all your courses with IDs and titles
- Useful for finding course IDs

## Overview

### `lingq overview`

Generate a CSV overview of your entire library.

```bash
lingq overview
```

**Output:**
- Creates a CSV file with all courses across all languages
- Includes statistics like lesson count, word count, etc.

## Statistics

### `lingq stats`

Show reading statistics for a language.

```bash
lingq stats ja
```

**Arguments:**
- `language_code`: Language code

**Output:**
- Known words count
- Reading hours
- Lessons completed
- And more statistics

## Merge

### `lingq merge`

Merge multiple courses into one.

```bash
lingq merge en 129129 129130 129131 -t "Combined Course"
```

**Arguments:**
- `language_code`: Language code
- `course_ids`: Space-separated course IDs to merge

**Options:**
- `-t, --title`: Title for the merged course

## Reindex

### `lingq reindex`

Reindex lesson titles with automatic numbering.

```bash
lingq reindex en 129129
```

**Arguments:**
- `language_code`: Language code
- `course_id`: Course ID

**Use case:**
- Add consistent numbering to lesson titles
- Fix gaps in numbering after deleting lessons

## Replace

### `lingq replace`

Replace text in lessons using regex patterns.

```bash
lingq replace en 129129 "old_pattern" "new_text"
```

**Arguments:**
- `language_code`: Language code
- `course_id`: Course ID
- `pattern`: Regex pattern to find
- `replacement`: Text to replace with

**Use case:**
- Fix recurring typos across multiple lessons
- Update formatting consistently

## Next Steps

- [Learn common workflows](workflows.md)
- [Explore API reference](../api-reference/lingqhandler.md)
- [Read tutorials](../tutorials/uploading.md)
