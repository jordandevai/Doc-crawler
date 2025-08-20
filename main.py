#!/usr/bin/env python3
"""
Doc-Crawler Application Entry Point.

Initializes and runs the PyQt6 application, setting up the main window.
"""
import sys
from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main():
    """Initializes the Qt application and the main window."""
    app = QApplication(sys.argv)

    app.setApplicationName("Doc-Crawler")
    app.setApplicationVersion("1.1.0")
    app.setOrganizationName("Doc-Crawler")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()