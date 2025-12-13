# Uploading Content to LingQ

This tutorial covers different methods for uploading content to your LingQ courses.

## Prerequisites

- LingQ CLI installed and configured
- API key set up (`lingq setup yourApiKey`)
- Text files prepared (UTF-8 encoded)
- Optional: Audio files in supported formats (MP3, M4A, etc.)

## Method 1: Text Only

### Simple Upload

Upload plain text files without audio:

```bash
lingq post en 129129 "path/to/texts/"
```

This will:
1. Read all text files from the directory
2. Create one lesson per text file
3. Use the filename as the lesson title

### Example Structure

```
my-texts/
├── Chapter 1.txt
├── Chapter 2.txt
└── Chapter 3.txt
```

## Method 2: Text with Audio (Exact Matching)

### When to Use
Use exact matching when your text and audio files have identical names.

### File Structure

```
my-content/
├── texts/
│   ├── Lesson 1.txt
│   ├── Lesson 2.txt
│   └── Lesson 3.txt
└── audios/
    ├── Lesson 1.mp3
    ├── Lesson 2.mp3
    └── Lesson 3.mp3
```

### Command

```bash
lingq post en 129129 "my-content/texts" -a "my-content/audios" --pairing-strategy exact
```

## Method 3: Text with Audio (Fuzzy Matching)

### When to Use
Use fuzzy matching when filenames are similar but not identical.

### File Structure

```
my-content/
├── texts/
│   ├── 01 - First Lesson.txt
│   ├── 02 - Second Lesson.txt
│   └── 03 - Third Lesson.txt
└── audios/
    ├── first_lesson.mp3
    ├── second_lesson.mp3
    └── third_lesson.mp3
```

### Command

```bash
lingq post en 129129 "my-content/texts" -a "my-content/audios" --pairing-strategy fuzzy
```

### How It Works
- Uses Levenshtein distance to match similar filenames
- Ignores case and special characters
- Matches best candidates automatically

## Method 4: Zip/Zipsort Pairing

### When to Use
Use when text and audio files don't have matching names but should be paired in order.

### File Structure

```
book/
├── texts/
│   ├── chapter_01.txt
│   ├── chapter_02.txt
│   └── chapter_03.txt
└── audios/
    ├── audio_track_1.mp3
    ├── audio_track_2.mp3
    └── audio_track_3.mp3
```

### Commands

```bash
# Zip: Alphabetical order
lingq post en 129129 "book/texts" -a "book/audios" --pairing-strategy zip

# Zipsort: Natural sorting (better for numbers)
lingq post en 129129 "book/texts" -a "book/audios" --pairing-strategy zipsort
```

### Difference: Zip vs Zipsort

**Zip** (alphabetical):
```
file1.txt   → 1, 10, 11, 2, 3
file2.txt
...
```

**Zipsort** (natural):
```
file1.txt   → 1, 2, 3, 10, 11
file2.txt
...
```

## Method 5: Creating a New Course

### Command

```bash
lingq post ja -c "My New Course" "texts/" -a "audios/" --pairing-strategy zip
```

### What Happens
1. Creates a new course with the title "My New Course"
2. Uploads all lessons to the new course
3. Returns the new course ID

### Getting the Course ID

The command output will show:
```
Created collection: My New Course (ID: 129999)
Uploading lessons...
```

Save this ID for future operations.

## Post-Upload Tasks

### Generate Timestamps

After uploading with audio:

```bash
lingq timestamp en 129129
```

### Sort Lessons

Organize lessons in order:

```bash
lingq sort en 129129 --sort-key natural
```

### Reindex Titles

Add consistent numbering:

```bash
lingq reindex en 129129
```

## Best Practices

### File Naming

!!! tip "Good Naming Conventions"
    - Use consistent naming patterns
    - Include leading zeros for numbers: `01`, `02`, ... `10`
    - Avoid special characters: `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`
    - Keep names descriptive but concise

**Good examples:**
```
01_introduction.txt
02_chapter_one.txt
03_chapter_two.txt
```

**Avoid:**
```
intro.txt
1.txt
ChapterTwo?.txt
```

### Text File Format

!!! info "Text File Requirements"
    - Use UTF-8 encoding
    - Plain text format (.txt)
    - One file per lesson
    - Reasonable length (LingQ has limits per lesson)

### Audio File Format

!!! info "Supported Audio Formats"
    - MP3 (recommended)
    - M4A
    - WAV
    - OGG
    
    Keep file sizes reasonable for upload speed.

### Testing First

!!! warning "Test with Small Batches"
    Before uploading an entire book:
    1. Test with 2-3 chapters first
    2. Verify pairing works correctly
    3. Check text and audio alignment
    4. Then proceed with full upload

## Troubleshooting

### Pairing Failures

If text and audio don't pair correctly:

1. **Check file counts**
   ```bash
   ls texts/ | wc -l
   ls audios/ | wc -l
   ```
   Counts should match.

2. **Try different strategies**
   - Start with `exact`
   - If that fails, try `fuzzy`
   - Last resort: `zip` or `zipsort`

3. **Check filenames**
   ```bash
   ls texts/
   ls audios/
   ```
   Look for obvious differences.

### Upload Errors

If upload fails:

1. **Check API key**
   ```bash
   lingq show my en
   ```

2. **Verify course ID**
   - Check the ID exists
   - Ensure you have permission to upload

3. **Check file encoding**
   - Ensure UTF-8 encoding
   - Remove BOM if present

### Rate Limiting

For large uploads:

- The tool includes retry logic
- Wait between attempts if you hit rate limits
- Consider splitting very large uploads

## Advanced: Batch Uploading

### Multiple Courses Script

```bash
#!/bin/bash

BOOKS=(
    "japanese/book1:129129"
    "japanese/book2:129130"
    "japanese/book3:129131"
)

for book in "${BOOKS[@]}"; do
    path="${book%%:*}"
    course="${book##*:}"
    
    echo "Uploading $path to course $course"
    lingq post ja $course "$path/texts" -a "$path/audios" --pairing-strategy zip
    lingq timestamp ja $course
    lingq sort ja $course --sort-key natural
done
```

## Next Steps

- [Learn about managing courses](managing.md)
- [Explore all commands](../user-guide/commands.md)
- [Read common workflows](../user-guide/workflows.md)
