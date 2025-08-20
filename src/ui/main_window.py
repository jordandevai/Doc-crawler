import os
from datetime import datetime
from urllib.parse import urlparse
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox,
                           QCheckBox, QProgressBar, QSplitter, QGroupBox, QGridLayout,
                           QMessageBox, QFileDialog, QStatusBar, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QFont

from src.workers.crawl_worker import CrawlWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.crawl_worker = None
        self.total_markdown_content = ""
        self.stats_markdown_content = ""
        self.pages_processed = 0
        self.current_crawl_url = ""
        self.autosave_filepath = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Doc-Crawler v1.4 (Stats Edition)")
        self.setGeometry(100, 100, 1200, 800)
        self.setCentralWidget(QWidget())
        main_layout = QHBoxLayout(self.centralWidget())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_control_panel())
        splitter.addWidget(self._create_output_panel())
        splitter.setSizes([350, 850])
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_control_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)

        input_group = QGroupBox("Crawl Configuration")
        input_layout = QGridLayout(input_group)
        input_layout.addWidget(QLabel("Target URL:"), 0, 0)
        self.url_input = QLineEdit("https://docs.python.org/3/")
        self.url_input.setPlaceholderText("https://example.com")
        input_layout.addWidget(self.url_input, 0, 1)

        input_layout.addWidget(QLabel("Max Depth:"), 1, 0)
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setRange(0, 10)
        self.depth_spinbox.setValue(1)
        input_layout.addWidget(self.depth_spinbox, 1, 1)

        input_layout.addWidget(QLabel("Delay (ms):"), 2, 0)
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 5000)
        self.delay_spinbox.setValue(250)
        self.delay_spinbox.setSingleStep(50)
        input_layout.addWidget(self.delay_spinbox, 2, 1)

        self.robots_checkbox = QCheckBox("Respect robots.txt")
        self.robots_checkbox.setChecked(True)
        input_layout.addWidget(self.robots_checkbox, 3, 0, 1, 2)
        
        self.autosave_checkbox = QCheckBox("Autosave results")
        self.autosave_checkbox.setChecked(True)
        input_layout.addWidget(self.autosave_checkbox, 4, 0, 1, 2)
        
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
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_label = QLabel("Waiting to start...")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        layout.addWidget(progress_group)

        actions_group = QGroupBox("Output")
        actions_layout = QVBoxLayout(actions_group)
        self.save_button = QPushButton("Save Manually...")
        self.save_button.clicked.connect(self.save_markdown)
        self.save_button.setEnabled(False)
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        actions_layout.addWidget(self.save_button)
        actions_layout.addWidget(self.clear_button)
        layout.addWidget(actions_group)

        layout.addStretch()
        return panel

    def _create_output_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.output_tabs = QTabWidget()
        layout.addWidget(self.output_tabs)

        # Live Content Tab
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        font = QFont("Consolas", 10)
        self.output_text.setFont(font)
        content_layout.addWidget(self.output_text)
        self.output_tabs.addTab(content_widget, "Live Content")

        # Statistics Tab
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(font)
        stats_layout.addWidget(self.stats_text)
        self.output_tabs.addTab(stats_widget, "Crawl Statistics")
        
        return panel

    def _get_output_dir(self) -> str:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        output_dir = os.path.join(project_root, 'output')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _generate_default_filename(self) -> str:
        if not self.current_crawl_url: return "crawled_content.md"
        try:
            parsed_url = urlparse(self.current_crawl_url)
            domain = parsed_url.netloc.replace('.', '_').replace('-', '_')
            date_str = datetime.now().strftime("%d%m%y")
            return f"{domain}-{date_str}.md"
        except Exception:
            return f"crawl_output-{datetime.now().strftime('%d%m%y')}.md"

    def _format_stats_as_markdown(self, stats: dict) -> str:
        """Converts the stats dictionary to a readable Markdown string."""
        success_count = len(stats["successful_urls"])
        fail_count = len(stats["failed_urls"])
        total_urls = success_count + fail_count
        duration = stats.get("duration_seconds", 0)
        
        lines = [
            f"# Crawl Statistics for `{stats['start_url']}`",
            f"**Crawl Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            "", "---", "",
            "## Summary",
            f"- **Total URLs Processed:** `{total_urls}`",
            f"- **Successful Pages:** `{success_count}`",
            f"- **Failed Pages:** `{fail_count}`",
            f"- **Total Duration:** `{duration:.2f} seconds`",
            f"- **Total Content Size:** `{stats['total_size_bytes'] / 1024:.2f} KB`",
            f"- **Estimated Tokens:** `{stats['estimated_tokens']:,}`",
            "", "---", "",
            "## Configuration",
            f"- **Start URL:** `{stats['start_url']}`",
            f"- **Max Depth:** `{stats['max_depth']}`",
            f"- **Delay Between Requests:** `{stats['delay_ms']:.0f} ms`",
            f"- **Respect robots.txt:** `{stats['respect_robots']}`",
            "", "---", "",
            f"## Successful URLs ({success_count})",
        ]
        lines.extend([f"- `{url}`" for url in stats["successful_urls"]])
        
        lines.extend(["", "---", "", f"## Failed URLs ({fail_count})"])
        if not stats["failed_urls"]:
            lines.append("None.")
        else:
            lines.extend([f"- `{url}`" for url in stats["failed_urls"]])
            
        return "\n".join(lines)

    def start_crawl(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL.")
            return

        self.current_crawl_url = url
        self.clear_output()
        self.pages_processed = 0
        self.progress_label.setText("Initializing crawl...")
        self.output_tabs.setCurrentIndex(0) # Switch to live view
        
        if self.autosave_checkbox.isChecked():
            output_dir = self._get_output_dir()
            base_filename = self._generate_default_filename()
            self.autosave_filepath = os.path.join(output_dir, base_filename)
            if os.path.exists(f"{self.autosave_filepath}.tmp"):
                os.remove(f"{self.autosave_filepath}.tmp")
        else:
            self.autosave_filepath = None
            
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.crawl_worker = CrawlWorker(
            url=url,
            max_depth=self.depth_spinbox.value(),
            delay=self.delay_spinbox.value() / 1000.0,
            respect_robots=self.robots_checkbox.isChecked()
        )
        self.crawl_worker.page_processed.connect(self.on_page_processed)
        self.crawl_worker.crawl_finished.connect(self.on_crawl_finished)
        self.crawl_worker.crawl_error.connect(self.on_crawl_error)
        self.crawl_worker.status_update.connect(self.on_status_update)
        self.crawl_worker.start()

    def stop_crawl(self):
        if self.crawl_worker:
            self.crawl_worker.cancel()
            self.stop_button.setText("Stopping...")
            self.stop_button.setEnabled(False)
        if self.autosave_filepath and os.path.exists(f"{self.autosave_filepath}.tmp"):
            self.status_bar.showMessage(f"Crawl stopped. Partial results in {os.path.basename(self.autosave_filepath)}.tmp")

    def on_page_processed(self, url: str, markdown: str, count: int):
        self.pages_processed = count
        self.progress_label.setText(f"Processed {self.pages_processed} pages...")
        
        # Cleaner, LLM-friendly separator
        separator = "\n\n---\n\n"
        full_chunk = markdown if self.pages_processed == 1 else separator + markdown
        
        self.output_text.append(full_chunk)
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)

        if self.autosave_filepath:
            try:
                with open(f"{self.autosave_filepath}.tmp", 'a', encoding='utf-8') as f:
                    f.write(full_chunk)
            except Exception as e:
                self.status_bar.showMessage(f"Autosave failed: {e}")
                self.autosave_filepath = None

    def on_crawl_finished(self, stats: dict, combined_content: str):
        self.total_markdown_content = combined_content
        self.stats_markdown_content = self._format_stats_as_markdown(stats)
        
        self.stats_text.setText(self.stats_markdown_content)
        self.output_tabs.setCurrentIndex(1) # Switch to stats view

        self.reset_ui_after_crawl()
        
        if self.autosave_filepath and os.path.exists(f"{self.autosave_filepath}.tmp"):
            stats_path = self.autosave_filepath.replace('.md', '_stats.md')
            try:
                # Save main content
                os.rename(f"{self.autosave_filepath}.tmp", self.autosave_filepath)
                # Save stats
                with open(stats_path, 'w', encoding='utf-8') as f:
                    f.write(self.stats_markdown_content)
                msg = f"Crawl finished & autosaved to {os.path.basename(self.autosave_filepath)}"
            except OSError as e:
                msg = f"Error finalizing autosave: {e}"
        else:
            success_count = len(stats.get("successful_urls", []))
            fail_count = len(stats.get("failed_urls", []))
            msg = f"Crawl finished: {success_count} successful, {fail_count} failed."
            if self.total_markdown_content:
                self.save_button.setEnabled(True)
        
        self.status_bar.showMessage(msg)
        self.progress_label.setText(f"Completed. {self.pages_processed} pages processed.")
        QMessageBox.information(self, "Crawl Complete", msg)
        self.autosave_filepath = None

    def on_crawl_error(self, error_msg: str):
        self.reset_ui_after_crawl()
        tmp_path = f"{self.autosave_filepath}.tmp" if self.autosave_filepath else None
        if tmp_path and os.path.exists(tmp_path):
            status = f"Crawl failed. Partial results in {os.path.basename(tmp_path)}"
        else:
            status = "Crawl failed with an error."
        self.status_bar.showMessage(status)
        self.progress_label.setText("Crawl failed.")
        QMessageBox.critical(self, "Crawl Error", error_msg)
        self.autosave_filepath = None

    def on_status_update(self, message: str):
        self.status_bar.showMessage(message)

    def reset_ui_after_crawl(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stop Crawl")
        self.progress_bar.setVisible(False)
        if not self.autosave_checkbox.isChecked() and (self.total_markdown_content or self.stats_markdown_content):
            self.save_button.setEnabled(True)

    def save_markdown(self):
        if not self.total_markdown_content:
            QMessageBox.warning(self, "No Content", "No content to save.")
            return

        default_path = os.path.join(self._get_output_dir(), self._generate_default_filename())
        path, _ = QFileDialog.getSaveFileName(self, "Save Content File", default_path, "Markdown Files (*.md)")
        
        if path:
            stats_path = path.replace('.md', '_stats.md')
            try:
                # Save main content
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.total_markdown_content)
                # Save stats
                with open(stats_path, 'w', encoding='utf-8') as f:
                    f.write(self.stats_markdown_content)
                self.status_bar.showMessage(f"Saved content and stats to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save files: {e}")

    def clear_output(self):
        self.output_text.clear()
        self.stats_text.clear()
        self.total_markdown_content = ""
        self.stats_markdown_content = ""
        self.save_button.setEnabled(False)

    def closeEvent(self, event):
        if self.crawl_worker and self.crawl_worker.isRunning():
            reply = QMessageBox.question(self, 'Confirm Exit',
                'A crawl is running. Are you sure you want to exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_crawl()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()