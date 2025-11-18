import os
import shutil
import hashlib
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
DUPLICATES_DIR_NAME = "_duplicates"  # where detected duplicates are moved
INBOX_DIR_NAME = "_inbox"            # drop new media here to be auto-organized

def has_gps_exif(path: Path) -> bool:
    """Return True if image file has GPS EXIF data."""
    if path.suffix.lower() not in IMAGE_EXTS:
        return False

    try:
        with Image.open(path) as img:
            exif = img._getexif()
            if not exif:
                return False

            gps_tag_id = EXIF_TAGS.get("GPSInfo")
            if gps_tag_id is None:
                return False

            gps_info = exif.get(gps_tag_id)
            return bool(gps_info)  # True if dict is not empty
    except Exception:
        # If anything fails, just say no GPS
        return False


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

def file_hash(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a SHA-256 hash of the file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def organize(root_folder: Path):
    """
    Walk through root_folder, find media files, and move them into a structure like:

        <root>/YYYY-MM/YYYY-MM-DD/jpeg/
        <root>/YYYY-MM/YYYY-MM-DD/raw/
        <root>/YYYY-MM/YYYY-MM-DD/geo/jpeg/
        <root>/YYYY-MM/YYYY-MM-DD/geo/raw/
        <root>/YYYY-MM/YYYY-MM-DD/video/

    This keeps things grouped first by month, then by shooting day, and then by
    whether the file has GPS data (in the geo subfolder) and whether it is RAW/JPEG
    or video. A special "_inbox" folder is created at the root where you can drop new files to be organized, and any exact duplicates (by file content hash) are moved into a "_duplicates" folder for later review.
    """
    root_folder = root_folder.expanduser().resolve()
    print(f"Organizing files under: {root_folder}")

    # Ensure an inbox folder exists for new, unsorted media
    inbox_folder = root_folder / INBOX_DIR_NAME
    inbox_folder.mkdir(parents=True, exist_ok=True)

    # Track seen file hashes to detect exact duplicates
    seen_hashes = {}
    duplicates_root = root_folder / DUPLICATES_DIR_NAME

    for path in root_folder.rglob("*"):
        if not path.is_file():
            continue

        # Skip anything already in the duplicates folder
        try:
            path.relative_to(duplicates_root)
            # If this doesn't raise, the file is under _duplicates
            continue
        except ValueError:
            pass

        # Skip hidden files
        if path.name.startswith("."):
            continue

        ext = path.suffix.lower()
        if ext not in MEDIA_EXTS:
            continue

        # Check for duplicates by file content hash
        h = file_hash(path)
        if h in seen_hashes:
            target_dup = duplicates_root / path.name
            print(f"Duplicate detected (same as {seen_hashes[h]}): {path} -> {target_dup}  [duplicate]")
            safe_move(path, target_dup)
            continue
        else:
            seen_hashes[h] = path

        # Determine month and day folders from capture datetime
        dt = get_capture_datetime(path)
        month_folder_name = f"{dt.year:04d}-{dt.month:02d}"
        day_folder_name = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"

        # Videos: we don't care about geo/no-geo, just group by day
        if ext in VIDEO_EXTS:
            target_dir = root_folder / month_folder_name / day_folder_name / "video"
            label = f"{day_folder_name}/video"
        else:
            # Photos: only create a special folder for geo-tagged files.
            is_geo = has_gps_exif(path)

            if ext in RAW_EXTS:
                photo_type = "raw"
            else:
                photo_type = "jpeg"

            if is_geo:
                # Geo-tagged images go under geo/jpeg or geo/raw
                target_dir = root_folder / month_folder_name / day_folder_name / "geo" / photo_type
                label = f"{day_folder_name}/geo/{photo_type}"
            else:
                # Non-geo images go directly under jpeg/ or raw/ for that day
                target_dir = root_folder / month_folder_name / day_folder_name / photo_type
                label = f"{day_folder_name}/{photo_type}"

        target_path = target_dir / path.name

        # If file is already in the correct folder, skip it (makes script safe to re-run)
        if path.parent == target_dir:
            continue

        print(f"Moving: {path} -> {target_path}  [{label}]")
        safe_move(path, target_path)

    # Clean up old "no-geo" folders from the previous layout if they no longer contain files
    for dirpath in root_folder.rglob("no-geo"):
        if not dirpath.is_dir():
            continue
        has_files = False
        for p in dirpath.rglob("*"):
            if p.is_file():
                has_files = True
                break
        if not has_files:
            import shutil as _shutil
            print(f"Removing empty folder tree: {dirpath}")
            _shutil.rmtree(dirpath)


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