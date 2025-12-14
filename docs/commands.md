# Commands

## Tree

The command tree (made with [this](https://github.com/whwright/click-command-tree)):

```text
lingq             - Lingq command line scripts.
├── get           - Get commands.
│   ├── courses   - Get all courses for the given languages.
│   ├── images    - Get course images.
│   ├── lesson    - Get a lesson from a lesson id.
│   ├── lessons   - Get all lessons from a course id.
│   └── words     - Get all words (LingQs) for the given languages.
├── make          - Make commands.
│   ├── markdown  - Make markdown files for the given languages.
│   ├── overview  - Make a library overview.
│   └── yomitan   - Make a Yomitan dictionary from the result of 'lingq get words'.
├── merge         - Merge two courses.
├── patch         - Patch commands.
│   └── audios    - Patch a course audio.
├── post          - Upload lessons.
├── postyt        - Post a youtube playlist.
├── reindex       - Reindex course titles.
├── replace       - Replace words in a course.
├── resplit       - Resplit a course.
├── setup         - Create or update a config file with your LingQ API key.
├── show          - Show commands.
│   ├── course    - Show lessons in a language.
│   ├── my        - Show my collections in a language.
│   ├── stats     - Show stats.
│   └── status    - Show pending and refused lessons in a language.
├── sort          - Sort course lessons.
└── timestamp     - Add course timestamps.
```

::: mkdocs-click
    :module: lingq.cli
    :command: cli
    :prog_name: lingq
    :depth: 1
    :style: plain
