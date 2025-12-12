# Common Workflows

This guide walks you through common workflows and use cases for the LingQ CLI.

## Uploading a Book with Audio

### Scenario
You have a book split into chapters as text files and corresponding audio files.

### Steps

1. **Organize your files**

   Create two directories:
   ```
   my-book/
   ├── texts/
   │   ├── 01 - Chapter One.txt
   │   ├── 02 - Chapter Two.txt
   │   └── 03 - Chapter Three.txt
   └── audios/
       ├── 01 - Chapter One.mp3
       ├── 02 - Chapter Two.mp3
       └── 03 - Chapter Three.mp3
   ```

2. **Create a new course and upload**

   ```bash
   lingq post ja -c "My Japanese Book" "my-book/texts" -a "my-book/audios" --pairing-strategy exact
   ```

   Or upload to an existing course:
   ```bash
   lingq post ja 129129 "my-book/texts" -a "my-book/audios" --pairing-strategy exact
   ```

3. **Generate timestamps**

   ```bash
   lingq timestamp ja 129129
   ```

### Pairing Strategies

Choose the right strategy for your files:

- **exact**: When text and audio have identical filenames (default)
- **fuzzy**: When filenames are similar but not identical
- **zip**: When files should match in alphabetical order
- **zipsort**: When files should match using natural sorting (handles numbers better)

**Example with fuzzy matching:**
```bash
lingq post en 129129 "texts/" -a "audios/" --pairing-strategy fuzzy
```

## Importing YouTube Content

### Scenario
You want to import videos from a YouTube channel into your course.

### Steps

1. **Get the channel or playlist URL**

   Examples:
   - Channel: `https://www.youtube.com/@channelname`
   - Playlist: `https://www.youtube.com/playlist?list=PLxxxxxx`

2. **Upload to a new course**

   ```bash
   lingq postyt de -c "German Videos" "https://www.youtube.com/@germanchannel"
   ```

3. **Specify caption language (if different)**

   ```bash
   lingq postyt en 129129 "https://www.youtube.com/@channel" --caption-language en-US
   ```

### What Happens
- Downloads video captions (if available)
- Extracts audio from videos
- Creates lessons with synchronized text and audio
- Names lessons based on video titles

!!! tip "Caption Availability"
    The tool will automatically download captions if they're available. If not, you'll need to provide transcripts separately.

## Exporting Vocabulary

### Scenario
You want to export your LingQs (vocabulary) for backup or external use.

### Steps

1. **Export all words**

   ```bash
   lingq get words ja
   ```

2. **Export by status**

   ```bash
   # Export only words you're learning (status 1-2)
   lingq get words ja --status 1
   lingq get words ja --status 2
   ```

3. **Create a Yomitan dictionary**

   ```bash
   lingq get words ja
   lingq yomitan ja
   ```

### Status Codes
- `0`: New (yellow)
- `1`: Recognized (light blue)
- `2`: Familiar (dark blue)
- `3`: Learned (light gray)
- `4`: Known (white)

## Organizing and Sorting Lessons

### Scenario
Your lessons are out of order or need consistent numbering.

### Sorting Lessons

```bash
# Natural sort (handles numbers correctly)
lingq sort en 129129 --sort-key natural

# Greek alphabet order
lingq sort el 129129 --sort-key greek

# Roman numerals
lingq sort la 129129 --sort-key roman

# Version numbers (1.1, 1.2, 2.1, etc.)
lingq sort en 129129 --sort-key versioned
```

### Reindexing Lessons

Add consistent numbering:

```bash
lingq reindex en 129129
```

This will rename lessons like:
```
Before:            After:
Chapter One     → 1. Chapter One
Introduction    → 2. Introduction
Final Chapter   → 3. Final Chapter
```

## Batch Processing Multiple Courses

### Scenario
You want to generate timestamps for all your German courses.

### Steps

1. **Get all your courses**

   ```bash
   lingq get courses de
   ```

   Note the course IDs.

2. **Process each course**

   ```bash
   lingq timestamp de 129129
   lingq timestamp de 129130
   lingq timestamp de 129131
   ```

### Script Example

For multiple operations, create a bash script:

```bash
#!/bin/bash

COURSES=(129129 129130 129131 129132)

for course in "${COURSES[@]}"; do
    echo "Processing course $course"
    lingq timestamp de $course
    lingq sort de $course --sort-key natural
done
```

## Updating Audio Files

### Scenario
You have better quality audio files and want to replace existing ones.

### Steps

1. **Organize new audio files**

   ```
   new-audio/
   ├── Lesson 1.mp3
   ├── Lesson 2.mp3
   └── Lesson 3.mp3
   ```

2. **Patch the course**

   ```bash
   lingq patch audios en 129129 "new-audio/" --pairing-strategy fuzzy
   ```

## Creating Documentation

### Scenario
You want to create markdown documentation of your courses for backup or sharing.

### Steps

1. **Generate markdown for all languages**

   ```bash
   lingq markdown en de ja el
   ```

2. **Generate for only your courses**

   ```bash
   lingq markdown en --mine
   ```

3. **Exclude view counts**

   ```bash
   lingq markdown en --no-views
   ```

### Output Location
Files are saved to `etc/markdowns/` organized by options:
- `markdown_all/` - All courses
- `markdown_mine/` - Only your courses
- `markdown_shared/` - Only shared courses
- `*_no_views/` - Versions without view counts

## Fixing Text Issues

### Scenario
You need to fix recurring formatting issues across multiple lessons.

### Using Replace

```bash
# Fix double spaces
lingq replace en 129129 "  " " "

# Remove unwanted characters
lingq replace ja 129129 "【.*?】" ""

# Update formatting
lingq replace de 129129 "(\d+)\." "$1)"
```

!!! warning "Regex Patterns"
    The pattern parameter uses regex. Test patterns carefully before applying to important courses.

## Resplitting Japanese Lessons

### Scenario
LingQ updated their Japanese tokenization and you want to update your lessons.

### Steps

```bash
lingq resplit ja 129129
```

This will:
- Re-tokenize all text in the course
- Update word boundaries
- Preserve your LingQs

!!! info "Japanese Only"
    This command only works for Japanese (ja) language code.

## Finding Course IDs

### Scenario
You need to find the ID of a course to use in commands.

!!! tip "Quick Method"
    The easiest way is: `lingq show my <language_code>` - this shows all your courses with their IDs.

### Methods

1. **Show all your courses** (recommended)

   ```bash
   lingq show my en
   ```
   
   **Output example:**
   ```
   Course ID: 129129 - My English Course
   Course ID: 129130 - Another Course
   ```

2. **Get all courses in a language**

   ```bash
   lingq get courses en
   ```
   
   This shows all courses (not just yours) and includes more details.

3. **From the LingQ website URL**

   When viewing a course on the LingQ website, the course ID is in the URL:
   ```
   https://www.lingq.com/en/learn/en/web/course/129129
                                              ^^^^^^
                                            Course ID
   ```

## Working with Specific Lessons

### Scenario
You want to timestamp only specific lessons in a course.

### Steps

```bash
# Timestamp specific lessons by ID
lingq timestamp en 129129 --lesson-ids 12345678 12345679 12345680
```

## Next Steps

- [Explore all commands](commands.md)
- [Read API reference](../api-reference/lingqhandler.md)
- [Check out tutorials](../tutorials/uploading.md)
