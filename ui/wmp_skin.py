"""
ui/wmp_skin.py
Windows Media Player 9 Series ("Corona") Custom Multimedia Skin Components (PyQt6)
Authentic 2003 WMP9 / Winamp skeuomorphic aesthetics: dark obsidian-green chassis,
phosphor LCD viewport, transport buttons, segmented seek bar, and custom-skinned window chrome.
"""

from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient,
    QFont, QFontMetrics, QPaintEvent, QMouseEvent, QDragEnterEvent, QDropEvent
)
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout, QSizePolicy
)


# ── WMP9 Color Palette ────────────────────────────────────────────────────────
CLR_WMP_BG            = QColor("#08110B")
CLR_WMP_DARK          = QColor("#040805")
CLR_WMP_MID           = QColor("#0E1C12")
CLR_WMP_BORDER_LIGHT  = QColor("#22442C")
CLR_WMP_BORDER_DARK   = QColor("#020503")
CLR_WMP_HIGHLIGHT     = QColor("#3D7A50")

CLR_WMP_LCD_BG        = QColor("#020603")
CLR_WMP_LCD_BORDER    = QColor("#142A1A")
CLR_WMP_GREEN_LIME    = QColor("#00FF66")
CLR_WMP_GREEN_BRIGHT  = QColor("#39FF14")
CLR_WMP_GREEN_MID     = QColor("#00CC52")
CLR_WMP_GREEN_DIM     = QColor("#005C24")
CLR_WMP_TEXT          = QColor("#D8F4E0")
CLR_WMP_MUTED         = QColor("#4E7E5A")
CLR_WMP_AMBER         = QColor("#FFB800")
CLR_WMP_RED           = QColor("#FF3B3B")


# ── 1. WMP9 Skinned Custom Title Bar ───────────────────────────────────────────
class WmpTitleBar(QWidget):
    """
    Skinned WMP9 top title bar with window drag handle,
    early-2000s branding badge, and custom minimize/close buttons.
    """

    minimize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, title_text: str = "PSP VIDEO CONVERTER // WMP-9 SERIES", parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self._title = title_text
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 8, 2)
        layout.setSpacing(6)

        # Title Icon / Branding
        self.iconLabel = QLabel("▶")
        self.iconLabel.setStyleSheet("color: #00FF66; font-size: 10px; font-weight: bold;")
        self.titleLabel = QLabel(self._title)
        self.titleLabel.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        self.titleLabel.setStyleSheet("color: #D8F4E0; letter-spacing: 1px;")

        layout.addWidget(self.iconLabel)
        layout.addWidget(self.titleLabel)
        layout.addStretch()

        # Custom Window Control Buttons
        self.minBtn = WmpWindowButton(" _ ", parent=self)
        self.minBtn.clicked.connect(self.minimize_clicked.emit)
        self.closeBtn = WmpWindowButton(" ✕ ", is_close=True, parent=self)
        self.closeBtn.clicked.connect(self.close_clicked.emit)

        layout.addWidget(self.minBtn)
        layout.addWidget(self.closeBtn)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        # Top Bar Dark Metallic Green Gradient
        bar_grad = QLinearGradient(0, 0, 0, h)
        bar_grad.setColorAt(0.0, QColor("#1C3824"))
        bar_grad.setColorAt(0.2, QColor("#122417"))
        bar_grad.setColorAt(0.8, QColor("#09140C"))
        bar_grad.setColorAt(1.0, QColor("#050A06"))

        painter.fillRect(0, 0, w, h, QBrush(bar_grad))

        # Top & Bottom Bevel Edge Lines
        painter.setPen(QPen(QColor(0, 255, 102, 70), 1))
        painter.drawLine(0, 0, w, 0)
        painter.setPen(QPen(QColor(0, 0, 0, 220), 1))
        painter.drawLine(0, h - 1, w, h - 1)


