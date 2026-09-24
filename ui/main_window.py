"""
ui/main_window.py
PSP 3000 Video Converter — Windows Media Player 9 Series ("Corona") Skinned Console (PyQt6)
Authentic 2003 WMP9 multimedia player skin aesthetic with custom window chrome,
phosphor LCD viewport, transport controls, and dense media telemetry.
"""

import os
import json
import subprocess
from pathlib import Path

from PyQt6.QtCore import (Qt, QPoint, QTimer, pyqtSlot)
from PyQt6.QtGui import (QFont, QMouseEvent)
from PyQt6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
                               QLabel, QMainWindow, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget, QFrame, QMessageBox)

from converter import ConverterThread, CODEC_PRESETS
from ffmpeg_manager import ffmpeg_path, ffprobe_path, is_ffmpeg_available, download_ffmpeg
from ui.wmp_skin import (
    WmpSkinFrame, WmpTitleBar, WmpLcdDisplay, WmpProgressBar, WmpTransportButton,
    WmpPanel, WmpMediaTray, CLR_WMP_GREEN_LIME, CLR_WMP_GREEN_MID, CLR_WMP_MUTED
)


# ── Stylesheet for Dropdowns and Dialogs ──────────────────────────────────────
STYLESHEET = """
/* ── Global ─────────────────────────── */
QWidget {
    font-family: 'Tahoma', 'Segoe UI', Verdana, sans-serif;
    font-size: 11px;
    color: #CBE8D2;
}

QComboBox {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #163220, stop:0.25 #0E2214, stop:0.75 #06140A, stop:1 #020703);
    border: 1px solid #1E3F28;
    border-radius: 3px;
    color: #00FF66;
    padding: 4px 10px;
    font-family: 'Lucida Console', 'Consolas', monospace;
    font-size: 11px;
    font-weight: bold;
    min-width: 190px;
}
QComboBox:hover {
    border-color: #00FF66;
    color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
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


# ── Main Frameless Skinned Window Class ────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PSP Video Converter // WMP-9 Series Skin")
        self.setFixedSize(860, 680)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAcceptDrops(True)

        self._input_path = ""
        self._output_path = ""
        self._converter = None
        self._drag_pos = None

        self._build_ui()
        self._check_ffmpeg_on_startup()

    def _build_ui(self):
        # 1. Main WMP9 Skinned Frame Container
        self.skinFrame = WmpSkinFrame()
        self.setCentralWidget(self.skinFrame)

        main_layout = QVBoxLayout(self.skinFrame)
        main_layout.setContentsMargins(6, 6, 6, 12)
        main_layout.setSpacing(8)

        # ── 1. Custom WMP9 Title Bar ──────────────────────────────────────────
        self.titleBar = WmpTitleBar("PSP VIDEO CONVERTER // 9 SERIES DIGITAL ENGINE", parent=self)
        self.titleBar.minimize_clicked.connect(self.showMinimized)
        self.titleBar.close_clicked.connect(self.close)
        main_layout.addWidget(self.titleBar)

        # Content layout inside the skinned frame
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(14, 2, 14, 2)
        content_layout.setSpacing(8)

        # ── 2. Top Hardware Sub-Header with LED Status ────────────────────────
        sub_header = QHBoxLayout()
        sub_header.setSpacing(10)

        sub_title = QLabel("WINDOWS MEDIA PLAYER 9 // SONY PSP-3000 AVC TRANSCODER")
        sub_title.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        sub_title.setStyleSheet("color: #4A7A58; letter-spacing: 0.5px;")
        sub_header.addWidget(sub_title)
        sub_header.addStretch()

        def make_wmp_led(label_text: str):
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(2, 0, 2, 0)
            l.setSpacing(4)
            led = QLabel("●")
            led.setStyleSheet("color: #00FF66; font-size: 10px;")
            txt = QLabel(label_text)
            txt.setFont(QFont("Lucida Console", 8, QFont.Weight.Bold))
            txt.setStyleSheet("color: #6A9E78;")
            l.addWidget(led)
            l.addWidget(txt)
            return w

        sub_header.addWidget(make_wmp_led("CORE: ONLINE"))
        sub_header.addWidget(make_wmp_led("DSP: READY"))
        sub_header.addWidget(make_wmp_led("480×272 NATIVE"))

        content_layout.addLayout(sub_header)

        # ── 3. Central Phosphor LCD Screen ────────────────────────────────────
        self.lcd = WmpLcdDisplay()
        self.lcd.set_idle()
        content_layout.addWidget(self.lcd)

        # ── 4. Compact Media Loading Tray (Drop Zone) ─────────────────────────
        self.dropTray = WmpMediaTray()
        self.dropTray.file_dropped.connect(self._on_file_selected)
        content_layout.addWidget(self.dropTray)

        # ── 5. Segmented LED Seek / Progress Bar ──────────────────────────────
        self.progressRow = QHBoxLayout()
        self.progressRow.setSpacing(10)

        self.progressBar = WmpProgressBar()
        self.progressRow.addWidget(self.progressBar)

        self.progressPctLabel = QLabel("00%")
        self.progressPctLabel.setFont(QFont("Lucida Console", 9, QFont.Weight.Bold))
        self.progressPctLabel.setStyleSheet("color: #00FF66; min-width: 38px;")
        self.progressRow.addWidget(self.progressPctLabel)

        content_layout.addLayout(self.progressRow)

        # ── 6. Hardware Parameters & Destination Panel ────────────────────────
        self.paramsPanel = WmpPanel("HARDWARE CONVERSION PARAMETERS")
        params_layout = QHBoxLayout(self.paramsPanel)
        params_layout.setContentsMargins(8, 6, 8, 6)
        params_layout.setSpacing(12)

        # Profile Selector
        preset_box = QHBoxLayout()
        preset_box.setSpacing(6)
        preset_lbl = QLabel("PROFILE:")
        preset_lbl.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        preset_lbl.setStyleSheet("color: #4A7A58;")

        self.codecSelector = QComboBox()
        for name in CODEC_PRESETS:
            self.codecSelector.addItem(name)
        preset_box.addWidget(preset_lbl)
        preset_box.addWidget(self.codecSelector)
        params_layout.addLayout(preset_box)

        # Output Directory
        out_box = QHBoxLayout()
        out_box.setSpacing(6)
        out_lbl = QLabel("DESTINATION:")
        out_lbl.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        out_lbl.setStyleSheet("color: #4A7A58;")

        self.outputPathLabel = QLabel("SAME AS SOURCE")
        self.outputPathLabel.setFont(QFont("Lucida Console", 8))
        self.outputPathLabel.setStyleSheet("color: #00FF66; background: #030804; padding: 4px 8px; border: 1px inset #102414; border-radius: 2px;")
        self.outputPathLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.changeOutputBtn = WmpTransportButton("CHANGE...")
        self.changeOutputBtn.clicked.connect(self._choose_output_folder)

        out_box.addWidget(out_lbl)
        out_box.addWidget(self.outputPathLabel)
        out_box.addWidget(self.changeOutputBtn)
        params_layout.addLayout(out_box)

        content_layout.addWidget(self.paramsPanel)

        # ── 7. Bottom WMP9 Transport Controls / Action Bar ────────────────────
        transportBar = QHBoxLayout()
        transportBar.setSpacing(8)

        # Open File Button
        self.browseBtn = WmpTransportButton("⏏  OPEN FILE")
        self.browseBtn.setFixedWidth(160)
        self.browseBtn.clicked.connect(self._browse_file)
        transportBar.addWidget(self.browseBtn)

        # Open Output Folder Button
        self.openFolderBtn = WmpTransportButton("📁  OPEN FOLDER")
        self.openFolderBtn.setFixedWidth(160)
        self.openFolderBtn.clicked.connect(self._open_output_folder)
        self.openFolderBtn.hide()
        transportBar.addWidget(self.openFolderBtn)

        # Cancel / Stop Button
        self.cancelBtn = WmpTransportButton("⏹  STOP")
        self.cancelBtn.setFixedWidth(120)
        self.cancelBtn.clicked.connect(self._cancel_conversion)
        self.cancelBtn.hide()
        transportBar.addWidget(self.cancelBtn)

        transportBar.addStretch()

        # Primary Hero Button: CONVERT TO PSP
        self.convertBtn = WmpTransportButton("▶  CONVERT TO PSP", is_hero=True)
        self.convertBtn.setFixedWidth(230)
        self.convertBtn.setEnabled(False)
        self.convertBtn.clicked.connect(self._start_conversion)
        transportBar.addWidget(self.convertBtn)

        content_layout.addLayout(transportBar)

        # ── 8. Missing FFmpeg Download Panel ──────────────────────────────────
        self.ffmpegPanel = WmpPanel("ENGINE INITIALIZATION")
        ffmpegLayout = QVBoxLayout(self.ffmpegPanel)
        ffmpegLayout.setContentsMargins(8, 8, 8, 8)
        ffmpegLayout.setSpacing(6)

        ffmpegWarn = QLabel("⚠️  Portable FFmpeg transcode engine not detected.")
        ffmpegWarn.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        ffmpegWarn.setStyleSheet("color: #FFB800;")
        ffmpegWarn.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.downloadFfmpegBtn = WmpTransportButton("⬇  DOWNLOAD PORTABLE ENCODE ENGINE", is_hero=True)
        self.downloadFfmpegBtn.clicked.connect(self._download_ffmpeg)

        ffmpegLayout.addWidget(ffmpegWarn)
        ffmpegLayout.addWidget(self.downloadFfmpegBtn)
        self.ffmpegPanel.hide()
        content_layout.addWidget(self.ffmpegPanel)

        main_layout.addLayout(content_layout)

    # ── Window Drag Handling ───────────────────────────────────────────────────
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 36:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

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
        dur_info = "00:00:00"
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
                    video_info = f"{v_codec} · {w}×{h}{sar_txt}"

                if a:
                    a_codec = a.get("codec_name", "AAC").upper()
                    a_rate = a.get("sample_rate", "48000")
                    a_ch = a.get("channels", 2)
                    audio_info = f"{a_codec} · {a_rate}Hz · {a_ch}CH"

                dur = float(data.get("format", {}).get("duration", 0))
                if dur > 0:
                    hrs = int(dur // 3600)
                    mins = int((dur % 3600) // 60)
                    secs = int(dur % 60)
                    dur_info = f"{hrs:02d}:{mins:02d}:{secs:02d}"
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
