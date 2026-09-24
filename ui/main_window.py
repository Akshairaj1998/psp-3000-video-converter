"""
ui/main_window.py
PSP 3000 Video Converter — Early-2000s Multimedia Player Skin (PyQt6)
Aesthetic inspired by Windows Media Player 7/8/9, Winamp skins, and Xbox-era dark green/obsidian consoles.
"""

import os
import json
import subprocess
from pathlib import Path

from PyQt6.QtCore import (Qt, QTimer, pyqtSlot)
from PyQt6.QtGui import (QFont, QIcon)
from PyQt6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
                               QLabel, QMainWindow, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget, QFrame, QMessageBox)

from converter import ConverterThread, CODEC_PRESETS
from ffmpeg_manager import ffmpeg_path, ffprobe_path, is_ffmpeg_available, download_ffmpeg
from ui.skin_widgets import (
    RetroConsoleFrame, PhosphorLCDScreen, SegmentedLedMeter, SkeuomorphicButton,
    RetroInsetPanel, CompactMediaTray, CLR_LIME_BRIGHT, CLR_LIME_MID, CLR_TEXT_MUTED
)


# ── Stylesheet for Dropdowns, Dialogs, and Combos ─────────────────────────────
STYLESHEET = """
/* ── Global ─────────────────────────── */
QWidget {
    font-family: 'Segoe UI', Tahoma, Verdana, sans-serif;
    font-size: 12px;
    color: #CBE8D2;
}

QComboBox {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #142A1A, stop:0.3 #0E2014, stop:0.8 #06140A, stop:1 #030A05);
    border: 1px solid #1E3F28;
    border-radius: 4px;
    color: #00FF66;
    padding: 5px 12px;
    font-family: 'Lucida Console', 'Consolas', monospace;
    font-size: 11px;
    font-weight: bold;
    min-width: 200px;
}
QComboBox:hover {
    border-color: #00FF66;
    color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background: #06140A;
    border: 1px solid #00FF66;
    color: #00FF66;
    selection-background-color: #006629;
    selection-color: #FFFFFF;
}

QMessageBox {
    background-color: #06140A;
    color: #CBE8D2;
}
"""


