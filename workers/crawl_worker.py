from PyQt6.QtCore import QThread, pyqtSignal, QObject
from typing import List
import traceback
from core.crawler import Crawler, CrawlResult
from core.processor import ContentProcessor


class CrawlWorker(QThread):
    page_processed = pyqtSignal(str, str, int, int)
    crawl_finished = pyqtSignal(int, int, str)
    crawl_error = pyqtSignal(str)
    status_update = pyqtSignal(str)
    
    def __init__(self, url: str, max_depth: int = 2, delay: float = 1.0, 
                 respect_robots: bool = True):
        super().__init__()
        self.url = url
        self.max_depth = max_depth
        self.delay = delay
        self.respect_robots = respect_robots
        self._is_cancelled = False
        
    def cancel(self):
        self._is_cancelled = True
        
    def run(self):
        try:
            self.status_update.emit("Initializing crawler...")
            
            crawler = Crawler(
                max_depth=self.max_depth,
                delay=self.delay,
                respect_robots=self.respect_robots
            )
            
            processor = ContentProcessor(
                preserve_links=True,
                preserve_images=True,
                convert_code_blocks=True
            )
            
            self.status_update.emit(f"Starting crawl of {self.url}")
            
            results: List[CrawlResult] = crawler.crawl(self.url)
            
            if self._is_cancelled:
                self.status_update.emit("Crawl cancelled by user")
                return
            
            total_pages = len(results)
            successful_pages = 0
            errors = 0
            all_markdown_content = []
            
            for i, result in enumerate(results):
                if self._is_cancelled:
                    self.status_update.emit("Processing cancelled by user")
                    return
                
                self.status_update.emit(f"Processing page {i+1}/{total_pages}: {result.url}")
                
                if result.error:
                    errors += 1
                    markdown_content = processor.process_crawl_result(result)
                else:
                    successful_pages += 1
                    markdown_content = processor.process_crawl_result(result)
                
                all_markdown_content.append(markdown_content)
                
                self.page_processed.emit(
                    result.url, 
                    markdown_content,
                    i + 1,
                    total_pages
                )
            
            combined_content = processor.process_multiple_results(results)
            
            self.status_update.emit("Crawl completed successfully")
            self.crawl_finished.emit(successful_pages, errors, combined_content)
            
        except Exception as e:
            error_msg = f"Crawl failed: {str(e)}\n{traceback.format_exc()}"
            self.crawl_error.emit(error_msg)
            self.status_update.emit(f"Crawl failed: {str(e)}")