class WmpWindowButton(QPushButton):
    """Small glossy titlebar minimize/close button."""

    def __init__(self, text: str, is_close: bool = False, parent=None):
        super().__init__(text, parent)
        self.is_close = is_close
        self.setFixedSize(22, 18)
        self.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        pressed = self.isDown()
        hover = self.underMouse()

        rect = QRectF(1, 1, w - 2, h - 2)
        grad = QLinearGradient(0, 0, 0, h)

        if self.is_close:
            if pressed:
                grad.setColorAt(0.0, QColor("#801010"))
                grad.setColorAt(1.0, QColor("#B02020"))
                txt_clr = QColor("#FFFFFF")
            elif hover:
                grad.setColorAt(0.0, QColor("#E03030"))
                grad.setColorAt(1.0, QColor("#901818"))
                txt_clr = QColor("#FFFFFF")
            else:
                grad.setColorAt(0.0, QColor("#401818"))
                grad.setColorAt(1.0, QColor("#240C0C"))
                txt_clr = QColor("#D8A0A0")
        else:
            if pressed:
                grad.setColorAt(0.0, QColor("#040C06"))
                grad.setColorAt(1.0, QColor("#142A1A"))
                txt_clr = QColor("#00FF66")
            elif hover:
                grad.setColorAt(0.0, QColor("#1E4028"))
                grad.setColorAt(1.0, QColor("#0E2014"))
                txt_clr = QColor("#00FF66")
            else:
                grad.setColorAt(0.0, QColor("#142A1A"))
                grad.setColorAt(1.0, QColor("#08120A"))
                txt_clr = QColor("#A0D8B0")

        painter.setPen(QPen(QColor(0, 0, 0, 180), 1))
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(rect, 3, 3)

        painter.setFont(self.font())
        painter.setPen(txt_clr)
        painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.text())


# ── 2. WMP9 Skinned Main Frame ────────────────────────────────────────────────
class WmpSkinFrame(QWidget):
    """
    Main background chassis with WMP9 metallic rounded contour,
    deep green highlights, and beveled outer frame.
    """

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        # Outer Shadow & Border
        bg_grad = QLinearGradient(0, 0, w, h)
        bg_grad.setColorAt(0.0, QColor("#0C1A10"))
        bg_grad.setColorAt(0.3, QColor("#07120B"))
        bg_grad.setColorAt(0.8, QColor("#040905"))
        bg_grad.setColorAt(1.0, QColor("#08140C"))

        rect = QRectF(2, 2, w - 4, h - 4)
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(rect, 10, 10)

        # Highlight Inner Ridge
        painter.setPen(QPen(QColor(0, 255, 102, 45), 1.5))
        painter.drawRoundedRect(QRectF(3.5, 3.5, w - 7, h - 7), 9, 9)

        # Subtle Decorative Grippy on Left/Right corners
        painter.setPen(QPen(QColor(0, 255, 102, 30), 1))
        for gy in range(40, 90, 4):
            painter.drawLine(8, gy, 12, gy)
            painter.drawLine(int(w - 12), gy, int(w - 8), gy)


