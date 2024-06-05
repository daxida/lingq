import re


def fix_youtube_newlines(text: str) -> str:
    # Remove newlines if not after "。"
    text = re.sub(r'(?<!。)\n', '', text)

    # Add newlines after "。" if needed
    text = re.sub(r'。(?!\n)', '。\n', text)

    return text