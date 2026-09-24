"""
ui/skin_widgets.py
Early-2000s Windows Media Player / Winamp / Xbox-Era Multimedia Console Skin Widgets (PyQt6)
Custom skeuomorphic controls with dark obsidian-green hardware, glowing lime green phosphor LCD,
glossy 3D beveled buttons, and segmented LED meters.
"""

from pathlib import Path
from PyQt6.QtCore import Qt, QRect, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient,
    QFont, QFontMetrics, QPaintEvent, QDragEnterEvent, QDropEvent
)
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout, QSizePolicy
)


# ── Color Palette (Early 2000s Dark Obsidian + Glowing Acid / Lime Green) ───────
CLR_CHASSIS_DARK      = QColor("#050D07")
CLR_CHASSIS_MID       = QColor("#0A180E")
CLR_CHASSIS_LIGHT     = QColor("#142A1A")
CLR_CHASSIS_BORDER    = QColor("#1E3F28")
CLR_CHASSIS_BEVEL_HI  = QColor("#2D5E3C")
CLR_CHASSIS_BEVEL_SH  = QColor("#020603")

CLR_LCD_BG            = QColor("#020703")
CLR_LCD_BEZEL_DARK    = QColor("#000000")
CLR_LCD_BEZEL_LIGHT   = QColor("#122A17")
CLR_LIME_BRIGHT       = QColor("#00FF66")   # Glowing lime green
CLR_LIME_MID          = QColor("#00CC52")
CLR_LIME_DIM          = QColor("#006629")
CLR_LIME_DARK         = QColor("#0A2A14")
CLR_LIME_GLOW         = QColor(0, 255, 102, 60)

CLR_TEXT_PRIMARY      = QColor("#E2F8E8")
CLR_TEXT_MUTED        = QColor("#5A8A68")
CLR_TEXT_AMBER        = QColor("#FFB000")
CLR_TEXT_RED          = QColor("#FF4040")


# ── 1. Main Console Chassis Frame ──────────────────────────────────────────────
class RetroConsoleFrame(QWidget):
    """
    Early-2000s Multimedia Console Body with dark metallic-green finish,
    molded edge bevels, glowing lime-green seam lines, and corner hex rivets.
    """

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        # 1. Main Chassis Dark Obsidian-Green Gradient
        bg_grad = QLinearGradient(0, 0, w, h)
        bg_grad.setColorAt(0.0, QColor("#09190D"))
        bg_grad.setColorAt(0.2, QColor("#051109"))
        bg_grad.setColorAt(0.7, QColor("#030A05"))
        bg_grad.setColorAt(1.0, QColor("#06140A"))

        rect = QRectF(2, 2, w - 4, h - 4)
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(rect, 16, 16)

        # 2. Outer Beveled Metallic Highlight Line
        painter.setPen(QPen(CLR_CHASSIS_BEVEL_HI, 1.5))
        painter.drawRoundedRect(QRectF(3, 3, w - 6, h - 6), 15, 15)

        # 3. Inner Glowing Seam Accent Contour
        painter.setPen(QPen(QColor(0, 255, 102, 35), 1))
        painter.drawRoundedRect(QRectF(7, 7, w - 14, h - 14), 12, 12)

        # 4. Top Ventilation / Speaker Grille Accent lines
        painter.setPen(QPen(QColor(0, 255, 102, 20), 1))
        mid_x = w / 2
        for i in range(-6, 7):
            gx = mid_x + (i * 12)
            painter.drawLine(int(gx), 8, int(gx + 6), 14)

        # 5. Corner Hardware Hex Screws
        screws = [(16, 16), (w - 16, 16), (16, h - 16), (w - 16, h - 16)]
        for sx, sy in screws:
            # Screw body
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.setBrush(QBrush(QColor("#0E2214")))
            painter.drawEllipse(QRectF(sx - 5, sy - 5, 10, 10))
            # Green hex ring
            painter.setPen(QPen(QColor(0, 255, 102, 120), 1))
            painter.drawEllipse(QRectF(sx - 3, sy - 3, 6, 6))
            # Center slot
            painter.setPen(QPen(QColor("#00FF66"), 1))
            painter.drawLine(sx - 2, sy, sx + 2, sy)


