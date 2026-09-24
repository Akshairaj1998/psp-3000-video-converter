"""
ui/main_window.py
PSP 3000 Video Converter — Main Application Window (PyQt6)
"""

import os
from pathlib import Path

from PyQt6.QtCore import (Qt, QMimeData, QPropertyAnimation,
                           QEasingCurve, QRect, QTimer, pyqtSlot)
from PyQt6.QtGui import (QColor, QDragEnterEvent, QDropEvent, QFont,
                          QFontDatabase, QIcon, QPainter, QPalette,
                          QPixmap, QLinearGradient, QBrush)
from PyQt6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
                              QLabel, QMainWindow, QProgressBar,
                              QPushButton, QSizePolicy, QVBoxLayout,
                              QWidget, QFrame, QGraphicsDropShadowEffect,
                              QMessageBox, QGraphicsOpacityEffect)

from converter import ConverterThread, CODEC_PRESETS
from ffmpeg_manager import ffmpeg_path, ffprobe_path, is_ffmpeg_available, download_ffmpeg


# ── Stylesheet ─────────────────────────────────────────────────────────────────
STYLESHEET = """
/* ── Global ─────────────────────────── */
QWidget {
    background-color: #0D0F14;
    color: #E2E8F0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

/* ── Main window ─────────────────────── */
QMainWindow {
    background-color: #0D0F14;
}

/* ── Drop zone card ──────────────────── */
#dropZone {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #131824, stop:1 #0E1520);
    border: 2px dashed #2A3A5C;
    border-radius: 18px;
}
#dropZone[dragActive="true"] {
    border: 2px dashed #00D4FF;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0E1B30, stop:1 #091528);
}

/* ── Labels ──────────────────────────── */
#titleLabel {
    color: #FFFFFF;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
#subtitleLabel {
    color: #64748B;
    font-size: 12px;
}
#dropHintLabel {
    color: #94A3B8;
    font-size: 15px;
    font-weight: 500;
}
#dropSubLabel {
    color: #475569;
    font-size: 11px;
}
#fileNameLabel {
    color: #00D4FF;
    font-size: 13px;
    font-weight: 600;
}
#statusLabel {
    color: #94A3B8;
    font-size: 12px;
}
#statusLabelDone {
    color: #10B981;
    font-size: 12px;
    font-weight: 600;
}
#statusLabelError {
    color: #F87171;
    font-size: 12px;
    font-weight: 600;
}

/* ── Spec badge ──────────────────────── */
#specCard {
    background: #131824;
    border: 1px solid #1E2D45;
    border-radius: 10px;
}
#specTitle {
    color: #475569;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}
#specValue {
    color: #CBD5E1;
    font-size: 11px;
    font-weight: 600;
}

/* ── Progress bar ────────────────────── */
QProgressBar {
    background-color: #1E2D45;
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00D4FF, stop:1 #A855F7);
    border-radius: 5px;
}

/* ── Codec selector ─────────────────── */
QComboBox#codecSelector {
    background: #131824;
    border: 1px solid #2A3A5C;
    border-radius: 8px;
    color: #CBD5E1;
    padding: 6px 12px;
    font-size: 12px;
    min-width: 180px;
}
QComboBox#codecSelector:hover {
    border-color: #00D4FF;
}
QComboBox#codecSelector::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background: #131824;
    border: 1px solid #2A3A5C;
    color: #CBD5E1;
    selection-background-color: #1E2D45;
}

/* ── Buttons ─────────────────────────── */
#browseBtn {
    background: transparent;
    border: 1px solid #2A3A5C;
    border-radius: 8px;
    color: #94A3B8;
    padding: 7px 18px;
    font-size: 12px;
}
#browseBtn:hover {
    border-color: #00D4FF;
    color: #00D4FF;
    background: rgba(0, 212, 255, 0.06);
}
#convertBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0099CC, stop:1 #7C3AED);
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 700;
    padding: 12px 32px;
    letter-spacing: 0.3px;
}
#convertBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00B8E6, stop:1 #9333EA);
}
#convertBtn:disabled {
    background: #1E2D45;
    color: #475569;
}
#cancelBtn {
    background: transparent;
    border: 1px solid #7F1D1D;
    border-radius: 8px;
    color: #F87171;
    padding: 7px 18px;
    font-size: 12px;
}
#cancelBtn:hover {
    background: rgba(248, 113, 113, 0.08);
}
#openFolderBtn {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid #059669;
    border-radius: 8px;
    color: #10B981;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}
#openFolderBtn:hover {
    background: rgba(16, 185, 129, 0.2);
}
#downloadFfmpegBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #D97706, stop:1 #B45309);
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
    padding: 11px 28px;
}
#downloadFfmpegBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #F59E0B, stop:1 #D97706);
}

/* ── Divider line ────────────────────── */
QFrame#divider {
    color: #1E2D45;
    background: #1E2D45;
    max-height: 1px;
}
"""