# ── Main Application Window ───────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PSP Video Converter // Digital Media Console")
        self.setFixedSize(860, 680)
        self.setAcceptDrops(True)

        self._input_path = ""
        self._output_path = ""
        self._converter = None

        self._build_ui()
        self._check_ffmpeg_on_startup()

    def _build_ui(self):
        # 1. Main Console Chassis
        self.console = RetroConsoleFrame()
        self.setCentralWidget(self.console)

        main_layout = QVBoxLayout(self.console)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(10)

        # ── Header Console Identity ───────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)

        app_title = QLabel("PSP TRANSCODER  //  DIGITAL MEDIA CONSOLE")
        app_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #00FF66; letter-spacing: 1.5px;")

        app_sub = QLabel("MPEG-4 AVC / AAC-LC ENCODE ENGINE · PSP-3000 HARDWARE NATIVE")
        app_sub.setFont(QFont("Lucida Console", 8, QFont.Weight.Bold))
        app_sub.setStyleSheet("color: #4A7A58; letter-spacing: 0.5px;")

        title_col.addWidget(app_title)
        title_col.addWidget(app_sub)
        header.addLayout(title_col)
        header.addStretch()

        # Hardware Status LED Matrix
        led_row = QHBoxLayout()
        led_row.setSpacing(12)

        def make_hardware_led(label_text: str, is_on: bool = True):
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(4, 2, 4, 2)
            l.setSpacing(5)
            led = QLabel("●")
            led.setStyleSheet(f"color: {'#00FF66' if is_on else '#004D1F'}; font-size: 11px;")
            txt = QLabel(label_text)
            txt.setFont(QFont("Lucida Console", 8, QFont.Weight.Bold))
            txt.setStyleSheet("color: #6A9E78;")
            l.addWidget(led)
            l.addWidget(txt)
            return w

        led_row.addWidget(make_hardware_led("CORE: ONLINE"))
        led_row.addWidget(make_hardware_led("DSP: READY"))
        led_row.addWidget(make_hardware_led("480x272"))

        header.addLayout(led_row)
        main_layout.addLayout(header)

        # ── Central Phosphor LCD Screen ───────────────────────────────────────
        self.lcd = PhosphorLCDScreen()
        self.lcd.set_idle()
        main_layout.addWidget(self.lcd)

        # ── Compact Media Tray / Drop Zone ────────────────────────────────────
        self.dropTray = CompactMediaTray()
        self.dropTray.file_dropped.connect(self._on_file_selected)
        main_layout.addWidget(self.dropTray)

        # ── Segmented LED Progress Meter ──────────────────────────────────────
        self.meterRow = QHBoxLayout()
        self.meterRow.setSpacing(10)

        self.progressBar = SegmentedLedMeter()
        self.meterRow.addWidget(self.progressBar)

        self.progressPctLabel = QLabel("00%")
        self.progressPctLabel.setFont(QFont("Lucida Console", 10, QFont.Weight.Bold))
        self.progressPctLabel.setStyleSheet("color: #00FF66; min-width: 44px;")
        self.meterRow.addWidget(self.progressPctLabel)

        main_layout.addLayout(self.meterRow)

        # ── Hardware Parameters & Destination Panel ───────────────────────────
        self.paramsPanel = RetroInsetPanel("TRANSCODE HARDWARE PARAMETERS")
        params_layout = QHBoxLayout(self.paramsPanel)
        params_layout.setContentsMargins(10, 8, 10, 8)
        params_layout.setSpacing(14)

        # Profile Selector
        preset_box = QHBoxLayout()
        preset_box.setSpacing(6)
        preset_lbl = QLabel("PROFILE:")
        preset_lbl.setFont(QFont("Lucida Console", 8, QFont.Weight.Bold))
        preset_lbl.setStyleSheet("color: #4A7A58;")

        self.codecSelector = QComboBox()
        for name in CODEC_PRESETS:
            self.codecSelector.addItem(name)
        preset_box.addWidget(preset_lbl)
        preset_box.addWidget(self.codecSelector)
        params_layout.addLayout(preset_box)

        # Output Destination
        out_box = QHBoxLayout()
        out_box.setSpacing(6)
        out_lbl = QLabel("DESTINATION:")
        out_lbl.setFont(QFont("Lucida Console", 8, QFont.Weight.Bold))
        out_lbl.setStyleSheet("color: #4A7A58;")

        self.outputPathLabel = QLabel("SAME AS SOURCE")
        self.outputPathLabel.setFont(QFont("Lucida Console", 8))
        self.outputPathLabel.setStyleSheet("color: #00FF66; background: #040C06; padding: 4px 8px; border: 1px inset #142A1A; border-radius: 3px;")
        self.outputPathLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.changeOutputBtn = SkeuomorphicButton("CHANGE...")
        self.changeOutputBtn.clicked.connect(self._choose_output_folder)

        out_box.addWidget(out_lbl)
        out_box.addWidget(self.outputPathLabel)
        out_box.addWidget(self.changeOutputBtn)
        params_layout.addLayout(out_box)

        main_layout.addWidget(self.paramsPanel)

        # ── Primary Control Buttons / Action Bar ──────────────────────────────
        actionBar = QHBoxLayout()
        actionBar.setSpacing(10)

        # Browse / Select Media
        self.browseBtn = SkeuomorphicButton("⏏  SELECT VIDEO FILE")
        self.browseBtn.setFixedWidth(180)
        self.browseBtn.clicked.connect(self._browse_file)
        actionBar.addWidget(self.browseBtn)

        # Open Output Folder Button
        self.openFolderBtn = SkeuomorphicButton("📁  OPEN OUTPUT FOLDER")
        self.openFolderBtn.setFixedWidth(190)
        self.openFolderBtn.clicked.connect(self._open_output_folder)
        self.openFolderBtn.hide()
        actionBar.addWidget(self.openFolderBtn)

        # Cancel Button
        self.cancelBtn = SkeuomorphicButton("⏹  STOP / CANCEL")
        self.cancelBtn.setFixedWidth(140)
        self.cancelBtn.clicked.connect(self._cancel_conversion)
        self.cancelBtn.hide()
        actionBar.addWidget(self.cancelBtn)

        actionBar.addStretch()

        # Primary Hero Button: CONVERT TO PSP
        self.convertBtn = SkeuomorphicButton("▶  CONVERT TO PSP", is_hero=True)
        self.convertBtn.setFixedWidth(240)
        self.convertBtn.setEnabled(False)
        self.convertBtn.clicked.connect(self._start_conversion)
        actionBar.addWidget(self.convertBtn)

        main_layout.addLayout(actionBar)

        # ── Missing FFmpeg Panel ──────────────────────────────────────────────
        self.ffmpegPanel = RetroInsetPanel("ENGINE INITIALIZATION")
        ffmpegLayout = QVBoxLayout(self.ffmpegPanel)
        ffmpegLayout.setContentsMargins(10, 10, 10, 10)
        ffmpegLayout.setSpacing(6)

        ffmpegWarn = QLabel("⚠️  Portable FFmpeg transcode engine not detected.")
        ffmpegWarn.setFont(QFont("Lucida Console", 9, QFont.Weight.Bold))
        ffmpegWarn.setStyleSheet("color: #FFB000;")
        ffmpegWarn.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.downloadFfmpegBtn = SkeuomorphicButton("⬇  DOWNLOAD PORTABLE ENCODE ENGINE (AUTOMATIC)", is_hero=True)
        self.downloadFfmpegBtn.clicked.connect(self._download_ffmpeg)

        ffmpegLayout.addWidget(ffmpegWarn)
        ffmpegLayout.addWidget(self.downloadFfmpegBtn)
        self.ffmpegPanel.hide()
        main_layout.addWidget(self.ffmpegPanel)

    # ── FFmpeg Detection & Download ────────────────────────────────────────────
    def _check_ffmpeg_on_startup(self):
        if not is_ffmpeg_available():
            self.convertBtn.hide()
            self.ffmpegPanel.show()

    def _download_ffmpeg(self):
        self.downloadFfmpegBtn.setEnabled(False)
        self.downloadFfmpegBtn.setText("⬇  DOWNLOADING ENGINE...")
        self.lcd.set_converting(0, "DOWNLOADING PORTABLE FFMPEG ENCODE ENGINE...")

        def _progress(pct):
            self.progressBar.setValue(pct)
            self.progressPctLabel.setText(f"{pct:02d}%")

        def _done():
            self.ffmpegPanel.hide()
            self.convertBtn.show()
            self.progressBar.setValue(0)
            self.progressPctLabel.setText("00%")
            if self._input_path:
                self._on_file_selected(self._input_path)
            else:
                self.lcd.set_idle()

        def _error(msg):
            self.downloadFfmpegBtn.setEnabled(True)
            self.downloadFfmpegBtn.setText("⬇  RETRY ENGINE DOWNLOAD")
            self.lcd.set_error(f"Download error: {msg}")

        download_ffmpeg(
            progress_callback=lambda p: QTimer.singleShot(0, lambda: _progress(p)),
            done_callback=lambda: QTimer.singleShot(0, _done),
            error_callback=lambda m: QTimer.singleShot(0, lambda: _error(m)),
        )

    # ── File Selection & Stream Metadata Inspection ────────────────────────────
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.3gp *.ts *.m2ts);;All Files (*)",
        )
        if path:
            self._on_file_selected(path)

    @pyqtSlot(str)
    def _on_file_selected(self, path: str):
        self._input_path = path
        self.dropTray.set_file(path)
        self.convertBtn.setEnabled(True)
        self.openFolderBtn.hide()
        self.cancelBtn.hide()
        self.progressBar.setValue(0)
        self.progressPctLabel.setText("00%")

        # Default output file
        in_p = Path(path)
        default_out = in_p.parent / f"{in_p.stem}_PSP.mp4"
        self._output_path = str(default_out)
        self.outputPathLabel.setText(str(in_p.parent))

        # Inspect and populate LCD
        self._inspect_and_update_lcd(path)

    def _inspect_and_update_lcd(self, path: str):
        """Extract stream properties via ffprobe and display in phosphor LCD."""
        file_name = Path(path).name
        video_info = "UNKNOWN CODEC"
        audio_info = "UNKNOWN AUDIO"
        dur_info = "00:00"
        size_info = f"{Path(path).stat().st_size / (1024*1024):.1f} MB"

        probe = ffprobe_path()
        if probe:
            try:
                res = subprocess.run(
                    [probe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
                    capture_output=True, text=True, timeout=8, creationflags=subprocess.CREATE_NO_WINDOW
                )
                data = json.loads(res.stdout)
                v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
                a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})

                if v:
                    v_codec = v.get("codec_name", "AVC").upper()
                    w, h = v.get("width", 0), v.get("height", 0)
                    sar = v.get("sample_aspect_ratio", "")
                    sar_txt = f" [SAR {sar}]" if sar and sar != "1:1" else ""
                    video_info = f"{v_codec} · {w}x{h}{sar_txt}"

                if a:
                    a_codec = a.get("codec_name", "AAC").upper()
                    a_rate = a.get("sample_rate", "48000")
                    a_ch = a.get("channels", 2)
                    audio_info = f"{a_codec} · {a_rate}Hz · {a_ch}CH"

                dur = float(data.get("format", {}).get("duration", 0))
                if dur > 0:
                    mins, secs = int(dur // 60), int(dur % 60)
                    dur_info = f"{mins:02d}:{secs:02d}"
            except Exception:
                pass

        self.lcd.set_file_info(file_name, video_info, audio_info, dur_info, size_info)

    def _choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Destination Folder")
        if folder and self._input_path:
            in_p = Path(self._input_path)
            self._output_path = str(Path(folder) / f"{in_p.stem}_PSP.mp4")
            self.outputPathLabel.setText(folder)

    # ── Transcode Operations ───────────────────────────────────────────────────
    def _start_conversion(self):
        if not self._input_path:
            return

        ffmpeg = ffmpeg_path()
        if not ffmpeg:
            QMessageBox.warning(self, "Engine Missing", "FFmpeg executable not available.")
            return

        self.convertBtn.setEnabled(False)
        self.browseBtn.setEnabled(False)
        self.changeOutputBtn.setEnabled(False)
        self.openFolderBtn.hide()
        self.cancelBtn.show()
        self.progressBar.setValue(0)
        self.progressPctLabel.setText("00%")

        selected_preset = self.codecSelector.currentText()
        flags = CODEC_PRESETS.get(selected_preset)
        self._converter = ConverterThread(ffmpeg, self._input_path, self._output_path, flags=flags)

        self._converter.progress.connect(self._on_progress)
        self._converter.status.connect(self._on_status)
        self._converter.finished.connect(self._on_finished)
        self._converter.error.connect(self._on_error)
        self._converter.start()

    def _cancel_conversion(self):
        if self._converter and self._converter.isRunning():
            self._converter.abort()
        self._reset_to_idle()

    @pyqtSlot(int)
    def _on_progress(self, pct: int):
        self.progressBar.setValue(pct)
        self.progressPctLabel.setText(f"{pct:02d}%")

    @pyqtSlot(str)
    def _on_status(self, msg: str):
        self.lcd.set_converting(self.progressBar.value(), msg)

    @pyqtSlot(str)
    def _on_finished(self, output_path: str):
        self.progressBar.setValue(100)
        self.progressPctLabel.setText("100%")
        self.cancelBtn.hide()
        self.openFolderBtn.show()
        self.convertBtn.setEnabled(True)
        self.browseBtn.setEnabled(True)
        self.changeOutputBtn.setEnabled(True)

        self._output_path = output_path
        self.lcd.set_done(output_path)

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        self.cancelBtn.hide()
        self.convertBtn.setEnabled(True)
        self.browseBtn.setEnabled(True)
        self.changeOutputBtn.setEnabled(True)
        self.lcd.set_error(msg)

    def _open_output_folder(self):
        folder = str(Path(self._output_path).parent)
        os.startfile(folder)

    def _reset_to_idle(self):
        self.cancelBtn.hide()
        self.convertBtn.setEnabled(bool(self._input_path))
        self.browseBtn.setEnabled(True)
        self.changeOutputBtn.setEnabled(True)
        self.progressBar.setValue(0)
        self.progressPctLabel.setText("00%")
        if self._input_path:
            self._inspect_and_update_lcd(self._input_path)
        else:
            self.lcd.set_idle()


def apply_stylesheet(app: QApplication):
    app.setStyleSheet(STYLESHEET)
