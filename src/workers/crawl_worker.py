import asyncio
import traceback
import time
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.crawler import Crawler
from src.core.processor import ContentProcessor

class CrawlWorker(QThread):
    """Worker thread to run the web crawler without blocking the UI."""
    page_processed = pyqtSignal(str, str, int)
    # Signals: stats_dict, combined_markdown_content
    crawl_finished = pyqtSignal(dict, str)
    crawl_error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(
        self, url: str, max_depth: int, delay: float, respect_robots: bool
    ):
        super().__init__()
        self.url = url
        self.max_depth = max_depth
        self.delay = delay
        self.respect_robots = respect_robots
        self._cancel_event = asyncio.Event()

    def cancel(self):
        """Signals the cancellation event to stop the crawl."""
        self._cancel_event.set()

    async def _run_async(self):
        """The asynchronous core of the crawler task."""
        start_time = time.monotonic()
        crawler = Crawler(respect_robots=self.respect_robots)
        processor = ContentProcessor()
        
        all_results = []
        stats = {
            "start_url": self.url,
            "max_depth": self.max_depth,
            "delay_ms": self.delay * 1000,
            "respect_robots": self.respect_robots,
            "successful_urls": [],
            "failed_urls": [],
            "total_size_bytes": 0,
            "estimated_tokens": 0,
        }
        
        try:
            self.status_update.emit(f"Starting crawl of {self.url}...")
            async for result in crawler.crawl(
                self.url, self.max_depth, self.delay, self._cancel_event
            ):
                all_results.append(result)

                if result.error:
                    stats["failed_urls"].append(f"{result.url} (Status: {result.status_code}, Error: {result.error})")
                else:
                    stats["successful_urls"].append(result.url)
                    if result.content:
                        stats["total_size_bytes"] += len(result.content.encode('utf-8'))

                markdown = processor.process_crawl_result(result)
                stats["estimated_tokens"] += len(markdown.split())
                self.page_processed.emit(result.url, markdown, len(all_results))

            if self._cancel_event.is_set():
                self.status_update.emit("Crawl cancelled by user.")
            else:
                self.status_update.emit("Crawl completed. Finalizing content...")

            combined_content = processor.process_multiple_results(all_results)
            
            stats["duration_seconds"] = time.monotonic() - start_time
            self.crawl_finished.emit(stats, combined_content)

        finally:
            await crawler.close()

    def run(self):
        """Executes the crawler task in a new asyncio event loop."""
        try:
            asyncio.run(self._run_async())
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}\n{traceback.format_exc()}"
            self.crawl_error.emit(error_msg)
            self.status_update.emit(f"Crawl failed: {e}")