# ── 3. Embedded Phosphor LCD Display (Central Viewport) ────────────────────────
class WmpLcdDisplay(QWidget):
    """
    Recessed WMP9 LCD screen with scanline texture, glowing phosphor readout,
    digital timer clock, stream properties, and compliance status.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._mode = "idle"  # "idle", "loaded", "converting", "done", "error"
        self._title = "WINDOWS MEDIA PLAYER 9 // PSP ENGINE"
        self._lines: list[tuple[str, str, str]] = []
        self._status_text = "READY · DROP VIDEO FILE OR CLICK [ OPEN FILE ]"
        self._progress_pct = 0
        self._timer_val = "00:00:00"

    def set_idle(self):
        self._mode = "idle"
        self._title = "PSP VIDEO CONVERTER // WMP-9"
        self._status_text = "READY · INSERT MEDIA FILE TO BEGIN"
        self._timer_val = "00:00:00"
        self._lines = [
            ("TARGET DEVICE", "SONY PLAYSTATION PORTABLE (PSP-3000 / 2000 / E1000)", "lime"),
            ("VIDEO CODEC", "H.264 / AVC CONSTRAINED BASELINE 4.0 · 480 × 272", "text"),
            ("GEOMETRY", "SAMPLE ASPECT RATIO 1:1 · AUTO LETTERBOX / PILLARBOX", "text"),
            ("AUDIO CODEC", "AAC-LC STEREO · 48,000 HZ · 160 KBPS", "text"),
            ("CONTAINER", "MP42 ATOM MUXER + FASTSTART (MEMORY STICK READY)", "dim"),
        ]
        self.update()

    def set_file_info(self, file_name: str, video_info: str, audio_info: str, dur_info: str, size_info: str):
        self._mode = "loaded"
        self._title = "MEDIA LOADED // READY TO CONVERT"
        self._status_text = "CLICK [ ▶ CONVERT TO PSP ] TO START ENCODING"
        self._timer_val = dur_info
        self._lines = [
            ("SOURCE FILE", file_name, "lime"),
            ("VIDEO STREAM", video_info, "text"),
            ("AUDIO STREAM", audio_info, "text"),
            ("DURATION / SIZE", f"{dur_info} · {size_info}", "text"),
            ("TARGET SPEC", "480×272 · H.264 BASELINE 4.0 · AAC-LC 48kHz (PSP NATIVE)", "highlight"),
        ]
        self.update()

    def set_converting(self, pct: int, status_msg: str):
        self._mode = "converting"
        self._progress_pct = pct
        self._title = f"ENCODING MEDIA STREAM [ {pct:02d}% ]"
        self._status_text = status_msg.upper()
        self.update()

    def set_done(self, output_file: str):
        self._mode = "done"
        self._progress_pct = 100
        self._title = "CONVERSION COMPLETE // 100% PSP COMPLIANT"
        self._status_text = f"OUTPUT: {Path(output_file).name} (READY FOR PSP /VIDEO/ FOLDER)"
        self.update()

    def set_error(self, err_msg: str):
        self._mode = "error"
        self._title = "TRANSCODE ERROR"
        self._status_text = f"ERROR: {err_msg}"
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        # 1. Dark Recessed LCD Frame
        painter.setPen(QPen(CLR_WMP_BORDER_DARK, 2))
        painter.setBrush(QBrush(CLR_WMP_LCD_BG))
        rect_outer = QRectF(2, 2, w - 4, h - 4)
        painter.drawRoundedRect(rect_outer, 6, 6)

        # 2. Inset Bevel Edge
        painter.setPen(QPen(CLR_WMP_LCD_BORDER, 1.5))
        painter.drawRoundedRect(QRectF(3, 3, w - 6, h - 6), 5, 5)

        # 3. Horizontal Phosphor CRT Scanlines
        painter.setPen(QPen(QColor(0, 255, 102, 9), 1))
        for y in range(6, h - 6, 3):
            painter.drawLine(6, y, w - 6, y)

        # 4. Top Glass Gloss Reflection Curve
        glass_grad = QLinearGradient(0, 0, 0, h * 0.45)
        glass_grad.setColorAt(0.0, QColor(0, 255, 102, 22))
        glass_grad.setColorAt(0.5, QColor(0, 255, 102, 6))
        glass_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(QRect(4, 4, w - 8, int(h * 0.45)), QBrush(glass_grad))

        # 5. Header Separator Bar
        header_y = 26
        painter.setPen(QPen(QColor("#0E2214"), 1))
        painter.drawLine(12, header_y + 4, w - 12, header_y + 4)

        # Header Title
        font_header = QFont("Tahoma", 8, QFont.Weight.Bold)
        painter.setFont(font_header)

        if self._mode == "done":
            title_clr = CLR_WMP_GREEN_LIME
        elif self._mode == "error":
            title_clr = CLR_WMP_RED
        elif self._mode == "converting":
            title_clr = CLR_WMP_GREEN_LIME
        elif self._mode == "loaded":
            title_clr = CLR_WMP_GREEN_LIME
        else:
            title_clr = CLR_WMP_GREEN_MID

        painter.setPen(title_clr)
        painter.drawText(16, 20, f"■ {self._title}")

        # Top-right Digital Timer Clock
        font_timer = QFont("Lucida Console", 8, QFont.Weight.Bold)
        if not font_timer.exactMatch():
            font_timer = QFont("Consolas", 8, QFont.Weight.Bold)
        painter.setFont(font_timer)
        painter.setPen(CLR_WMP_GREEN_LIME if self._mode in ("loaded", "converting") else CLR_WMP_GREEN_DIM)
        painter.drawText(w - 190, 20, f"TIME: {self._timer_val}")

        # 6. LCD Body Telemetry Lines
        curr_y = 48
        font_label = QFont("Tahoma", 8, QFont.Weight.Bold)
        font_val = QFont("Lucida Console", 8)
        if not font_val.exactMatch():
            font_val = QFont("Consolas", 8)

        if self._mode in ("idle", "loaded"):
            for label, value, clr_type in self._lines:
                painter.setFont(font_label)
                painter.setPen(CLR_WMP_MUTED)
                painter.drawText(18, curr_y, f"{label:<16}:")

                painter.setFont(font_val)
                if clr_type == "lime":
                    painter.setPen(CLR_WMP_GREEN_LIME)
                elif clr_type == "highlight":
                    painter.setPen(QColor("#66FF99"))
                elif clr_type == "dim":
                    painter.setPen(CLR_WMP_GREEN_DIM)
                else:
                    painter.setPen(CLR_WMP_TEXT)

                metrics = QFontMetrics(font_val)
                val_str = metrics.elidedText(value, Qt.TextElideMode.ElideRight, w - 170)
                painter.drawText(160, curr_y, val_str)
                curr_y += 24

        elif self._mode == "converting":
            painter.setFont(font_label)
            painter.setPen(CLR_WMP_GREEN_LIME)
            painter.drawText(18, curr_y, "VIDEO DSP    : ENCODING (libx264 Constrained Baseline 4.0)")
            curr_y += 22
            painter.setPen(CLR_WMP_GREEN_MID)
            painter.drawText(18, curr_y, "AUDIO DSP    : ENCODING (AAC-LC Stereo 48000Hz 160k)")
            curr_y += 22
            painter.setPen(CLR_WMP_TEXT)
            painter.drawText(18, curr_y, "BITSTREAM    : 480×272 · SAR=1:1 · DAR=30:17 · VBV CAP 768k")
            curr_y += 22
            painter.setPen(CLR_WMP_GREEN_LIME)
            painter.drawText(18, curr_y, f"MUXER STATUS : GENERATING MP42 ATOMS (FASTSTART) · {self._progress_pct}%")
            curr_y += 22

        elif self._mode == "done":
            painter.setFont(font_label)
            painter.setPen(CLR_WMP_GREEN_LIME)
            painter.drawText(18, curr_y, "✓ CONTAINER  : MP4 (major_brand=mp42, compatible=mp42iso2avc1)")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ VIDEO      : H.264 AVC (Constrained Baseline L4.0 · 480×272)")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ GEOMETRY   : Square Pixels (SAR 1:1) · Widescreen (DAR 30:17)")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ AUDIO      : AAC-LC Stereo · 48,000 Hz · 160 kbps")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ HARDWARE   : 100% READY FOR SONY PSP-3000 PLAYBACK")
            curr_y += 20

        elif self._mode == "error":
            painter.setFont(font_label)
            painter.setPen(CLR_WMP_RED)
            painter.drawText(18, curr_y, "CONVERSION ERROR OCCURRED:")
            curr_y += 24
            painter.setFont(font_val)
            painter.setPen(CLR_WMP_TEXT)
            metrics = QFontMetrics(font_val)
            err_str = metrics.elidedText(self._status_text, Qt.TextElideMode.ElideRight, w - 36)
            painter.drawText(18, curr_y, err_str)

        # 7. Bottom Status Line
        status_bar_y = h - 28
        painter.setPen(QPen(QColor("#0E2214"), 1))
        painter.drawLine(12, status_bar_y, w - 12, status_bar_y)

        painter.setFont(font_timer)
        painter.setPen(CLR_WMP_GREEN_LIME if self._mode != "error" else CLR_WMP_RED)
        painter.drawText(18, h - 12, f"▶ {self._status_text}")


# ── 4. WMP9 Segmented Seek / Progress Bar ─────────────────────────────────────
class WmpProgressBar(QWidget):
    """
    WMP9-era segmented seek / progress track with glowing green fill blocks.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._value = 0

    def setValue(self, val: int):
        self._value = max(0, min(100, val))
        self.update()

    def value(self) -> int:
        return self._value

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        # Inset Track Frame
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.setBrush(QBrush(QColor("#030A05")))
        painter.drawRect(0, 0, w - 1, h - 1)

        painter.setPen(QPen(QColor(0, 255, 102, 35), 1))
        painter.drawLine(1, h - 1, w - 1, h - 1)
        painter.drawLine(w - 1, 1, w - 1, h - 1)

        # Draw Progress Segments
        seg_width = 7
        seg_gap = 2
        pad_x = 3
        pad_y = 2
        avail_w = w - (pad_x * 2)
        total_segs = max(1, avail_w // (seg_width + seg_gap))
        active_segs = int((self._value / 100.0) * total_segs)
        seg_h = h - (pad_y * 2)

        for i in range(total_segs):
            x = pad_x + i * (seg_width + seg_gap)
            is_active = i < active_segs

            if is_active:
                frac = i / total_segs
                seg_clr = QColor("#00FF66") if frac < 0.9 else QColor("#39FF14")

                painter.setPen(QPen(seg_clr.darker(140), 1))
                painter.setBrush(QBrush(seg_clr))
                painter.drawRect(x, pad_y, seg_width, seg_h)

                # Segment top gloss highlight
                painter.setPen(QPen(QColor(255, 255, 255, 160), 1))
                painter.drawLine(x + 1, pad_y + 1, x + seg_width - 1, pad_y + 1)
            else:
                painter.setPen(QPen(QColor("#061208"), 1))
                painter.setBrush(QBrush(QColor("#040D06")))
                painter.drawRect(x, pad_y, seg_width, seg_h)


# ── 5. WMP9 Transport Push Button (Skeuomorphic) ──────────────────────────────
class WmpTransportButton(QPushButton):
    """
    Skeuomorphic WMP9 transport control button with 3D raised bevel,
    metallic green gloss, and pressed state.
    """

    def __init__(self, text: str, is_hero: bool = False, parent=None):
        super().__init__(text, parent)
        self.is_hero = is_hero
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        self.setMinimumHeight(32 if not is_hero else 46)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        pressed = self.isDown()
        hover = self.underMouse()
        enabled = self.isEnabled()

        offset = 1 if pressed else 0
        rect = QRectF(1, 1, w - 2, h - 2)

        if self.is_hero:
            # ── Hero "CONVERT TO PSP" Action Control ──────────────────────────
            rim_grad = QLinearGradient(0, 0, 0, h)
            if pressed:
                rim_grad.setColorAt(0.0, QColor("#020503"))
                rim_grad.setColorAt(1.0, QColor("#122417"))
            else:
                rim_grad.setColorAt(0.0, QColor("#1E3F28"))
                rim_grad.setColorAt(0.5, QColor("#0E2214"))
                rim_grad.setColorAt(1.0, QColor("#040C06"))

            painter.setPen(QPen(QColor(0, 255, 102, 120 if hover else 70), 1.5))
            painter.setBrush(QBrush(rim_grad))
            painter.drawRoundedRect(rect, 7, 7)

            # Inner Dome Button
            inner_rect = QRectF(3 + offset, 3 + offset, w - 6, h - 6)
            green_grad = QLinearGradient(0, 3, 0, h - 3)

            if not enabled:
                green_grad.setColorAt(0.0, QColor("#122016"))
                green_grad.setColorAt(1.0, QColor("#08120B"))
                text_color = QColor("#33553C")
            elif pressed:
                green_grad.setColorAt(0.0, QColor("#004D1F"))
                green_grad.setColorAt(0.5, QColor("#008033"))
                green_grad.setColorAt(1.0, QColor("#00B347"))
                text_color = QColor("#FFFFFF")
            elif hover:
                green_grad.setColorAt(0.0, QColor("#00FF66"))
                green_grad.setColorAt(0.3, QColor("#00CC52"))
                green_grad.setColorAt(1.0, QColor("#006629"))
                text_color = QColor("#FFFFFF")
            else:
                green_grad.setColorAt(0.0, QColor("#00CC52"))
                green_grad.setColorAt(0.4, QColor("#00993D"))
                green_grad.setColorAt(1.0, QColor("#004D1F"))
                text_color = QColor("#FFFFFF")

            painter.setPen(QPen(QColor(0, 0, 0, 140), 1))
            painter.setBrush(QBrush(green_grad))
            painter.drawRoundedRect(inner_rect, 5, 5)

            # Top gloss highlight
            if enabled and not pressed:
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1))
                painter.drawLine(int(inner_rect.left() + 4), int(inner_rect.top() + 2),
                                 int(inner_rect.right() - 4), int(inner_rect.top() + 2))

        else:
            # ── Standard WMP9 Transport Push Button ────────────────────────────
            btn_grad = QLinearGradient(0, 0, 0, h)
            if not enabled:
                btn_grad.setColorAt(0.0, QColor("#0C160F"))
                btn_grad.setColorAt(1.0, QColor("#060C08"))
                text_color = QColor("#2A4432")
                border_clr = QColor("#102014")
            elif pressed:
                btn_grad.setColorAt(0.0, QColor("#020603"))
                btn_grad.setColorAt(0.4, QColor("#08140B"))
                btn_grad.setColorAt(1.0, QColor("#122417"))
                text_color = QColor("#00FF66")
                border_clr = QColor("#00FF66")
            elif hover:
                btn_grad.setColorAt(0.0, QColor("#1E3F28"))
                btn_grad.setColorAt(0.2, QColor("#122417"))
                btn_grad.setColorAt(0.7, QColor("#08140B"))
                btn_grad.setColorAt(1.0, QColor("#040A06"))
                text_color = QColor("#00FF66")
                border_clr = QColor("#00FF66")
            else:
                btn_grad.setColorAt(0.0, QColor("#163220"))
                btn_grad.setColorAt(0.15, QColor("#0E2014"))
                btn_grad.setColorAt(0.6, QColor("#07140B"))
                btn_grad.setColorAt(1.0, QColor("#030804"))
                text_color = QColor("#CBE8D2")
                border_clr = QColor("#1E3F28")

            painter.setPen(QPen(border_clr, 1))
            painter.setBrush(QBrush(btn_grad))
            painter.drawRoundedRect(rect, 4, 4)

            # Highlight edge
            if not pressed and enabled:
                painter.setPen(QPen(QColor(0, 255, 102, 50), 1))
                painter.drawLine(2, 2, int(w - 3), 2)
                painter.drawLine(2, 2, 2, int(h - 3))

        # Text Label
        painter.setFont(self.font())
        if not pressed and enabled:
            painter.setPen(QColor(0, 0, 0, 200))
            painter.drawText(QRect(offset, offset + 1, w, h), Qt.AlignmentFlag.AlignCenter, self.text())

        painter.setPen(text_color)
        painter.drawText(QRect(offset, offset, w, h), Qt.AlignmentFlag.AlignCenter, self.text())


