import re
from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as md
from src.core.crawler import CrawlResult

class ContentProcessor:
    def __init__(self, 
                 strip_tags: list = None, 
                 convert_code_blocks: bool = True,
                 preserve_links: bool = True,
                 preserve_images: bool = True):
        
        self.junk_selectors = [
            'script', 'style', 'nav', 'footer', 'aside', 'header', 'menu',
            '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]',
            '[id*="cookie"]', '[class*="cookie"]', '[id*="consent"]', '[class*="consent"]',
            '[id*="sidebar"]', '[class*="sidebar"]', '[id*="popup"]', '[class*="popup"]',
            '[class*="social"]', '[class*="related"]', '[class*="advert"]'
        ]
        
        self.gibberish_pattern = re.compile(r'\b[A-Za-z0-9+/=]{100,}\b')
        self.min_line_length = 5

        # <<< FIX: The invalid 'strip' key has been removed.
        # 'a' and 'img' are correctly placed only in the 'convert' list.
        self.markdownify_options = {
            'heading_style': 'ATX',
            'bullets': '-',
            'convert': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'a', 'img', 'pre', 'code'],
        }
    
    def _extract_main_content(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'lxml')
        
        for selector in self.junk_selectors:
            for tag in soup.select(selector):
                tag.decompose()
        
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        content_selectors = ['main', 'article', '[role="main"]', '.main-content', '.content', '#main', '#content']
        main_content = None
        for selector in content_selectors:
            if main_content := soup.select_one(selector):
                break
        
        if not main_content:
            main_content = soup.body or soup
            
        return str(main_content)
    
    def _clean_markdown(self, markdown_content: str) -> str:
        lines = markdown_content.split('\n')
        cleaned_lines = []
        
        in_code_block = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
            
            if not in_code_block and self.gibberish_pattern.search(line):
                continue

            stripped_line = line.strip()
            if len(stripped_line) < self.min_line_length and not stripped_line.startswith(('*', '-', '1.', '2.', '3.')):
                if not in_code_block and stripped_line != "":
                    continue

            if len(set(stripped_line)) < 3 and len(stripped_line) > 10:
                continue

            cleaned_lines.append(line)

        markdown_content = '\n'.join(cleaned_lines)
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        markdown_content = markdown_content.strip()
        
        return markdown_content
    
    def _add_metadata(self, markdown_content: str, crawl_result: CrawlResult) -> str:
        metadata_lines = [
            f"# {crawl_result.title}",
            f"**Source:** `{crawl_result.url}`",
            "", "---", "",
            markdown_content
        ]
        return '\n'.join(metadata_lines)
    
    def html_to_markdown(self, html_content: str) -> str:
        if not html_content or not html_content.strip():
            return ""
        try:
            main_content_html = self._extract_main_content(html_content)
            markdown_content = md(main_content_html, **self.markdownify_options)
            cleaned_markdown = self._clean_markdown(markdown_content)
            return cleaned_markdown
        except Exception as e:
            # This exception block is what correctly caught and reported the error.
            return f"Error processing HTML content: {str(e)}"
    
    def process_crawl_result(self, crawl_result: CrawlResult, include_metadata: bool = True) -> str:
        if crawl_result.error:
            return (f"# Error Processing Page\n\n"
                    f"**URL:** `{crawl_result.url}`\n"
                    f"**Error:** {crawl_result.error}\n")
        
        if not crawl_result.content:
            return ""

        markdown_content = self.html_to_markdown(crawl_result.content)
        
        if not markdown_content.strip():
            return ""

        if include_metadata and crawl_result.title:
            markdown_content = self._add_metadata(markdown_content, crawl_result)
        
        return markdown_content
    
    def process_multiple_results(self, crawl_results: list[CrawlResult], separator: str = "\n\n---\n\n") -> str:
        processed_pages = []
        for result in crawl_results:
            processed_content = self.process_crawl_result(result)
            if processed_content:
                processed_pages.append(processed_content)
        return separator.join(processed_pages)