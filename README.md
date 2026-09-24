# PSP 3000 Video Converter

A dedicated desktop video conversion tool designed specifically for the **Sony PlayStation Portable (PSP-3000, PSP-2000, PSP-E1000)**. Converts any modern video file (MKV, MP4, AVI, MOV, WEBM, etc.) into 100% hardware-compatible MP4 files that play natively on PSP firmware without "Unsupported Data" errors.

---

## Features

- **Hardware Compliant Output**:
  - **Video**: H.264 / AVC (Constrained Baseline Profile, Level 4.0 / 3.0, 480x272, 29.97 fps)
  - **SAR / DAR Normalization**: Enforces square pixels (SAR 1:1) and aspect ratio preservation with letterboxing/pillarboxing so non-16:9 videos are never stretched.
  - **Audio**: AAC-LC Stereo, 48,000 Hz, 160 kbps.
  - **Container**: MP4 (`major_brand: mp42`, `compatible_brands: mp42iso2avc1mp41`) with faststart (`moov` atom at front for instant Memory Stick playback).
  - **Clean Bitstream**: Strips source metadata and chapter tracks to prevent broken QuickTime track warnings.
- **Built-in Portable FFmpeg Manager**: Automatically downloads and configures portable FFmpeg and FFprobe binaries if not present on your system.
- **Automated PSP-3000 Compliance Validator**: Automatically runs `ffprobe` on completed files to verify all container, stream, bitrate, and codec parameters.
- **Simple One-Click Workflow**: Drag-and-drop or browse for a video, click "Convert to PSP", and open the output folder.

---

## Installation & Running

### Option 1: Run from Source

1. Clone this repository:
   ```bash
   git clone <repo-url>
   cd "PSP video converter"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

### Option 2: Build Standalone Executable (.exe)

Run the included build script:
```bash
build.bat
```
Or with PyInstaller:
```bash
python -m PyInstaller --onefile --windowed --name "PSP 3000 Video Converter" --add-data "ui;ui" --add-data "psp_validator.py;." main.py
```

The resulting executable will be created in the `dist/` folder.

---

## License
MIT
