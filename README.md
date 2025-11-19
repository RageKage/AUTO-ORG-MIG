# Media Organizer (Desktop ➜ SSD)

Two Python scripts work together to keep your photo/video library organized:

- `organize_media_by_month.py` – sorts everything in `_inbox` into a clean date-based structure.
- `migrate_media_to_SSD.py` – copies organized months from your Desktop to the SSD.

---

## 1. Requirements

- Python 3 (run with `python3` on macOS).
- Pillow for EXIF dates:

  ```bash
  pip3 install pillow
  ```

---

## 2. Folder layout (after organizing)

When you run `organize_media_by_month.py` on your Pictures folder (for example `/Users/fadel/Desktop/Pictures`), anything in `_inbox` is moved into:

```text
Pictures/
  2025-07/
    2025-07-28/
      jpeg/
      raw/
      video/
  _inbox/
```

- `YYYY-MM/` – one folder per month  
- `YYYY-MM-DD/` – one folder per shooting day inside each month  
- `jpeg/` – JPEG/PNG images  
- `raw/` – RAW files (`.raf`, `.cr2`, `.nef`, `.dng`, `.arw`, `.rw2`, `.orf`)  
- `video/` – video files (`.mp4`, `.mov`, `.m4v`, `.avi`, `.mts`, `.m2ts`)  
- `_inbox/` – drop new media here; the script moves it out into the right date folders

Files like `.log`, `.txt`, `.psd`, etc. are ignored.

---

## 3. Daily workflow (Desktop)

From this folder (`Org`) in Terminal:

1. **Drop new media into `_inbox`:**

   Copy/import new photos and videos into:

   ```text
   /Users/fadel/Desktop/Pictures/_inbox
   ```

2. **Organize on Desktop:**

   ```bash
   python3 organize_media_by_month.py "/Users/fadel/Desktop/Pictures"
   ```

   This:
   - Looks only inside `_inbox`
   - Figures out dates from EXIF (or file modified time)
   - Moves files into `YYYY-MM/YYYY-MM-DD/jpeg|raw|video`
   - Leaves already-organized months alone

---

## 4. Migrate to SSD (Portal)

After organizing on the Desktop, copy new months/files to the SSD:

```bash
python3 migrate_media_to_SSD.py \
  "/Users/fadel/Desktop/Pictures" \
  "/Volumes/Portal/Pictures"
```

This script:
- Treats `/Users/fadel/Desktop/Pictures` as the **master** library
- Treats `/Volumes/Portal/Pictures` as the **SSD archive**
- Syncs top-level `YYYY-MM` folders:
  - If a month is new on the SSD → copy the whole folder
  - If a month already exists → only copy files that are missing
- Never deletes anything on Desktop or SSD

You can run both scripts as many times as you want:
- `organize_media_by_month.py` keeps sorting whatever is in `_inbox`
- `migrate_media_to_SSD.py` keeps the SSD updated with new months/files
