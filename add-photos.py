#!/usr/bin/env python3
"""Add photos to the site.

Usage: ./add-photos.py [--album "Beach 2026"] FILE_OR_DIR [...]

Each photo is converted to JPEG, resized (2048px full, 600px thumbnail),
stripped of ALL metadata (GPS, camera, etc.), and appended to photos.json.
Needs macOS `sips` and `exiftool` (brew install exiftool).
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FULL = ROOT / "photos" / "full"
THUMB = ROOT / "photos" / "thumb"
MANIFEST = ROOT / "photos.json"
EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".webp"}


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def taken_date(src):
    out = run("exiftool", "-s3", "-d", "%Y-%m-%d", "-DateTimeOriginal", "-CreateDate", str(src))
    lines = [l for l in out.splitlines() if l.strip()]
    return lines[0] if lines else None


def size(path):
    out = run("sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path))
    vals = [int(l.split(":")[1]) for l in out.splitlines() if "pixel" in l]
    return vals[0], vals[1]


def make(src, dest, max_px, quality):
    run("sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
        "-Z", str(max_px), str(src), "--out", str(dest))
    run("exiftool", "-q", "-all=", "-overwrite_original", str(dest))


def collect(paths):
    for p in map(Path, paths):
        if p.is_dir():
            yield from sorted(f for f in p.rglob("*") if f.suffix.lower() in EXTS)
        elif p.suffix.lower() in EXTS:
            yield p
        else:
            print(f"skip (not an image): {p}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--album", help="section heading; defaults to the year taken")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    photos = json.loads(MANIFEST.read_text())
    known = {p["file"] for p in photos}
    added = 0

    for src in collect(args.paths):
        name = hashlib.sha256(src.read_bytes()).hexdigest()[:16] + ".jpg"
        if name in known:
            continue
        full, thumb = FULL / name, THUMB / name
        make(src, full, 2048, 82)
        make(src, thumb, 600, 75)
        w, h = size(thumb)
        entry = {"file": name, "date": taken_date(src), "w": w, "h": h}
        if args.album:
            entry["album"] = args.album
        photos.append(entry)
        known.add(name)
        added += 1
        print(f"added {src.name} -> {name}")

    photos.sort(key=lambda p: p.get("date") or "", reverse=True)
    MANIFEST.write_text(json.dumps(photos, indent=1) + "\n")
    print(f"{added} added, {len(photos)} total. Edit photos.json to add captions, then commit and push.")


if __name__ == "__main__":
    main()
