# Managing Courses

This tutorial covers course management operations like sorting, merging, updating, and organizing lessons.

## Sorting Lessons

### Why Sort?

Lessons can become unordered when:
- Uploading in multiple batches
- Manual reordering on the website
- Importing from different sources

### Available Sort Keys

#### Natural Sort

Best for most cases with numbers:

```bash
lingq sort en 129129 --sort-key natural
```

**Handles:**
- `Lesson 1`, `Lesson 2`, ..., `Lesson 10`, `Lesson 11`
- `Chapter1`, `Chapter2`, ..., `Chapter10`
- Mixed text and numbers

#### Greek Sort

For Greek alphabet ordering:

```bash
lingq sort el 129129 --sort-key greek
```

**Orders by:**
- Alpha (Α), Beta (Β), Gamma (Γ), Delta (Δ), etc.
- Handles both uppercase and lowercase
- Accent-insensitive

#### Roman Numeral Sort

For Roman numerals:

```bash
lingq sort la 129129 --sort-key roman
```

**Handles:**
- I, II, III, IV, V, etc.
- Mixed with text: `Chapter I`, `Chapter II`

#### Versioned Sort

For version-style numbering:

```bash
lingq sort en 129129 --sort-key versioned
```

**Handles:**
- `1.1`, `1.2`, `1.10`, `2.1`
- `Chapter 1.1`, `Chapter 1.2`

## Reindexing Lessons

### Adding Numbers to Titles

Automatically number lessons:

```bash
lingq reindex en 129129
```

**Before:**
```
Introduction
First Chapter
Second Chapter
Conclusion
```

**After:**
```
1. Introduction
2. First Chapter
3. Second Chapter
4. Conclusion
```

### Use Cases

- Adding consistent numbering to imported content
- Fixing gaps after deleting lessons
- Preparing courses for export

## Merging Courses

### Basic Merge

Combine multiple courses into one:

```bash
lingq merge en 129129 129130 129131 -t "Complete Series"
```

### What Happens

1. Creates a new course titled "Complete Series"
2. Copies all lessons from source courses in order
3. Preserves audio and text
4. Original courses remain unchanged

### Use Cases

- Combining a book series
- Consolidating related content
- Creating compilation courses

### Workflow Example

```bash
# Step 1: Merge courses
lingq merge ja 129129 129130 129131 -t "Complete Textbook"

# Step 2: Get the new course ID from output
# (e.g., "Created collection ID: 129999")

# Step 3: Sort the merged content
lingq sort ja 129999 --sort-key natural

# Step 4: Reindex with numbers
lingq reindex ja 129999
```

## Updating Audio

### Replace Existing Audio

Update audio files in a course:

```bash
lingq patch audios en 129129 "new-audio/" --pairing-strategy fuzzy
```

### When to Update

- Improved audio quality available
- Fixed pronunciation errors
- Better recording conditions
- Different speaker/voice

### File Preparation

```
new-audio/
├── Lesson 1.mp3  (better quality)
├── Lesson 2.mp3  (better quality)
└── Lesson 3.mp3  (better quality)
```

### After Patching

Regenerate timestamps if needed:

```bash
lingq timestamp en 129129
```

## Deleting Lessons

### Individual Lessons

Currently requires direct API access. Alternative: use LingQ website.

### Entire Course

Use the website or contact support for bulk deletion.

## Text Replacement

### Find and Replace

Replace text across all lessons in a course:

```bash
lingq replace en 129129 "old text" "new text"
```

### Regex Patterns

Use regex for complex replacements:

```bash
# Remove text in brackets
lingq replace en 129129 "\[.*?\]" ""

# Fix numbering format
lingq replace en 129129 "Chapter (\d+)" "Ch. $1"

# Clean up spaces
lingq replace en 129129 "\s+" " "
```

### Common Use Cases

**Remove annotations:**
```bash
lingq replace ja 129129 "【.*?】" ""
```

