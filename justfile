# For debugging:
# set -x LOGURU_LEVEL TRACE

# Ignore handler test
test *FLAGS:
  pytest --ignore=tests/test_lingq_handler.py {{FLAGS}}

# Format
fmt:
  ruff format
  ruff check --fix

# Lint
lint:
  mypy src

# Download youtube audio from URL
dl URL:
  yt-dlp -x --audio-format mp3 '{{URL}}'

# Forced alignment
fa *FLAGS:
  python3 etc/forced_alignment/forced_alignment.py {{FLAGS}}
