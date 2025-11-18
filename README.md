This folder contains two small Python tools that keep your photo/video library clean:

- `organize_media_by_month.py` — walks a library, sorts files into a consistent date-based structure, and finds duplicates.
- `migrate_media_to_SSD.py` — moves the organized months (and `_duplicates`) from your main drive to an external SSD.

---

## 1. Requirements

- Python 3 installed (macOS already has it, but `python3` must work in Terminal).
- The Pillow library for reading EXIF data:

  ```bash
  pip3 install pillow
  ```

---

## 2. Folder layout

When you run `organize_media_by_month.py` on a root folder (for example `/Users/fadel/Desktop/Pictures`), it will:

- Create or update this structure:

  ```
  Pictures/
    2025-07/
      2025-07-28/
        jpeg/
        raw/
        geo/
          jpeg/
          raw/
        video/
    _duplicates/
    _inbox/
  ```

### What each folder means

- `YYYY-MM/` — one folder per month.
- `YYYY-MM-DD/` — one folder per shooting day inside each month.
- `jpeg/` — JPEG/PNG images without GPS data.
- `raw/` — RAW files (`.raf`, `.cr2`, `.nef`, `.dng`, `.arw`, `.rw2`, `.orf`) without GPS data.
- `geo/jpeg/` and `geo/raw/` — images that *do* have GPS EXIF data.
- `video/` — video files (`.mp4`, `.mov`, `.m4v`, `.avi`, `.mts`, `.m2ts`) for that day.
- `_duplicates/` — exact duplicates (detected by SHA‑256 hash). Safe place to review and delete later.
- `_inbox/` — a drop box. Anything you put here that has a supported extension will be organized on the next run.

---

## 3. What gets organized?

The organizer only touches files with these extensions:

- Images: `.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`, `.heic`, `.png`
- RAW: `.raf`, `.cr2`, `.nef`, `.dng`, `.arw`, `.rw2`, `.orf`
- Video: `.mp4`, `.mov`, `.m4v`, `.avi`, `.mts`, `.m2ts`

Files like `.log`, `.txt`, `.psd`, etc. are ignored and left where they are.

Anything with a supported extension that you drop into `_inbox/` will be picked up, dated by its EXIF capture time (or file modified time as a fallback), and moved into the correct month/day folder.

---

## 4. Running the organizer

From this folder (`Org`) in Terminal:

```bash
python3 organize_media_by_month.py "/Users/fadel/Desktop/Pictures"
```

You can safely run this multiple times. The script:

- Skips files already in the correct target folder.
- Detects exact duplicates by content hash and moves them to `_duplicates/`.
- Cleans up any old empty `no-geo` folders from the previous layout.

Recommended workflow:

1. Import or copy new media into `Pictures/_inbox/`.
2. Run the organizer command above.
3. Review `_duplicates/` occasionally and delete what you don’t need.

---

## 5. Migrating to the SSD

Once your `Pictures` folder is organized, you can move the month folders and `_duplicates` to your external SSD (e.g., the `Portal` drive):

```bash
python3 migrate_media_to_SSD.py "/Users/fadel/Desktop/Pictures" "/Volumes/Portal/Pictures"
```

This script:

- Moves all top‑level month folders (`YYYY-MM`) and `_duplicates` from the source root to the destination root.
- Leaves `_inbox` and any other non‑month folders in place on your main drive.
- Prints each move so you can see what happened.

You can run `organize_media_by_month.py` on either location (internal drive or SSD), as long as you point it at the correct root folder.

---