# ── Spec Panel widget ──────────────────────────────────────────────────────────
class SpecBadge(QWidget):
    """A small two-line spec badge: label on top, value below."""

    def __init__(self, label: str, value: str, parent=None):
        super().__init__(parent)
        self.setObjectName("specCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        lbl = QLabel(label.upper())
        lbl.setObjectName("specTitle")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val = QLabel(value)
        val.setObjectName("specValue")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl)
        layout.addWidget(val)


# ── Drop Zone widget ───────────────────────────────────────────────────────────
class DropZone(QWidget):
    """A drag-and-drop target that emits file_dropped when a video is dropped."""

    from PyQt6.QtCore import pyqtSignal as _sig
    file_dropped = _sig(str)

    SUPPORTED = {".mp4", ".mkv", ".avi", ".mov", ".wmv",
                 ".flv", ".webm", ".m4v", ".3gp", ".ts", ".m2ts"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        # Icon (unicode PSP controller emoji as fallback)
        self.iconLabel = QLabel("🎮")
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iconLabel.setStyleSheet("font-size: 48px; background: transparent;")

        self.hintLabel = QLabel("Drop your video here")
        self.hintLabel.setObjectName("dropHintLabel")
        self.hintLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subLabel = QLabel("or click Browse to select a file")
        self.subLabel.setObjectName("dropSubLabel")
        self.subLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.fileLabel = QLabel("")
        self.fileLabel.setObjectName("fileNameLabel")
        self.fileLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fileLabel.setWordWrap(True)
        self.fileLabel.hide()

        layout.addWidget(self.iconLabel)
        layout.addWidget(self.hintLabel)
        layout.addWidget(self.subLabel)
        layout.addWidget(self.fileLabel)

    def set_file(self, path: str):
        name = Path(path).name
        self.fileLabel.setText(f"📄  {name}")
        self.fileLabel.show()
        self.hintLabel.setText("File selected — ready to convert")
        self.subLabel.setText("Drop another file to replace")

    def reset(self):
        self.fileLabel.hide()
        self.hintLabel.setText("Drop your video here")
        self.subLabel.setText("or click Browse to select a file")

    # ── Drag events ────────────────────────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and Path(urls[0].toLocalFile()).suffix.lower() in self.SUPPORTED:
                self.setProperty("dragActive", "true")
                self.style().polish(self)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragActive", "false")
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragActive", "false")
        self.style().polish(self)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).suffix.lower() in self.SUPPORTED:
                self.file_dropped.emit(path)
                event.acceptProposedAction()


