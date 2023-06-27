# LingQ

Scripts for basic interactions with LingQ's (awful) API

## How to get the API token

Go to https://www.lingq.com/en/accounts/apikey/

## Description

- **Markdown** (create a markdown of courses)

- **Get** (download lessons): 
  - get_lessons: download audio/text from a lesson.
  - get_courses: download audio/text from all the lessons in a language. (unfinished)

- **Post** (upload lessons): Upload text or text with audio. Also allow for going over the 6k words by sending a patch request (although now that the limit went from 2k to 6k I wouldn't recommend it).

- **Patch** (fix or complete lessons): Allows to bulk upload audio to a collection with only text. Can also be used to overwrite text and to bypass the word limit. (unfinished)

- **Scripts**:
  - Processing text: A bunch of ad-hoc scripts.
  - Processing audio: uses https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04 to split the timestamps if the original video didn't have them and you wanted to do it manually.
  - Stats: periodically export LingQ stats https://www.lingq.com/es/community/forum/support-feedback-forum/how-do-you-export-statistics-i

## Others

- A miniminalist script to upload content to LingQ. May not be up to date: https://github.com/paulywill/lingq_upload
- For splitting downloaded audio from youtube: https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04
