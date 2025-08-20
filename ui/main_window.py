import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox, 
                           QCheckBox, QProgressBar, QSplitter, QGroupBox, QGridLayout,
                           QMessageBox, QFileDialog, QStatusBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor
from workers.crawl_worker import CrawlWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.crawl_worker = None
        self.total_markdown_content = ""
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Web Crawler - Document Processor")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = self.create_control_panel()
        right_panel = self.create_output_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to crawl")
        
    def create_control_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        
        input_group = QGroupBox("Crawl Configuration")
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("Target URL:"), 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        self.url_input.setText("https://docs.python.org/3/")
        input_layout.addWidget(self.url_input, 0, 1)
        
        input_layout.addWidget(QLabel("Max Depth:"), 1, 0)
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setRange(1, 10)
        self.depth_spinbox.setValue(2)
        input_layout.addWidget(self.depth_spinbox, 1, 1)
        
        input_layout.addWidget(QLabel("Delay (seconds):"), 2, 0)
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 60)
        self.delay_spinbox.setValue(1)
        input_layout.addWidget(self.delay_spinbox, 2, 1)
        
        self.robots_checkbox = QCheckBox("Respect robots.txt")
        self.robots_checkbox.setChecked(True)
        input_layout.addWidget(self.robots_checkbox, 3, 0, 1, 2)
        
        layout.addWidget(input_group)
        
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Crawl")
        self.start_button.clicked.connect(self.start_crawl)
        
        self.stop_button = QPushButton("Stop Crawl")
        self.stop_button.clicked.connect(self.stop_crawl)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        layout.addLayout(buttons_layout)
        
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("0 / 0 pages processed")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.save_button = QPushButton("Save Markdown")
        self.save_button.clicked.connect(self.save_markdown)
        self.save_button.setEnabled(False)
        
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        
        actions_layout.addWidget(self.save_button)
        actions_layout.addWidget(self.clear_button)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        return panel
    
    def create_output_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        output_group = QGroupBox("Crawled Content (Markdown)")
        output_layout = QVBoxLayout(output_group)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.output_text.setFont(font)
        
        output_layout.addWidget(self.output_text)
        layout.addWidget(output_group)
        
        return panel
    
    def start_crawl(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL to crawl.")
            return
        
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            self.url_input.setText(url)
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.output_text.clear()
        self.total_markdown_content = ""
        
        max_depth = self.depth_spinbox.value()
        delay = self.delay_spinbox.value()
        respect_robots = self.robots_checkbox.isChecked()
        
        self.crawl_worker = CrawlWorker(
            url=url,
            max_depth=max_depth,
            delay=delay,
            respect_robots=respect_robots
        )
        
        self.crawl_worker.page_processed.connect(self.on_page_processed)
        self.crawl_worker.crawl_finished.connect(self.on_crawl_finished)
        self.crawl_worker.crawl_error.connect(self.on_crawl_error)
        self.crawl_worker.status_update.connect(self.on_status_update)
        
        self.crawl_worker.start()
    
    def stop_crawl(self):
        if self.crawl_worker and self.crawl_worker.isRunning():
            self.crawl_worker.cancel()
            self.crawl_worker.wait(3000)
            if self.crawl_worker.isRunning():
                self.crawl_worker.terminate()
                self.crawl_worker.wait()
        
        self.reset_ui_after_crawl()
        self.status_bar.showMessage("Crawl stopped by user")
    
    def on_page_processed(self, url: str, markdown_content: str, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current} / {total} pages processed")
        
        separator = "\n\n" + "="*80 + "\n\n"
        self.output_text.append(separator + markdown_content)
        
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
    
    def on_crawl_finished(self, successful: int, errors: int, combined_content: str):
        self.total_markdown_content = combined_content
        self.reset_ui_after_crawl()
        self.save_button.setEnabled(True)
        
        success_msg = f"Crawl completed! {successful} pages processed successfully"
        if errors > 0:
            success_msg += f", {errors} errors occurred"
        
        self.status_bar.showMessage(success_msg)
        QMessageBox.information(self, "Crawl Complete", success_msg)
    
    def on_crawl_error(self, error_message: str):
        self.reset_ui_after_crawl()
        self.status_bar.showMessage("Crawl failed")
        QMessageBox.critical(self, "Crawl Error", f"An error occurred:\n\n{error_message}")
    
    def on_status_update(self, message: str):
        self.status_bar.showMessage(message)
    
    def reset_ui_after_crawl(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("0 / 0 pages processed")
    
    def save_markdown(self):
        if not self.total_markdown_content:
            QMessageBox.warning(self, "No Content", "No content available to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown File",
            "crawled_content.md",
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.total_markdown_content)
                QMessageBox.information(self, "Saved", f"Content saved to {file_path}")
                self.status_bar.showMessage(f"Saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")
    
    def clear_output(self):
        self.output_text.clear()
        self.total_markdown_content = ""
        self.save_button.setEnabled(False)
        self.status_bar.showMessage("Output cleared")
    
    def closeEvent(self, event):
        if self.crawl_worker and self.crawl_worker.isRunning():
            reply = QMessageBox.question(
                self, 
                'Exit Application',
                'A crawl is currently running. Do you want to stop it and exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_crawl()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()