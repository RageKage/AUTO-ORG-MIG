from pathlib import Path
import shutil
import sys

def print_usage():
    print("Usage: python migrate_media_to_SSD.py <source_root> <destination_root>")
    print("Example:")
    print("  python migrate_media_to_SSD.py /Users/fadel/Desktop/Pictures /Volumes/Portal/Pictures")

def main():
    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments.")
        print_usage()
        sys.exit(1)

    source_root = Path(sys.argv[1])
    destination_root = Path(sys.argv[2])

    if not source_root.exists() or not source_root.is_dir():
        print(f"Error: Source root '{source_root}' does not exist or is not a directory.")
        sys.exit(1)

    if not destination_root.exists() or not destination_root.is_dir():
        print(f"Error: Destination root '{destination_root}' does not exist or is not a directory.")
        sys.exit(1)

    # Identify folders to move: top-level folders named like YYYY-MM and the _duplicates folder
    to_move = []
    for item in source_root.iterdir():
        if item.is_dir():
            if item.name == "_duplicates":
                to_move.append(item)
            elif len(item.name) == 7 and item.name[4] == '-' and item.name[:4].isdigit() and item.name[5:7].isdigit():
                to_move.append(item)

    if not to_move:
        print("Nothing to move from source root.")
        sys.exit(0)

    for folder in to_move:
        dest_path = destination_root / folder.name
        print(f"Moving '{folder}' to '{dest_path}'")
        if dest_path.exists():
            print(f"Warning: Destination folder '{dest_path}' already exists. Skipping move of '{folder}'.")
            continue
        shutil.move(str(folder), str(dest_path))

if __name__ == "__main__":
    main()