# ── 2. Phosphor LCD Display Screen with CRT Scanlines & Digital Telemetry ───────
class PhosphorLCDScreen(QWidget):
    """
    Early-2000s Green Phosphor LCD screen with scanline grid,
    glowing digital text readouts, and detailed stream telemetry.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._mode = "idle"  # "idle", "loaded", "converting", "done", "error"
        self._title = "SYSTEM STANDBY"
        self._lines: list[tuple[str, str, str]] = []
        self._status_text = "INSERT MEDIA · DROP VIDEO FILE TO LOAD"
        self._progress_pct = 0
        self._elapsed_str = "00:00:00"
        self._timer_sec = 0

    def set_idle(self):
        self._mode = "idle"
        self._title = "MEDIA PLAYER STANDBY"
        self._status_text = "READY FOR MEDIA INPUT · DROP FILE OR CLICK [ LOAD MEDIA ]"
        self._lines = [
            ("TARGET DEVICE", "SONY PSP-3000 (FIRMWARE 6.XX COMPLIANT)", "lime"),
            ("VIDEO ENCODER", "AVC / H.264 CONSTRAINED BASELINE 4.0 · 480x272", "text"),
            ("ASPECT RATIO", "AUTO-FIT LETTERBOX / PILLARBOX · FORCE SAR 1:1", "text"),
            ("AUDIO ENCODER", "AAC-LC STEREO · 48,000 HZ · 160 KBPS", "text"),
            ("CONTAINER MUX", "MP42 (FASTSTART MOOV) · NO BROKEN TRACKS", "dim"),
        ]
        self.update()

    def set_file_info(self, file_name: str, video_info: str, audio_info: str, dur_info: str, size_info: str):
        self._mode = "loaded"
        self._title = "MEDIA LOADED · TRANSCODE READY"
        self._status_text = "PRESS [ ▶ CONVERT TO PSP ] TO BEGIN TRANSCODE"
        self._lines = [
            ("SOURCE FILE", file_name, "lime"),
            ("INPUT VIDEO", video_info, "text"),
            ("INPUT AUDIO", audio_info, "text"),
            ("DURATION / SIZE", f"{dur_info} · {size_info}", "text"),
            ("OUTPUT TARGET", "480x272 · H.264 BASELINE 4.0 · AAC-LC 48kHz (PSP NATIVE)", "highlight"),
        ]
        self.update()

    def set_converting(self, pct: int, status_msg: str):
        self._mode = "converting"
        self._progress_pct = pct
        self._title = f"ENCODING IN PROGRESS [ {pct:02d}% ]"
        self._status_text = status_msg.upper()
        self.update()

    def set_done(self, output_file: str):
        self._mode = "done"
        self._progress_pct = 100
        self._title = "TRANSCODE COMPLETE · 100% PSP COMPLIANT"
        self._status_text = f"SAVED: {Path(output_file).name} (READY FOR MEMORY STICK)"
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

        # 1. Recessed Deep Black-Green LCD Background
        painter.setPen(QPen(CLR_LCD_BEZEL_DARK, 2))
        painter.setBrush(QBrush(CLR_LCD_BG))
        rect_outer = QRectF(2, 2, w - 4, h - 4)
        painter.drawRoundedRect(rect_outer, 8, 8)

        # 2. Inner Bevel Highlight
        painter.setPen(QPen(CLR_LCD_BEZEL_LIGHT, 1.5))
        painter.drawRoundedRect(QRectF(3, 3, w - 6, h - 6), 7, 7)

        # 3. Horizontal Phosphor CRT Scanlines
        painter.setPen(QPen(QColor(0, 255, 102, 10), 1))
        for y in range(8, h - 8, 3):
            painter.drawLine(8, y, w - 8, y)

        # 4. Top Glass Gloss / Reflection Curve
        glass_grad = QLinearGradient(0, 0, 0, h * 0.4)
        glass_grad.setColorAt(0.0, QColor(0, 255, 102, 28))
        glass_grad.setColorAt(0.4, QColor(0, 255, 102, 8))
        glass_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(QRect(4, 4, w - 8, int(h * 0.4)), QBrush(glass_grad))

        # 5. Header Separator Bar
        header_y = 26
        painter.setPen(QPen(CLR_LIME_DARK, 1))
        painter.drawLine(14, header_y + 4, w - 14, header_y + 4)

        # Header Title
        font_header = QFont("Lucida Console", 9, QFont.Weight.Bold)
        if not font_header.exactMatch():
            font_header = QFont("Consolas", 9, QFont.Weight.Bold)
        painter.setFont(font_header)

        if self._mode == "done":
            title_clr = CLR_LIME_BRIGHT
        elif self._mode == "error":
            title_clr = CLR_TEXT_RED
        elif self._mode == "converting":
            title_clr = CLR_LIME_BRIGHT
        elif self._mode == "loaded":
            title_clr = CLR_LIME_BRIGHT
        else:
            title_clr = CLR_LIME_MID

        painter.setPen(title_clr)
        painter.drawText(16, 20, f"■ {self._title}")

        # Top-right codec tag badges
        font_mono_small = QFont("Lucida Console", 8)
        if not font_mono_small.exactMatch():
            font_mono_small = QFont("Consolas", 8)
        painter.setFont(font_mono_small)
        painter.setPen(CLR_LIME_DIM)
        painter.drawText(w - 210, 20, "PSP-3000 AVC/AAC ENGINE")

        # 6. LCD Body Content
        curr_y = 48
        font_label = QFont("Lucida Console", 8, QFont.Weight.Bold)
        if not font_label.exactMatch():
            font_label = QFont("Consolas", 8, QFont.Weight.Bold)

        font_val = QFont("Lucida Console", 8)
        if not font_val.exactMatch():
            font_val = QFont("Consolas", 8)

        if self._mode in ("idle", "loaded"):
            for label, value, clr_type in self._lines:
                # Label
                painter.setFont(font_label)
                painter.setPen(CLR_LIME_DIM)
                painter.drawText(18, curr_y, f"{label:<16}:")

                # Value
                painter.setFont(font_val)
                if clr_type == "lime":
                    painter.setPen(CLR_LIME_BRIGHT)
                elif clr_type == "highlight":
                    painter.setPen(QColor("#70FF9E"))
                elif clr_type == "dim":
                    painter.setPen(CLR_LIME_DIM)
                else:
                    painter.setPen(CLR_TEXT_PRIMARY)

                metrics = QFontMetrics(font_val)
                val_str = metrics.elidedText(value, Qt.TextElideMode.ElideRight, w - 170)
                painter.drawText(160, curr_y, val_str)
                curr_y += 24

        elif self._mode == "converting":
            painter.setFont(font_label)
            painter.setPen(CLR_LIME_BRIGHT)
            painter.drawText(18, curr_y, "DSP CORE 01 : ENCODING VIDEO (libx264 Constrained Baseline 4.0)")
            curr_y += 22
            painter.setPen(CLR_LIME_MID)
            painter.drawText(18, curr_y, "DSP CORE 02 : ENCODING AUDIO (AAC-LC 48000Hz 160k Stereo)")
            curr_y += 22
            painter.setPen(CLR_TEXT_PRIMARY)
            painter.drawText(18, curr_y, "BITSTREAM   : Geometry 480x272 · SAR=1:1 · DAR=30:17 · VBV 768k")
            curr_y += 22
            painter.setPen(CLR_LIME_BRIGHT)
            painter.drawText(18, curr_y, f"CONTAINER   : MUXING MP42 CONTAINER ATOMS · {self._progress_pct}%")
            curr_y += 22

        elif self._mode == "done":
            painter.setFont(font_label)
            painter.setPen(CLR_LIME_BRIGHT)
            painter.drawText(18, curr_y, "✓ CONTAINER  : MP4 (major_brand=mp42, compatible=mp42iso2avc1)")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ VIDEO      : H.264 AVC (Constrained Baseline L4.0 · 480x272 · 29.97fps)")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ GEOMETRY   : Square Pixels (SAR 1:1) · Widescreen (DAR 30:17)")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ AUDIO      : AAC-LC Stereo · 48,000 Hz · 160 kbps")
            curr_y += 20
            painter.drawText(18, curr_y, "✓ HARDWARE   : 100% READY FOR SONY PSP MEMORY STICK PLAYBACK")
            curr_y += 20

        elif self._mode == "error":
            painter.setFont(font_label)
            painter.setPen(CLR_TEXT_RED)
            painter.drawText(18, curr_y, "CONVERSION FAILED:")
            curr_y += 24
            painter.setFont(font_val)
            painter.setPen(CLR_TEXT_PRIMARY)
            metrics = QFontMetrics(font_val)
            err_str = metrics.elidedText(self._status_text, Qt.TextElideMode.ElideRight, w - 36)
            painter.drawText(18, curr_y, err_str)

        # 7. Bottom Status line
        status_bar_y = h - 28
        painter.setPen(QPen(CLR_LIME_DARK, 1))
        painter.drawLine(14, status_bar_y, w - 14, status_bar_y)

        painter.setFont(font_mono_small)
        painter.setPen(CLR_LIME_BRIGHT if self._mode != "error" else CLR_TEXT_RED)
        painter.drawText(18, h - 12, f"▶ {self._status_text}")


# ── 3. Early 2000s Segmented Lime-Green LED Progress Meter ─────────────────────
class SegmentedLedMeter(QWidget):
    """
    Segmented illuminated LED progress bar with individual glowing lime green blocks.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
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

        # Inset Dark Beveled Frame
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.setBrush(QBrush(QColor("#040C06")))
        painter.drawRect(0, 0, w - 1, h - 1)

        painter.setPen(QPen(QColor(0, 255, 102, 40), 1))
        painter.drawLine(1, h - 1, w - 1, h - 1)
        painter.drawLine(w - 1, 1, w - 1, h - 1)

        # Draw LED Segments
        seg_width = 8
        seg_gap = 2
        pad_x = 4
        pad_y = 3
        avail_w = w - (pad_x * 2)
        total_segs = max(1, avail_w // (seg_width + seg_gap))
        active_segs = int((self._value / 100.0) * total_segs)
        seg_h = h - (pad_y * 2)

        for i in range(total_segs):
            x = pad_x + i * (seg_width + seg_gap)
            is_active = i < active_segs

            if is_active:
                # Glowing Lime Green LED
                frac = i / total_segs
                if frac < 0.8:
                    seg_clr = QColor("#00FF66")
                elif frac < 0.95:
                    seg_clr = QColor("#39FF14")
                else:
                    seg_clr = QColor("#FFD700")

                painter.setPen(QPen(seg_clr.darker(140), 1))
                painter.setBrush(QBrush(seg_clr))
                painter.drawRect(x, pad_y, seg_width, seg_h)

                # Segment top gloss highlight
                painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
                painter.drawLine(x + 1, pad_y + 1, x + seg_width - 1, pad_y + 1)
            else:
                # Unlit dim segment
                painter.setPen(QPen(QColor("#081A0D"), 1))
                painter.setBrush(QBrush(QColor("#06140A")))
                painter.drawRect(x, pad_y, seg_width, seg_h)


# ── 4. Skeuomorphic 2000s Multimedia Push Button ──────────────────────────────
class SkeuomorphicButton(QPushButton):
    """
    Physical early-2000s multimedia console button with glossy gradient,
    3D raised bevel, lime green edge glow, and tactile pressed feedback.
    """

    def __init__(self, text: str, is_hero: bool = False, parent=None):
        super().__init__(text, parent)
        self.is_hero = is_hero
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.setMinimumHeight(36 if not is_hero else 50)

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
            # ── Large Hero "CONVERT TO PSP" Action Button ──────────────────────
            # Outer dark metallic frame
            rim_grad = QLinearGradient(0, 0, 0, h)
            if pressed:
                rim_grad.setColorAt(0.0, QColor("#020603"))
                rim_grad.setColorAt(1.0, QColor("#142A1A"))
            else:
                rim_grad.setColorAt(0.0, QColor("#1E3F28"))
                rim_grad.setColorAt(0.5, QColor("#0E2214"))
                rim_grad.setColorAt(1.0, QColor("#040C06"))

            painter.setPen(QPen(QColor(0, 255, 102, 100 if hover else 60), 1.5))
            painter.setBrush(QBrush(rim_grad))
            painter.drawRoundedRect(rect, 8, 8)

            # Inner glossy green power dome
            inner_rect = QRectF(4 + offset, 4 + offset, w - 8, h - 8)
            green_grad = QLinearGradient(0, 4, 0, h - 4)

            if not enabled:
                green_grad.setColorAt(0.0, QColor("#142218"))
                green_grad.setColorAt(1.0, QColor("#0A140E"))
                text_color = QColor("#3A5E44")
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
            painter.drawRoundedRect(inner_rect, 6, 6)

            # Top gloss highlight curve
            if enabled and not pressed:
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1))
                painter.drawLine(int(inner_rect.left() + 4), int(inner_rect.top() + 2),
                                 int(inner_rect.right() - 4), int(inner_rect.top() + 2))

            # Hardware corner accents on hero button
            painter.setPen(QPen(QColor("#00FF66"), 1))
            painter.setBrush(QBrush(QColor("#040C06")))
            for rx, ry in [(8, 8), (w - 8, 8), (8, h - 8), (w - 8, h - 8)]:
                painter.drawEllipse(QRectF(rx - 2, ry - 2, 4, 4))

        else:
            # ── Standard Metallic / Dark Green Console Push Button ─────────────
            btn_grad = QLinearGradient(0, 0, 0, h)
            if not enabled:
                btn_grad.setColorAt(0.0, QColor("#0E1A12"))
                btn_grad.setColorAt(1.0, QColor("#08100A"))
                text_color = QColor("#2E4836")
                border_clr = QColor("#122216")
            elif pressed:
                btn_grad.setColorAt(0.0, QColor("#030804"))
                btn_grad.setColorAt(0.4, QColor("#0A180E"))
                btn_grad.setColorAt(1.0, QColor("#142A1A"))
                text_color = QColor("#00FF66")
                border_clr = QColor("#00FF66")
            elif hover:
                btn_grad.setColorAt(0.0, QColor("#1E3F28"))
                btn_grad.setColorAt(0.2, QColor("#142A1A"))
                btn_grad.setColorAt(0.7, QColor("#0A180E"))
                btn_grad.setColorAt(1.0, QColor("#050D07"))
                text_color = QColor("#00FF66")
                border_clr = QColor("#00FF66")
            else:
                btn_grad.setColorAt(0.0, QColor("#163220"))
                btn_grad.setColorAt(0.15, QColor("#0E2214"))
                btn_grad.setColorAt(0.6, QColor("#08160D"))
                btn_grad.setColorAt(1.0, QColor("#040B06"))
                text_color = QColor("#CBE8D2")
                border_clr = QColor("#1E3F28")

            painter.setPen(QPen(border_clr, 1))
            painter.setBrush(QBrush(btn_grad))
            painter.drawRoundedRect(rect, 5, 5)

            # Top highlight edge
            if not pressed and enabled:
                painter.setPen(QPen(QColor(0, 255, 102, 60), 1))
                painter.drawLine(3, 2, int(w - 4), 2)
                painter.drawLine(2, 3, 2, int(h - 4))

        # Render Button Text with 3D Shadow
        painter.setFont(self.font())
        if not pressed and enabled:
            painter.setPen(QColor(0, 0, 0, 200))
            painter.drawText(QRect(offset, offset + 1, w, h), Qt.AlignmentFlag.AlignCenter, self.text())

        painter.setPen(text_color)
        painter.drawText(QRect(offset, offset, w, h), Qt.AlignmentFlag.AlignCenter, self.text())