# ── Main Window ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PSP 3000 Video Converter")
        self.setFixedSize(860, 680)
        self.setAcceptDrops(True)

        self._input_path  = ""
        self._output_path = ""
        self._converter   = None

        self._build_ui()
        self._check_ffmpeg_on_startup()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # --- Header ---
        header = QHBoxLayout()
        titleCol = QVBoxLayout()
        titleCol.setSpacing(2)

        title = QLabel("PSP 3000  Video Converter")
        title.setObjectName("titleLabel")

        sub = QLabel("Convert any video to Sony PSP 3000 native format · 480 × 272 · H.264 · AAC")
        sub.setObjectName("subtitleLabel")

        titleCol.addWidget(title)
        titleCol.addWidget(sub)

        header.addLayout(titleCol)
        header.addStretch()

        # Browse button
        self.browseBtn = QPushButton("📂  Browse")
        self.browseBtn.setObjectName("browseBtn")
        self.browseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browseBtn.clicked.connect(self._browse_file)
        header.addWidget(self.browseBtn)

        root.addLayout(header)

        # --- Drop Zone ---
        self.dropZone = DropZone()
        self.dropZone.file_dropped.connect(self._on_file_selected)
        self.dropZone.setMinimumHeight(200)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 212, 255, 40))
        self.dropZone.setGraphicsEffect(shadow)

        root.addWidget(self.dropZone)

        # --- Spec row ---
        specRow = QHBoxLayout()
        specRow.setSpacing(8)
        specs = [
            ("Resolution", "480 × 272"),
            ("Codec", "H.264"),
            ("Profile", "Baseline 3.0"),
            ("Video", "768 kbps"),
            ("Audio", "AAC 128k"),
            ("FPS", "29.97"),
            ("Container", ".mp4"),
        ]
        for label, value in specs:
            badge = SpecBadge(label, value)
            specRow.addWidget(badge)
        root.addLayout(specRow)

        # --- Divider ---
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(divider)

        # --- Codec selector row ---
        codecRow = QHBoxLayout()
        codecLabel = QLabel("Codec:")
        codecLabel.setObjectName("subtitleLabel")
        codecLabel.setFixedWidth(54)

        self.codecSelector = QComboBox()
        self.codecSelector.setObjectName("codecSelector")
        self.codecSelector.setCursor(Qt.CursorShape.PointingHandCursor)
        for name in CODEC_PRESETS:
            self.codecSelector.addItem(name)

        codecHint = QLabel("Try MPEG-4 if H.264 shows 'Unsupported Data' on PSP")
        codecHint.setObjectName("subtitleLabel")

        codecRow.addWidget(codecLabel)
        codecRow.addWidget(self.codecSelector)
        codecRow.addSpacing(12)
        codecRow.addWidget(codecHint)
        codecRow.addStretch()
        root.addLayout(codecRow)

        # --- Output path row ---
        outputRow = QHBoxLayout()
        outputLabel = QLabel("Save to:")
        outputLabel.setObjectName("subtitleLabel")
        outputLabel.setFixedWidth(54)

        self.outputPathLabel = QLabel("Same folder as input file")
        self.outputPathLabel.setObjectName("subtitleLabel")
        self.outputPathLabel.setSizePolicy(QSizePolicy.Policy.Expanding,
                                           QSizePolicy.Policy.Preferred)

        self.changeOutputBtn = QPushButton("Change")
        self.changeOutputBtn.setObjectName("browseBtn")
        self.changeOutputBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.changeOutputBtn.clicked.connect(self._choose_output_folder)

        outputRow.addWidget(outputLabel)
        outputRow.addWidget(self.outputPathLabel)
        outputRow.addWidget(self.changeOutputBtn)
        root.addLayout(outputRow)

        # --- Progress bar ---
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setFixedHeight(8)
        self.progressBar.hide()
        root.addWidget(self.progressBar)

        # --- Status label ---
        self.statusLabel = QLabel("")
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.hide()
        root.addWidget(self.statusLabel)

        # --- Diagnostic label (ffprobe PSP-3000 compliance table) ---
        self.diagLabel = QLabel("")
        self.diagLabel.setObjectName("subtitleLabel")
        self.diagLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.diagLabel.setTextFormat(Qt.TextFormat.RichText)
        self.diagLabel.setWordWrap(True)
        self.diagLabel.hide()
        root.addWidget(self.diagLabel)

        # --- Bottom action row ---
        actionRow = QHBoxLayout()
        actionRow.setSpacing(10)

        self.openFolderBtn = QPushButton("📁  Open Output Folder")
        self.openFolderBtn.setObjectName("openFolderBtn")
        self.openFolderBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.openFolderBtn.clicked.connect(self._open_output_folder)
        self.openFolderBtn.hide()

        self.cancelBtn = QPushButton("✕  Cancel")
        self.cancelBtn.setObjectName("cancelBtn")
        self.cancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancelBtn.clicked.connect(self._cancel_conversion)
        self.cancelBtn.hide()

        actionRow.addWidget(self.openFolderBtn)
        actionRow.addStretch()
        actionRow.addWidget(self.cancelBtn)

        self.convertBtn = QPushButton("▶  Convert to PSP Format")
        self.convertBtn.setObjectName("convertBtn")
        self.convertBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convertBtn.setEnabled(False)
        self.convertBtn.setFixedHeight(46)
        self.convertBtn.clicked.connect(self._start_conversion)

        root.addLayout(actionRow)
        root.addWidget(self.convertBtn)

        # --- FFmpeg warning panel (shown if FFmpeg missing) ---
        self.ffmpegPanel = QWidget()
        ffmpegLayout = QVBoxLayout(self.ffmpegPanel)
        ffmpegLayout.setContentsMargins(0, 0, 0, 0)
        ffmpegLayout.setSpacing(8)

        ffmpegWarn = QLabel("⚠️  FFmpeg not found — required for video conversion")
        ffmpegWarn.setObjectName("statusLabelError")
        ffmpegWarn.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ffmpegSub = QLabel("Click below to download the FFmpeg engine automatically (≈ 40 MB).")
        ffmpegSub.setObjectName("subtitleLabel")
        ffmpegSub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.downloadFfmpegBtn = QPushButton("⬇  Download FFmpeg (required)")
        self.downloadFfmpegBtn.setObjectName("downloadFfmpegBtn")
        self.downloadFfmpegBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.downloadFfmpegBtn.setFixedHeight(44)
        self.downloadFfmpegBtn.clicked.connect(self._download_ffmpeg)

        ffmpegLayout.addWidget(ffmpegWarn)
        ffmpegLayout.addWidget(ffmpegSub)
        ffmpegLayout.addWidget(self.downloadFfmpegBtn)

        self.ffmpegPanel.hide()
        root.addWidget(self.ffmpegPanel)

    # ── FFmpeg ─────────────────────────────────────────────────────────────────

    def _check_ffmpeg_on_startup(self):
        if not is_ffmpeg_available():
            self.convertBtn.hide()
            self.ffmpegPanel.show()

    def _download_ffmpeg(self):
        self.downloadFfmpegBtn.setEnabled(False)
        self.downloadFfmpegBtn.setText("⬇  Downloading FFmpeg…")
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.show()
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setText("Downloading FFmpeg engine…")
        self.statusLabel.show()

        def _progress(pct):
            self.progressBar.setValue(pct)

        def _done():
            self.progressBar.hide()
            self.ffmpegPanel.hide()
            self.convertBtn.show()
            self.statusLabel.setObjectName("statusLabelDone")
            self.statusLabel.setText("✅  FFmpeg downloaded successfully! Ready to convert.")
            self.statusLabel.show()
            self.style().polish(self.statusLabel)

        def _error(msg):
            self.progressBar.hide()
            self.downloadFfmpegBtn.setEnabled(True)
            self.downloadFfmpegBtn.setText("⬇  Download FFmpeg (required)")
            self.statusLabel.setObjectName("statusLabelError")
            self.statusLabel.setText(f"❌  Download failed: {msg}")
            self.statusLabel.show()
            self.style().polish(self.statusLabel)

        download_ffmpeg(
            progress_callback=lambda p: QTimer.singleShot(0, lambda: _progress(p)),
            done_callback=lambda: QTimer.singleShot(0, _done),
            error_callback=lambda m: QTimer.singleShot(0, lambda: _error(m)),
        )

    # ── File selection ─────────────────────────────────────────────────────────

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
        self.dropZone.set_file(path)
        self.convertBtn.setEnabled(True)
        self._reset_status()

        # Default output: same folder as input, with _PSP suffix
        in_p = Path(path)
        default_out = in_p.parent / f"{in_p.stem}_PSP.mp4"
        self._output_path = str(default_out)
        self.outputPathLabel.setText(str(in_p.parent))

    def _choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if folder and self._input_path:
            in_p = Path(self._input_path)
            self._output_path = str(Path(folder) / f"{in_p.stem}_PSP.mp4")
            self.outputPathLabel.setText(folder)

    # ── Conversion ─────────────────────────────────────────────────────────────

    def _start_conversion(self):
        if not self._input_path:
            return

        ffmpeg = ffmpeg_path()
        if not ffmpeg:
            QMessageBox.warning(self, "FFmpeg Missing",
                                "FFmpeg is not available. Please download it first.")
            return

        self.convertBtn.setEnabled(False)
        self.browseBtn.setEnabled(False)
        self.changeOutputBtn.setEnabled(False)
        self.progressBar.setValue(0)
        self.progressBar.show()
        self.cancelBtn.show()
        self.openFolderBtn.hide()
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setText("Starting conversion…")
        self.statusLabel.show()
        self.style().polish(self.statusLabel)

        selected_preset = self.codecSelector.currentText()
        flags = CODEC_PRESETS.get(selected_preset)
        self._converter = ConverterThread(ffmpeg, self._input_path, self._output_path, flags=flags)
        self._converter.progress.connect(self.progressBar.setValue)
        self._converter.status.connect(self._on_status)
        self._converter.finished.connect(self._on_finished)
        self._converter.error.connect(self._on_error)
        self._converter.start()

    def _cancel_conversion(self):
        if self._converter and self._converter.isRunning():
            self._converter.abort()
        self._reset_to_idle()

    # ── Slots ──────────────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_status(self, msg: str):
        self.statusLabel.setText(msg)

    @pyqtSlot(str)
    def _on_finished(self, output_path: str):
        self.progressBar.setValue(100)
        self.cancelBtn.hide()
        self.openFolderBtn.show()
        self.convertBtn.setEnabled(True)
        self.browseBtn.setEnabled(True)
        self.changeOutputBtn.setEnabled(True)
        self.statusLabel.setObjectName("statusLabelDone")
        self.statusLabel.setText(
            f"✅  Conversion complete!  →  {Path(output_path).name}"
        )
        self.style().polish(self.statusLabel)
        self._output_path = output_path
        # Run ffprobe to confirm container brand and show diagnostic
        self._run_ffprobe_check(output_path)

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        self.progressBar.hide()
        self.cancelBtn.hide()
        self.convertBtn.setEnabled(True)
        self.browseBtn.setEnabled(True)
        self.changeOutputBtn.setEnabled(True)
        self.statusLabel.setObjectName("statusLabelError")
        self.statusLabel.setText(f"❌  {msg}")
        self.style().polish(self.statusLabel)

    def _open_output_folder(self):
        folder = str(Path(self._output_path).parent)
        os.startfile(folder)

    def _run_ffprobe_check(self, output_path: str):
        """Run ffprobe and show full PSP-3000 compliance report."""
        import subprocess
        from psp_validator import validate
        probe = ffprobe_path()
        if not probe:
            self.diagLabel.setText(
                "⚠️  ffprobe not found — cannot validate output. "
                "Re-download FFmpeg to get ffprobe."
            )
            self.diagLabel.show()
            return

        try:
            report = validate(probe, output_path)
        except Exception as exc:
            self.diagLabel.setText(f"⚠️  Validation error: {exc}")
            self.diagLabel.show()
            return

        if report.ffprobe_error:
            self.diagLabel.setText(f"⚠️  ffprobe error: {report.ffprobe_error}")
            self.diagLabel.show()
            return

        # Build HTML table of results
        rows = []
        for c in report.checks:
            icon  = "✅" if c.passed else "❌"
            color = "#10B981" if c.passed else "#F87171"
            note  = f"<br><span style='color:#64748B;font-size:10px'>{c.note}</span>" if c.note else ""
            rows.append(
                f"<tr>"
                f"<td style='padding:2px 8px'>{icon}</td>"
                f"<td style='padding:2px 8px;color:#CBD5E1'>{c.name}</td>"
                f"<td style='padding:2px 8px;color:{color};font-weight:600'>{c.actual}</td>"
                f"<td style='padding:2px 8px;color:#475569'>{c.expected}{note}</td>"
                f"</tr>"
            )

        table = (
            "<table style='border-collapse:collapse;width:100%'>"
            "<tr style='color:#475569;font-size:10px'>"
            "<th></th><th align='left' style='padding:2px 8px'>Check</th>"
            "<th align='left' style='padding:2px 8px'>Actual</th>"
            "<th align='left' style='padding:2px 8px'>Expected</th>"
            "</tr>"
            + "".join(rows)
            + "</table>"
        )

        self.diagLabel.setText(table)
        self.diagLabel.show()

        # Update status line to reflect validation outcome
        if not report.all_passed:
            n = report.fail_count
            self.statusLabel.setObjectName("statusLabelError")
            self.statusLabel.setText(
                f"⚠️  Conversion done but {n} PSP-3000 compatibility "
                f"check{'s' if n != 1 else ''} failed — file may not play on PSP hardware."
            )
            self.style().polish(self.statusLabel)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _reset_status(self):
        self.statusLabel.hide()
        self.progressBar.hide()
        self.openFolderBtn.hide()
        self.cancelBtn.hide()
        self.diagLabel.hide()

    def _reset_to_idle(self):
        self.progressBar.hide()
        self.cancelBtn.hide()
        self.convertBtn.setEnabled(bool(self._input_path))
        self.browseBtn.setEnabled(True)
        self.changeOutputBtn.setEnabled(True)
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setText("Conversion cancelled.")
        self.statusLabel.show()
        self.style().polish(self.statusLabel)


def apply_stylesheet(app: QApplication):
    app.setStyleSheet(STYLESHEET)

