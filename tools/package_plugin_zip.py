import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "astrbot_plugin_meme_studio"
OUTPUT = ROOT.parent / f"{PACKAGE_NAME}_install.zip"

EXCLUDE_DIRS = {
    ".git",
    ".meme_studio_sessions",
    ".meme_studio_previews",
    "__pycache__",
    "build",
    "dist",
    "docs",
    "exports",
    "tests",
}
EXCLUDE_FILES = {
    ".gitignore",
    ".gitattributes",
    "MemeStudio.exe",
}
EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".spec",
}


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in relative.parts):
        return False
    if path.name in EXCLUDE_FILES:
        return False
    return path.suffix not in EXCLUDE_SUFFIXES


def archive_name(path: Path) -> str:
    relative = path.relative_to(ROOT)
    return PurePosixPath(PACKAGE_NAME, *relative.parts).as_posix()


def main() -> None:
    if OUTPUT.exists():
        OUTPUT.unlink()

    files = [path for path in ROOT.rglob("*") if path.is_file() and should_include(path)]
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(f"{PACKAGE_NAME}/", "")
        for path in sorted(files):
            archive.write(path, archive_name(path))

    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"created {OUTPUT} ({size_mb:.2f} MB, {len(files)} files)")


if __name__ == "__main__":
    main()
