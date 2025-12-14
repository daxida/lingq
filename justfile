# For debugging:
# set -x LOGURU_LEVEL TRACE # trace logs
# set -e LOGURU_LEVEL       # default

clean:
  rm -rf downloads

fmt:
  ruff format
  ruff check --fix

lint *args:
  mypy src {{args}}

# To deploy, mkdocs gh-deploy
docs:
  mkdocs serve

bump:
  uv version --bump patch

# Publish to PyPI. Requires setting UV_PUBLISH_TOKEN=
publish:
  uv build
  uv publish

# Ignores handler test. Run `pytest` to include it.
test *args:
  pytest --ignore=tests/test_lingq_handler.py {{args}}

test-handler:
  python3 tests/test_lingq_handler.py

alias t := test

