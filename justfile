# For debugging:
# set -x LOGURU_LEVEL TRACE

clean:
  rm -rf downloads

# Ignores handler test. Run `pytest` to include it.
test *args:
  pytest --ignore=tests/test_lingq_handler.py {{args}}

test-handler:
  python3 tests/test_lingq_handler.py

alias t := test

# Format
fmt:
  ruff format
  ruff check --fix

# Lint
lint *args:
  mypy src {{args}}