# ── 6. WMP9 Recessed Information Panel ─────────────────────────────────────────
class WmpPanel(QFrame):
    """
    Recessed parameter panel with beveled dark borders and title badge.
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self.setContentsMargins(10, 16 if title else 6, 10, 6)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        top_offset = 7 if self._title else 2
        rect = QRectF(2, top_offset, w - 4, h - top_offset - 2)

        panel_grad = QLinearGradient(0, top_offset, 0, h)
        panel_grad.setColorAt(0.0, QColor("#020603"))
        panel_grad.setColorAt(0.4, QColor("#050F08"))
        panel_grad.setColorAt(1.0, QColor("#0A1C0E"))

        painter.setPen(QPen(QColor("#142E1B"), 1))
        painter.setBrush(QBrush(panel_grad))
        painter.drawRoundedRect(rect, 5, 5)

        # Title Badge
        if self._title:
            font = QFont("Tahoma", 7, QFont.Weight.Bold)
            painter.setFont(font)
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(self._title) + 12

            title_rect = QRectF(10, 1, tw, 13)
            painter.setPen(QPen(QColor("#1E3F28"), 1))
            painter.setBrush(QBrush(QColor("#050F08")))
            painter.drawRoundedRect(title_rect, 2, 2)

            painter.setPen(CLR_WMP_GREEN_MID)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self._title)


# ── 7. Compact WMP9 File Loading Tray ──────────────────────────────────────────
class WmpMediaTray(QWidget):
    """
    Compact WMP9 media tray slot supporting drag and drop.
    """

    file_dropped = pyqtSignal(str)
    SUPPORTED = {".mp4", ".mkv", ".avi", ".mov", ".wmv",
                 ".flv", ".webm", ".m4v", ".3gp", ".ts", ".m2ts"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._hover = False
        self._file_name = ""

    def set_file(self, path: str):
        self._file_name = Path(path).name
        self.update()

    def reset(self):
        self._file_name = ""
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        slot_rect = QRectF(2, 2, w - 4, h - 4)
        bg_grad = QLinearGradient(0, 0, 0, h)
        if self._hover:
            bg_grad.setColorAt(0.0, QColor("#0A2412"))
            bg_grad.setColorAt(1.0, QColor("#030E06"))
            border_pen = QPen(CLR_WMP_GREEN_LIME, 1.5, Qt.PenStyle.DashLine)
        else:
            bg_grad.setColorAt(0.0, QColor("#030A05"))
            bg_grad.setColorAt(0.5, QColor("#010402"))
            bg_grad.setColorAt(1.0, QColor("#050E07"))
            border_pen = QPen(QColor("#142E1B"), 1)

        painter.setPen(border_pen)
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(slot_rect, 5, 5)

        # Slot lines
        painter.setPen(QPen(QColor(0, 0, 0, 240), 2))
        painter.drawLine(8, 6, int(w - 8), 6)
        painter.setPen(QPen(QColor(0, 255, 102, 25), 1))
        painter.drawLine(8, int(h - 6), int(w - 8), int(h - 6))

        # Media Text
        font = QFont("Lucida Console", 8, QFont.Weight.Bold)
        if not font.exactMatch():
            font = QFont("Consolas", 8, QFont.Weight.Bold)
        painter.setFont(font)

        if self._file_name:
            painter.setPen(CLR_WMP_GREEN_LIME)
            text = f"▶ CURRENT MEDIA: [ {self._file_name} ]  (DROP NEW FILE TO REPLACE)"
        else:
            painter.setPen(CLR_WMP_GREEN_LIME if self._hover else CLR_WMP_MUTED)
            text = "⏏ MEDIA TRAY · DROP VIDEO FILE HERE OR CLICK [ OPEN FILE ]"

        painter.drawText(slot_rect, Qt.AlignmentFlag.AlignCenter, text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and Path(urls[0].toLocalFile()).suffix.lower() in self.SUPPORTED:
                self._hover = True
                self.update()
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._hover = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._hover = False
        self.update()
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).suffix.lower() in self.SUPPORTED:
                self.file_dropped.emit(path)
                event.acceptProposedAction()
