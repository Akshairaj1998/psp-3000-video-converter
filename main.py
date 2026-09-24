"""
main.py — PSP 3000 Video Converter
Entry point for the application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow, apply_stylesheet


def main():
    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PSP 3000 Video Converter")
    app.setOrganizationName("PSPConverter")
    app.setApplicationVersion("1.0.0")

    # Apply dark stylesheet
    apply_stylesheet(app)

    # Show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
