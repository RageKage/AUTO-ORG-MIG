from pathlib import Path
import shutil
import sys


def print_usage() -> None:
    print("Usage: python migrate_media_to_SSD.py <source_root> <destination_root>")
    print()
    print("Example:")
    print('  python migrate_media_to_SSD.py '
          '"/Users/fadel/Desktop/Pictures" '
          '"/Volumes/Portal/Pictures"')
    print()
    print("This script assumes:")
    print("- <source_root> is your organized master library on the Desktop.")
    print("- <destination_root> is the SSD copy (archive).")
    print("- Top-level folders named YYYY-MM are the months to sync.")
    print("- The script ONLY copies from source to destination. It never deletes.")


def is_month_folder(name: str) -> bool:
    """Return True if a folder name looks like YYYY-MM."""
    if len(name) != 7:
        return False
    if name[4] != "-":
        return False
    year, month = name[:4], name[5:]
    return year.isdigit() and month.isdigit()


def safe_copy(src, dst, *, follow_symlinks=True) -> None:
    """
    Copy a file from src to dst.

    Compatible with shutil.copytree(copy_function=...), which passes src/dst
    as strings plus an optional follow_symlinks keyword.

    Tries to preserve metadata, but falls back to a plain copy if the filesystem
    (like an external SSD formatted as exFAT) does not support macOS flags.
    """
    src_path = Path(src)
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(src_path, dst_path, follow_symlinks=follow_symlinks)
    except OSError as e:
        print(f"WARNING: copy2 failed for {src_path} -> {dst_path}: {e}. Retrying without metadata.")
        shutil.copyfile(src_path, dst_path)


def sync_month_folder(src_month: Path, dst_month: Path) -> tuple[int, int]:
    """
    Sync a single month folder from source to destination.

    Returns (copied_count, skipped_count).
    """
    copied = 0
    skipped = 0

    # If the whole month folder doesn't exist on SSD yet, we can copy it in one go.
    if not dst_month.exists():
        print(f"-> Month '{src_month.name}' is new. Copying entire folder...")
        # copytree with dirs_exist_ok=False so we don't overwrite a real folder by accident
        shutil.copytree(src_month, dst_month, copy_function=safe_copy, dirs_exist_ok=False)
        # We don't know exact file count without walking, but that's okay for now.
        # Optionally, we can count after copy:
        for f in dst_month.rglob("*"):
            if f.is_file():
                copied += 1
        return copied, skipped

    # If the month already exists, walk files and only copy the ones that are missing.
    print(f"-> Month '{src_month.name}' exists on SSD. Copying only new files...")
    for src_file in src_month.rglob("*"):
        if not src_file.is_file():
            continue

        rel = src_file.relative_to(src_month)
        dst_file = dst_month / rel

        if dst_file.exists():
            skipped += 1
            # Uncomment if you want to see every skip:
            # print(f"SKIP    : {src_file} (already on SSD)")
            continue

        safe_copy(src_file, dst_file)
        copied += 1
        print(f"COPIED  : {src_file} -> {dst_file}")

    return copied, skipped


def main() -> None:
    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments.\n")
        print_usage()
        sys.exit(1)

    source_root = Path(sys.argv[1]).expanduser().resolve()
    destination_root = Path(sys.argv[2]).expanduser().resolve()

    if not source_root.exists() or not source_root.is_dir():
        print(f"Error: Source root '{source_root}' does not exist or is not a directory.")
        sys.exit(1)

    if not destination_root.exists() or not destination_root.is_dir():
        print(f"Error: Destination root '{destination_root}' does not exist or is not a directory.")
        sys.exit(1)

    print(f"Source (master):      {source_root}")
    print(f"Destination (SSD):    {destination_root}")
    print()

    # Identify top-level month folders to sync: YYYY-MM
    month_folders = [
        item for item in sorted(source_root.iterdir(), key=lambda p: p.name)
        if item.is_dir() and is_month_folder(item.name)
    ]

    if not month_folders:
        print("No YYYY-MM month folders found at the source root. Nothing to migrate.")
        sys.exit(0)

    print("Months to sync:")
    for m in month_folders:
        print(f"  - {m.name}")
    print()

    total_copied = 0
    total_skipped = 0

    for src_month in month_folders:
        dst_month = destination_root / src_month.name
        copied, skipped = sync_month_folder(src_month, dst_month)
        total_copied += copied
        total_skipped += skipped
        print(f"   Summary for {src_month.name}: copied {copied}, skipped {skipped}\n")

    print("=== Overall summary ===")
    print(f"Total files copied to SSD:   {total_copied}")
    print(f"Total files already on SSD:  {total_skipped}")
    print()
    print("You can run this script any time after organizing new months on the Desktop.")
    print("It will only copy new files and will never delete anything on either side.")


if __name__ == "__main__":
    main()
