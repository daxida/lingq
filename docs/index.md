# CLI

This documentation focuses on **how the CLI is structured** and **how to understand the arguments it uses**, since many commands use the same identifiers.

See [commands](commands.md) for more information.

---

### `LANG`

A **single language code**: `en` (English), `pt` (Portuguese), `de` (German), etc.

```console
$ # pt
$ lingq show my pt -c
$ lingq get lesson pt 6001558
```

---

### `LANGS`

A **list of space-separated language codes**.

```console
$ # pt de
$ lingq make markdown pt de
$ lingq make markdown pt
$ lingq make markdown
```

!!! note
    If no languages are provided, default to **all languages in your account**.

---

### `COURSE_ID`

A numeric identifier for a **course**.

The easiest way to obtain a `COURSE_ID` is by opening it in the browser, then inspecting the last number of the url.

```text
URL:       https://www.lingq.com/en/learn/de/web/library/course/537808
COURSE_ID: 537808
```

Alternatively, you can get the `COURSE_ID` of your courses in a language, by running the following command:

```console
$ lingq show my pt -c
01:  746625 Blecaute
02:  780316 Imports - Youtube
...
```

---

### `LESSON_ID`

A numeric identifier for a **lesson**.

The easiest way to obtain a `LESSON_ID` is by opening it in the browser, then inspecting the last number of the url.

```text
URL:       https://www.lingq.com/en/learn/pt/web/reader/6001558
COURSE_ID: 6001558
```

Alternatively, you can get the `LESSON_ID` of your lessons in a course, by running the following command:

```console
$ lingq show course pt 780316 -c
01: 6001558 Shingo Tamagawa - Three Minutes, Three Years: Making Puparia
02: 6009955 Toshihiro Nagoshi, the Yakuza years - Archipel Caravan
03: 6555358 Saving a ramen chain during the pandemic - Staying Afloat
...
```

---