**Fix quotation marks:**
```bash
lingq replace en 129129 '"' '"'
lingq replace en 129129 '"' '"'
```

**Update formatting:**
```bash
lingq replace de 129129 "(\d+)\." "$1)"
```

## Resplitting (Japanese Only)

### What is Resplitting?

Updates word segmentation in Japanese lessons:

```bash
lingq resplit ja 129129
```

### When to Use

- After LingQ updates tokenization
- Improving word boundaries
- Better LingQ creation accuracy

### What It Does

1. Re-tokenizes all text in the course
2. Updates word boundaries
3. Preserves your existing LingQs
4. Updates lesson metadata

!!! warning "Japanese Only"
    This feature only works with Japanese (`ja`) language code.

## Generating Timestamps

### Basic Usage

Create timestamps for lessons with audio:

```bash
lingq timestamp de 129129
```

### How It Works

1. Calculates proportional timestamps based on:
   - Audio duration
   - Text length
   - Word count
2. Assigns timestamps to sentences
3. Skips lessons that already have timestamps

### Specific Lessons

Process only certain lessons:

```bash
lingq timestamp en 129129 --lesson-ids 12345678 12345679 12345680
```

### Best Practices

- Run after uploading new lessons with audio
- Re-run if you update audio files
- Check first few lessons to verify accuracy

## Course Statistics

### View Statistics

Check course progress:

```bash
lingq stats ja
```

**Shows:**
- Known words
- Reading hours  
- Lessons completed
- LingQs created
- And more

### Library Overview

Generate CSV of all courses:

```bash
lingq overview
```

**Output includes:**
- Course titles and IDs
- Lesson counts
- Word counts
- Status information

## Organizing Workflow

### Recommended Process

1. **Initial Upload**
   ```bash
   lingq post ja -c "My Course" "texts/" -a "audios/" --pairing-strategy zip
   ```

2. **Generate Timestamps**
   ```bash
   lingq timestamp ja 129999
   ```

3. **Sort Lessons**
   ```bash
   lingq sort ja 129999 --sort-key natural
   ```

4. **Add Numbering**
   ```bash
   lingq reindex ja 129999
   ```

5. **Verify**
   - Check on LingQ website
   - Test first lesson
   - Confirm audio syncs correctly

## Best Practices

### Before Making Changes

!!! tip "Safety First"
    1. **Test on a copy** if possible
    2. **Document course IDs** before merging
    3. **Backup exports** using `lingq get lessons`
    4. **Start small** - test with one lesson

### Regular Maintenance

- Sort lessons after new uploads
- Update timestamps when changing audio
- Regenerate documentation periodically
- Export vocabulary regularly

### Quality Checks

After bulk operations:

1. **Check lesson count**
   ```bash
   lingq get lessons ja 129129
   ```

2. **Verify sorting**
   - View course on website
   - Check first and last lessons

3. **Test audio sync**
   - Open a few lessons
   - Verify timestamps work

## Troubleshooting

### Sort Not Working

If lessons don't sort correctly:

1. **Check lesson titles**
   ```bash
   lingq get lessons en 129129
   ```

2. **Try different sort key**
   ```bash
   lingq sort en 129129 --sort-key natural
   ```

3. **Manual reindex first**
   ```bash
   lingq reindex en 129129
   lingq sort en 129129 --sort-key natural
   ```

### Timestamp Issues

If timestamps are inaccurate:

1. **Check audio files** - ensure correct duration
2. **Verify text content** - ensure proper sentence breaks
3. **Regenerate** - delete and recreate timestamps

### Merge Problems

If merge fails:

1. **Verify source courses exist**
   ```bash
   lingq show my en
   ```

2. **Check permissions** - ensure you own/can access courses
3. **Try smaller batches** - merge 2 courses at a time

## Next Steps

- [Learn about uploading content](uploading.md)
- [Explore all commands](../user-guide/commands.md)
- [Read common workflows](../user-guide/workflows.md)
