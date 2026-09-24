"""
converter.py
QThread worker that calls FFmpeg to convert a video to PSP 3000 format.

PSP 3000 target spec:
  Resolution : 480x272
  Video codec: H.264 Baseline Level 3.0
  Video bitrate: 768 kbps
  Audio codec: AAC
  Audio bitrate: 128 kbps
  Frame rate: 29.97 fps
  Container: .mp4
"""

import re
import subprocess
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


# ── PSP-3000 H.264 preset (HandBrake Reference Matched) ─────────────────────────
#
# Matched to known-working PSP-3000 HandBrake reference implementation:
#   1. Container: MP4 with major_brand=mp42, compatible_brands=mp42iso2avc1mp41, +faststart
#   2. Video: H.264 Constrained Baseline, Level 4.0, 480x272, 30000/1001 fps, yuv420p
#   3. Geometry: Preserves aspect ratio, pads to 480x272, forces SAR 1:1, DAR 30:17
#   4. Bitstream: No B-frames (-bf 0), 1 ref frame (-refs 1), CAVLC (-coder 0), 680k (cap 768k)
#   5. Audio: AAC-LC 48,000 Hz stereo, 160 kbps, codec tag mp4a
#   6. Metadata: -map_metadata -1 -map_chapters -1 (no metadata/chapter bleedthrough)
#
PSP_H264_FLAGS = [
    "-y",
    "-map_metadata", "-1",              # strip ALL source metadata
    "-map_chapters", "-1",              # strip chapter markers to prevent broken QT tracks
    "-vf", "scale=480:272:force_original_aspect_ratio=decrease,pad=480:272:(ow-iw)/2:(oh-ih)/2,setsar=1",
    "-c:v", "libx264",
    "-profile:v", "baseline",           # Constrained Baseline
    "-level:v", "4.0",                  # HandBrake PSP level 4.0
    "-pix_fmt", "yuv420p",              # YUV 4:2:0
    "-b:v", "680k",
    "-maxrate:v", "768k",               # VBV cap
    "-bufsize:v", "2000k",
    "-r", "30000/1001",                 # ~29.97 fps
    "-g", "60",                         # keyframe every ~2 s
    "-bf", "0",                         # Baseline = no B-frames
    "-refs", "1",                       # 1 reference frame
    "-coder", "0",                      # CAVLC
    "-c:a", "aac",
    "-profile:a", "aac_low",            # AAC-LC
    "-b:a", "160k",                     # 160 kbps matching HandBrake
    "-ar", "48000",                     # 48 kHz
    "-ac", "2",                         # stereo
    "-brand", "mp42",                   # major_brand = mp42
    "-movflags", "+faststart",          # moov atom at beginning of file
]

# ── MPEG-4 Part 2 preset (fallback) ───────────────────────────────────────────
PSP_MPEG4_FLAGS = [
    "-y",
    "-map_metadata", "-1",
    "-vcodec", "mpeg4",
    "-b:v", "768k",
    "-vf", "scale=480:272:force_original_aspect_ratio=decrease,pad=480:272:(ow-iw)/2:(oh-ih)/2,setsar=1",
    "-r", "29.97",
    "-acodec", "aac",
    "-profile:a", "aac_low",
    "-ab", "128k",
    "-ar", "48000",
    "-ac", "2",
    "-f", "psp",
]

CODEC_PRESETS = {
    "PSP-3000 H.264 (Recommended)": PSP_H264_FLAGS,
    "MPEG-4 (Fallback)": PSP_MPEG4_FLAGS,
}

# Default
PSP_FFMPEG_FLAGS = PSP_H264_FLAGS


def _parse_duration(line: str) -> float | None:
    """Extract total duration in seconds from FFmpeg's 'Duration:' line."""
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", line)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        return h * 3600 + mn * 60 + s
    return None


def _parse_time(line: str) -> float | None:
    """Extract the current encode position in seconds from FFmpeg's progress output."""
    m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        return h * 3600 + mn * 60 + s
    return None


class ConverterThread(QThread):
    """
    Runs FFmpeg conversion in a background thread.

    Signals
    -------
    progress(int)        0 – 100 percent complete
    status(str)          human-readable status message
    finished(str)        path to the output file on success
    error(str)           error message on failure
    """

    progress = pyqtSignal(int)
    status   = pyqtSignal(str)
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, ffmpeg_exe: str, input_path: str, output_path: str,
                 flags: list | None = None):
        super().__init__()
        self._ffmpeg  = ffmpeg_exe
        self._input   = input_path
        self._output  = output_path
        self._flags   = flags if flags is not None else PSP_H264_FLAGS
        self._aborted = False


    # ── public ────────────────────────────────────────────────────────────────

    def abort(self):
        self._aborted = True
        if hasattr(self, "_proc") and self._proc.poll() is None:
            self._proc.terminate()

    # ── QThread entry point ───────────────────────────────────────────────────

    def run(self):
        cmd = (
            [self._ffmpeg, "-i", self._input]
            + self._flags
            + [self._output]
        )

        try:
            self._proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,  # hide console on Windows
            )

            total_duration: float | None = None

            for line in self._proc.stderr:
                if self._aborted:
                    break

                # Grab total duration once
                if total_duration is None:
                    total_duration = _parse_duration(line)

                # Update progress from encode position
                current = _parse_time(line)
                if current is not None and total_duration:
                    pct = min(int(current / total_duration * 100), 99)
                    self.progress.emit(pct)
                    self.status.emit(f"Converting… {pct}%")

            self._proc.wait()

            if self._aborted:
                self.error.emit("Conversion cancelled.")
                return

            if self._proc.returncode != 0:
                self.error.emit(
                    f"FFmpeg exited with code {self._proc.returncode}. "
                    "The input file may be unsupported or corrupted."
                )
                return

            if not Path(self._output).exists():
                self.error.emit("Output file was not created. Conversion failed.")
                return

            self.progress.emit(100)
            self.status.emit("Done!")
            self.finished.emit(self._output)

        except FileNotFoundError:
            self.error.emit(
                "FFmpeg executable not found. Please restart the app to download it."
            )
        except Exception as exc:
            self.error.emit(f"Unexpected error: {exc}")
