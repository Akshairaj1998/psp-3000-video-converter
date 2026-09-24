"""
psp_validator.py
PSP-3000 output compliance checker.

Runs ffprobe against the converted file and validates every stream/container
property against the PSP-3000 hardware specification.  Returns a structured
report so the UI can show PASS / WARN / FAIL per parameter.
"""

from __future__ import annotations
import json
import subprocess
from dataclasses import dataclass, field
from typing import Any


# ── PSP-3000 specification ───────────────────────────────────────────────────
PSP_SPEC = {
    "container":       "mp4",
    "video_codec":     "h264",
    "profile":         {"Baseline", "Constrained Baseline"},   # ffprobe strings
    "levels":          {30, 40},     # 3.0 or 4.0 (HandBrake uses 4.0, hardware accepts 3.0/4.0)
    "width":           480,
    "height":          272,
    "pix_fmt":         "yuv420p",
    "sar":             {"1:1", "0:1", ""},
    "dar":             {"30:17", "16:9", ""},
    "has_b_frames":    0,
    "video_bitrate_min": 100_000,    # 100 kbps
    "video_bitrate_max": 1_000_000,  # up to 1 Mbps
    "audio_codec":     "aac",
    "audio_profile":   "LC",         # ffprobe: "LC"
    "audio_sample_rate": 48000,
    "audio_channels":  2,
    "audio_bitrate_min": 64_000,
    "audio_bitrate_max": 256_000,
}


@dataclass
class CheckResult:
    name: str
    actual: Any
    expected: Any
    passed: bool
    note: str = ""


@dataclass
class ValidationReport:
    checks: list[CheckResult] = field(default_factory=list)
    raw_video: dict = field(default_factory=dict)
    raw_audio: dict = field(default_factory=dict)
    raw_format: dict = field(default_factory=dict)
    ffprobe_error: str = ""

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)


def _run_ffprobe(ffprobe_exe: str, path: str) -> dict:
    result = subprocess.run(
        [
            ffprobe_exe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            path,
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        timeout=15,
    )
    return json.loads(result.stdout)


def _fps_ok(r_frame_rate: str) -> tuple[bool, str]:
    """Accept 29.97 (30000/1001) or 30000/1001 variants."""
    try:
        num, den = (int(x) for x in r_frame_rate.split("/"))
        fps = num / den
        ok = abs(fps - 29.97) < 0.1
        return ok, f"{fps:.4f}"
    except Exception:
        return False, r_frame_rate


def validate(ffprobe_exe: str, output_path: str) -> ValidationReport:
    """
    Run ffprobe and produce a full PSP-3000 ValidationReport.
    Never raises — errors are captured in report.ffprobe_error.
    """
    report = ValidationReport()

    try:
        data = _run_ffprobe(ffprobe_exe, output_path)
    except Exception as exc:
        report.ffprobe_error = str(exc)
        return report

    fmt     = data.get("format", {})
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), {})

    report.raw_format = fmt
    report.raw_video  = v
    report.raw_audio  = a

    def chk(name: str, actual: Any, passed: bool, expected: Any, note: str = ""):
        report.checks.append(CheckResult(name, actual, expected, passed, note))

    # ── Container ──────────────────────────────────────────────────────────────
    fmt_name    = fmt.get("format_name", "")
    brand       = fmt.get("tags", {}).get("major_brand", "unknown")
    compat      = fmt.get("tags", {}).get("compatible_brands", "")
    has_mp4     = "mp4" in fmt_name or "mov" in fmt_name
    chk("Container format",  fmt_name,  has_mp4,    "mp4")
    chk("Major brand",       brand,     brand in ("mp42", "isom"),  "mp42 (HandBrake) / isom",
        "MSNV is rejected; standard mp42 / isom is required for PSP /VIDEO/")
    if compat:
        chk("Compatible brands", compat, "mp42" in compat or "iso2" in compat or "isom" in compat, "mp42 / iso2 / avc1 / mp41")

    # ── Video ──────────────────────────────────────────────────────────────────
    codec   = v.get("codec_name", "")
    vtag    = v.get("codec_tag_string", "")
    profile = v.get("profile", "")
    level   = v.get("level", -1)          # integer e.g. 30 (3.0) or 40 (4.0)
    width   = v.get("width",  0)
    height  = v.get("height", 0)
    pix_fmt = v.get("pix_fmt", "")
    sar     = v.get("sample_aspect_ratio", "")
    dar     = v.get("display_aspect_ratio", "")
    has_b   = v.get("has_b_frames", -1)
    refs    = v.get("refs", -1)
    fps_ok, fps_str = _fps_ok(v.get("r_frame_rate", ""))
    vbr     = int(v.get("bit_rate", 0))

    chk("Video codec",       codec,   codec == "h264",                       "h264")
    if vtag:
        chk("Video codec tag", vtag,  vtag == "avc1",                        "avc1")
    chk("H.264 profile",     profile, profile in PSP_SPEC["profile"],        "Constrained Baseline / Baseline")
    chk("H.264 level",       f"{level/10:.1f}" if level > 0 else "?",
                             level in PSP_SPEC["levels"],                    "4.0 / 3.0")
    chk("Resolution",        f"{width}×{height}",
                             width == 480 and height == 272,                 "480×272")
    chk("Pixel format",      pix_fmt, pix_fmt == "yuv420p",                  "yuv420p")
    chk("SAR (pixel AR)",    sar,     sar in PSP_SPEC["sar"],                 "1:1",
        "Square pixels required. Non-square (e.g. 34:45) causes Unsupported Data")
    if dar:
        chk("DAR (aspect ratio)", dar, dar in PSP_SPEC["dar"] or dar == "30:17", "30:17 (widescreen)")
    chk("Frame rate",        fps_str, fps_ok,                                "29.97 (30000/1001)")
    chk("B-frames",          has_b,   has_b == 0,                            "0 (no B-frames)")
    chk("Reference frames",  refs,    refs in (1, -1),                       "1",
        "-1 = ffprobe could not read; treat as warn not fail")
    if vbr > 0:
        chk("Video bitrate", f"{vbr//1000} kbps",
                             PSP_SPEC["video_bitrate_min"] <= vbr <= PSP_SPEC["video_bitrate_max"],
                             "100–1000 kbps")

    # ── Audio ──────────────────────────────────────────────────────────────────
    acodec  = a.get("codec_name", "")
    atag    = a.get("codec_tag_string", "")
    aprofile= a.get("profile", "")
    asr     = int(a.get("sample_rate", 0))
    ach     = int(a.get("channels", 0))
    abr     = int(a.get("bit_rate", 0))

    chk("Audio codec",       acodec,  acodec == "aac",                       "aac")
    if atag:
        chk("Audio codec tag", atag,  atag == "mp4a",                        "mp4a")
    chk("AAC profile",       aprofile,aprofile == "LC",                       "LC  (AAC-LC)")
    chk("Audio sample rate", f"{asr} Hz", asr == 48000,                      "48000 Hz")
    chk("Audio channels",    f"{ach} (stereo)" if ach == 2 else str(ach), ach == 2, "2 (stereo)")
    if abr > 0:
        chk("Audio bitrate", f"{abr//1000} kbps",
                             PSP_SPEC["audio_bitrate_min"] <= abr <= PSP_SPEC["audio_bitrate_max"],
                             "64–256 kbps")

    return report
