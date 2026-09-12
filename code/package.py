"""Build the submission archive without including local secrets or caches."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "code.zip"
# Keep the archive scope explicit; root .env is never an allowed input.
ARCHIVE_ROOTS = ("code", "dataset", "evaluation", "README.md", "problem_statement.md", ".env.example")


def excluded(relative: Path) -> bool:
    if relative.name == ".env":
        return True
    if relative.name.startswith(".env.") and relative.name != ".env.example":
        return True
    if any(part in {".git", "__pycache__"} for part in relative.parts):
        return True
    if relative.suffix in {".pyc", ".pyo", ".tmp"}:
        return True
    return False


def archive_files() -> list[tuple[Path, Path]]:
    result: list[tuple[Path, Path]] = []
    for root_name in ARCHIVE_ROOTS:
        source = ROOT / root_name
        if not source.exists():
            continue
        if source.is_file():
            relative = source.relative_to(ROOT)
            if not excluded(relative):
                result.append((source, relative))
            continue
        for path in sorted(source.rglob("*")):
            if path.is_file():
                relative = path.relative_to(ROOT)
                if not excluded(relative):
                    result.append((path, relative))
    return result


def build_archive(destination: Path = DEFAULT_OUTPUT) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for path, relative in archive_files():
            archive.write(path, relative.as_posix())
    with ZipFile(destination) as archive:
        names = set(archive.namelist())
    if any(name == ".env" or name.endswith("/.env") for name in names):
        raise AssertionError("secret .env entered the archive")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_archive(args.destination)
    print(f"created {args.destination}")


if __name__ == "__main__":
    main()
