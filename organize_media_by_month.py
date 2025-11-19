import os
import shutil
from pathlib import Path
from datetime import datetime

from PIL import Image, ExifTags

# Map EXIF tag names to their numeric ids once
EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}

# File types we treat as "images" we try to read EXIF from
IMAGE_EXTS = {".jpg", ".jpeg", ".jpe", ".tif", ".tiff", ".heic", ".png"}

# RAW photo formats (will be placed in a separate "raw" folder)
RAW_EXTS = {".raf", ".cr2", ".nef", ".dng", ".arw", ".rw2", ".orf"}

# Video formats (will be placed in a separate "video" folder)
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mts", ".m2ts"}

# All media we want to move (you can add more extensions here)
MEDIA_EXTS = IMAGE_EXTS.union(RAW_EXTS).union(VIDEO_EXTS)

# Special folders at the root of the library
INBOX_DIR_NAME = "_inbox"            # drop new media here to be auto-organized

def get_capture_datetime(path: Path) -> datetime:
    """
    Try to get DateTimeOriginal from EXIF for images.
    If not available (or not an image), fall back to file's modified time.
    """
    if path.suffix.lower() in IMAGE_EXTS:
        try:
            with Image.open(path) as img:
                exif = img._getexif()
                if exif:
                    dto_tag = EXIF_TAGS.get("DateTimeOriginal")
                    if dto_tag in exif:
                        raw = exif[dto_tag]  # e.g. '2025:01:15 14:23:11'
                        # EXIF format: YYYY:MM:DD HH:MM:SS
                        return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass

    # Fallback: modification time
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts)


def safe_move(src: Path, dst: Path):
    """
    Move file from src to dst, avoiding overwriting.
    If dst exists, append _1, _2, etc. to filename.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)

    base = dst.stem
    ext = dst.suffix
    candidate = dst
    counter = 1

    while candidate.exists():
        candidate = dst.with_name(f"{base}_{counter}{ext}")
        counter += 1

    shutil.move(str(src), str(candidate))

def organize(root_folder: Path):
    """
    Walk through the `_inbox` folder under root_folder, find media files, and move
    them into a structure like:

        <root>/YYYY-MM/YYYY-MM-DD/jpeg/
        <root>/YYYY-MM/YYYY-MM-DD/raw/
        <root>/YYYY-MM/YYYY-MM-DD/video/

    This keeps things grouped first by month, then by shooting day, and separates
    photos (JPEG/PNG vs RAW) from video files. The `_inbox` folder acts as a
    drop box: you can put new media there and run this script to sort everything.
    """
    root_folder = root_folder.expanduser().resolve()
    print(f"Organizing files under: {root_folder}")

    # Ensure an inbox folder exists for new, unsorted media
    inbox_folder = root_folder / INBOX_DIR_NAME
    inbox_folder.mkdir(parents=True, exist_ok=True)

    # Only organize files that are currently in _inbox (or inside it)
    for path in inbox_folder.rglob("*"):
        if not path.is_file():
            continue

        # Skip hidden files
        if path.name.startswith("."):
            continue

        ext = path.suffix.lower()
        if ext not in MEDIA_EXTS:
            continue

        # Determine month and day folders from capture datetime
        dt = get_capture_datetime(path)
        month_folder_name = f"{dt.year:04d}-{dt.month:02d}"
        day_folder_name = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"

        # Decide subfolder based on file type
        if ext in VIDEO_EXTS:
            target_dir = root_folder / month_folder_name / day_folder_name / "video"
            label = f"{day_folder_name}/video"
        elif ext in RAW_EXTS:
            target_dir = root_folder / month_folder_name / day_folder_name / "raw"
            label = f"{day_folder_name}/raw"
        else:
            # Regular image (JPEG/PNG/etc.)
            target_dir = root_folder / month_folder_name / day_folder_name / "jpeg"
            label = f"{day_folder_name}/jpeg"

        target_path = target_dir / path.name

        # If file is already in the correct folder, skip it (makes script safe to re-run)
        if path.parent == target_dir:
            continue

        print(f"Moving: {path} -> {target_path}  [{label}]")
        safe_move(path, target_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 organize_media_by_month.py /path/to/your/folder")
        raise SystemExit(1)

    root = Path(sys.argv[1])
    if not root.exists() or not root.is_dir():
        print(f"Error: {root} is not a folder.")
        raise SystemExit(1)

    organize(root)
    print("Done.")