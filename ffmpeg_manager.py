"""
ffmpeg_manager.py
Handles downloading and locating a portable FFmpeg binary for the PSP Converter app.
FFmpeg is downloaded from the official GitHub releases (gyan.dev builds for Windows).
"""

import os
import sys
import zipfile
import shutil
import threading
import urllib.request
from pathlib import Path

# Portable FFmpeg stored next to the executable (or script)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

FFMPEG_DIR = BASE_DIR / "ffmpeg_bin"
FFMPEG_EXE  = FFMPEG_DIR / "ffmpeg.exe"
FFPROBE_EXE = FFMPEG_DIR / "ffprobe.exe"

# Official portable build from gyan.dev (GitHub Releases mirror)
FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


def ffmpeg_path() -> str:
    """Return the path to the ffmpeg executable (local bundle or system PATH)."""
    if FFMPEG_EXE.exists():
        return str(FFMPEG_EXE)
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    return ""


def ffprobe_path() -> str:
    """Return the path to the ffprobe executable (local bundle or system PATH)."""
    if FFPROBE_EXE.exists():
        return str(FFPROBE_EXE)
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return system_ffprobe
    return ""


def is_ffmpeg_available() -> bool:
    return bool(ffmpeg_path())


def download_ffmpeg(progress_callback=None, done_callback=None, error_callback=None):
    """
    Download portable FFmpeg in a background thread.
    progress_callback(percent: int)   — called with 0-100
    done_callback()                   — called on success
    error_callback(message: str)      — called on failure
    """

    def _download():
        try:
            FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
            zip_path = FFMPEG_DIR / "ffmpeg_download.zip"

            # --- Download ---
            def _reporthook(block_num, block_size, total_size):
                if total_size > 0 and progress_callback:
                    pct = min(int(block_num * block_size * 100 / total_size), 95)
                    progress_callback(pct)

            urllib.request.urlretrieve(FFMPEG_URL, zip_path, reporthook=_reporthook)

            # --- Extract ffmpeg.exe and ffprobe.exe from the zip ---
            if progress_callback:
                progress_callback(96)
            needed = {"bin/ffmpeg.exe": FFMPEG_EXE, "bin/ffprobe.exe": FFPROBE_EXE}
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    for suffix, target in needed.items():
                        if member.endswith(suffix):
                            source = zf.open(member)
                            with open(target, "wb") as f:
                                shutil.copyfileobj(source, f)


            zip_path.unlink(missing_ok=True)

            if progress_callback:
                progress_callback(100)
            if done_callback:
                done_callback()

        except Exception as exc:
            if error_callback:
                error_callback(str(exc))

    thread = threading.Thread(target=_download, daemon=True)
    thread.start()
    return thread