# ── 5. Recessed Inset Panel with Illuminated Header ───────────────────────────
class RetroInsetPanel(QFrame):
    """
    Recessed console panel with beveled dark green borders and silk-screened title.
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self.setContentsMargins(10, 18 if title else 8, 10, 8)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        top_offset = 8 if self._title else 2
        rect = QRectF(2, top_offset, w - 4, h - top_offset - 2)

        # Inset dark gradient
        panel_grad = QLinearGradient(0, top_offset, 0, h)
        panel_grad.setColorAt(0.0, QColor("#030804"))
        panel_grad.setColorAt(0.4, QColor("#061208"))
        panel_grad.setColorAt(1.0, QColor("#0A1E0E"))

        painter.setPen(QPen(QColor("#142E1B"), 1))
        painter.setBrush(QBrush(panel_grad))
        painter.drawRoundedRect(rect, 6, 6)

        # Inner top-left shadow
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.drawLine(4, top_offset + 2, int(w - 5), top_offset + 2)
        painter.drawLine(3, top_offset + 3, 3, int(h - 4))

        # Title Badge
        if self._title:
            font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font)
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(self._title) + 14

            title_rect = QRectF(12, 1, tw, 14)
            painter.setPen(QPen(QColor("#1E3F28"), 1))
            painter.setBrush(QBrush(QColor("#061208")))
            painter.drawRoundedRect(title_rect, 3, 3)

            painter.setPen(CLR_LIME_MID)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self._title)


# ── 6. Compact Media Source Slot / Tray (Drop Zone) ───────────────────────────
class CompactMediaTray(QWidget):
    """
    Compact optical/memory media tray styled drop zone with glowing intake slot.
    """

    file_dropped = pyqtSignal(str)
    SUPPORTED = {".mp4", ".mkv", ".avi", ".mov", ".wmv",
                 ".flv", ".webm", ".m4v", ".3gp", ".ts", ".m2ts"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(58)
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
            bg_grad.setColorAt(0.0, QColor("#0A2A14"))
            bg_grad.setColorAt(1.0, QColor("#041408"))
            border_pen = QPen(CLR_LIME_BRIGHT, 1.5, Qt.PenStyle.DashLine)
        else:
            bg_grad.setColorAt(0.0, QColor("#040C06"))
            bg_grad.setColorAt(0.5, QColor("#020603"))
            bg_grad.setColorAt(1.0, QColor("#06140A"))
            border_pen = QPen(QColor("#142E1B"), 1)

        painter.setPen(border_pen)
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(slot_rect, 6, 6)

        # Slot Intake Lines
        painter.setPen(QPen(QColor(0, 0, 0, 240), 2))
        painter.drawLine(8, 8, int(w - 8), 8)
        painter.setPen(QPen(QColor(0, 255, 102, 30), 1))
        painter.drawLine(8, int(h - 8), int(w - 8), int(h - 8))

        # Media Text
        font = QFont("Lucida Console", 8, QFont.Weight.Bold)
        if not font.exactMatch():
            font = QFont("Consolas", 8, QFont.Weight.Bold)
        painter.setFont(font)

        if self._file_name:
            painter.setPen(CLR_LIME_BRIGHT)
            text = f"▶ LOADED MEDIA: [ {self._file_name} ]  (DROP NEW FILE TO REPLACE)"
        else:
            painter.setPen(CLR_LIME_BRIGHT if self._hover else CLR_TEXT_MUTED)
            text = "⏏ MEDIA TRAY · DROP VIDEO FILE HERE OR CLICK [ SELECT VIDEO ]"

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
