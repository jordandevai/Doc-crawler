#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def check_dependencies():
    missing_deps = []
    
    try:
        import PyQt6
    except ImportError:
        missing_deps.append('PyQt6')
    
    try:
        import httpx
    except ImportError:
        missing_deps.append('httpx')
    
    try:
        import bs4
    except ImportError:
        missing_deps.append('beautifulsoup4')
    
    try:
        import lxml
    except ImportError:
        missing_deps.append('lxml')
    
    try:
        import markdownify
    except ImportError:
        missing_deps.append('markdownify')
    
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install them using:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def main():
    if not check_dependencies():
        sys.exit(1)
    
    app = QApplication(sys.argv)
    
    app.setApplicationName("Web Crawler")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Doc-Crawler")
    
    try:
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()