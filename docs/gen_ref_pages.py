"""Generate API reference pages automatically."""
from pathlib import Path
import mkdocs_gen_files

# Define the source directory
src = Path("src")

# Generate reference pages for Python modules
for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("api-reference/generated", doc_path)

    parts = tuple(module_path.parts)

    # Skip __pycache__ and other special directories
    if "__pycache__" in parts or parts[0].startswith("_"):
        continue

    # Skip __init__ files for cleaner structure
    if parts[-1] == "__init__":
        continue

    # Create the documentation path
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(parts)
        print(f"# {identifier}", file=fd)
        print(f"::: {identifier}", file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)
