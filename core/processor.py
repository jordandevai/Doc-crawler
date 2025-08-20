from typing import Optional, Dict, Any
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from .crawler import CrawlResult


class ContentProcessor:
    def __init__(self, 
                 strip_tags: list = None, 
                 convert_code_blocks: bool = True,
                 preserve_links: bool = True,
                 preserve_images: bool = True):
        self.strip_tags = strip_tags or [
            'script', 'style', 'nav', 'footer', 'aside', 
            'header', 'menu', 'advertisement'
        ]
        self.convert_code_blocks = convert_code_blocks
        self.preserve_links = preserve_links
        self.preserve_images = preserve_images
        
        self.markdownify_options = {
            'heading_style': 'ATX',
            'bullets': '-',
            'strip': self.strip_tags,
            'convert': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li'],
            'escape_misc': False,
            'escape_asterisks': False,
            'escape_underscores': False,
        }
        
        if self.preserve_links:
            self.markdownify_options['convert'].extend(['a'])
        
        if self.preserve_images:
            self.markdownify_options['convert'].extend(['img'])
            
        if self.convert_code_blocks:
            self.markdownify_options['convert'].extend(['pre', 'code'])
    
    def _extract_main_content(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'lxml')
        
        for tag in soup(self.strip_tags):
            tag.decompose()
        
        content_selectors = [
            'main',
            'article', 
            '[role="main"]',
            '.main-content',
            '.content',
            '#main',
            '#content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body or soup
        
        return str(main_content)
    
    def _clean_markdown(self, markdown_content: str) -> str:
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        markdown_content = re.sub(r'[ \t]+$', '', markdown_content, flags=re.MULTILINE)
        
        markdown_content = re.sub(r'^\s*$\n', '', markdown_content, flags=re.MULTILINE)
        
        markdown_content = markdown_content.strip()
        
        return markdown_content
    
    def _add_metadata(self, markdown_content: str, crawl_result: CrawlResult) -> str:
        metadata_lines = [
            f"# {crawl_result.title}",
            f"",
            f"**Source:** {crawl_result.url}",
            f"**Status:** {crawl_result.status_code}",
            f"",
            "---",
            f"",
            markdown_content
        ]
        
        return '\n'.join(metadata_lines)
    
    def html_to_markdown(self, html_content: str) -> str:
        if not html_content or not html_content.strip():
            return ""
        
        try:
            main_content_html = self._extract_main_content(html_content)
            
            markdown_content = md(
                main_content_html,
                **self.markdownify_options
            )
            
            cleaned_markdown = self._clean_markdown(markdown_content)
            
            return cleaned_markdown
            
        except Exception as e:
            return f"Error processing HTML content: {str(e)}"
    
    def process_crawl_result(self, crawl_result: CrawlResult, 
                           include_metadata: bool = True) -> str:
        if crawl_result.error:
            error_content = f"# Error Processing Page\n\n"
            error_content += f"**URL:** {crawl_result.url}\n"
            error_content += f"**Error:** {crawl_result.error}\n"
            error_content += f"**Status Code:** {crawl_result.status_code}\n"
            return error_content
        
        if not crawl_result.content:
            return f"# Empty Content\n\n**URL:** {crawl_result.url}\n\nNo content found on this page."
        
        soup = BeautifulSoup(crawl_result.content, 'html.parser')
        html_content = str(soup)
        
        markdown_content = self.html_to_markdown(html_content)
        
        if include_metadata:
            markdown_content = self._add_metadata(markdown_content, crawl_result)
        
        return markdown_content
    
    def process_multiple_results(self, crawl_results: list[CrawlResult], 
                               separator: str = "\n\n---\n\n") -> str:
        processed_pages = []
        
        for result in crawl_results:
            processed_content = self.process_crawl_result(result)
            if processed_content.strip():
                processed_pages.append(processed_content)
        
        return separator.join(processed_pages)
    
    def save_to_file(self, content: str, filename: str, encoding: str = 'utf-8') -> bool:
        try:
            with open(filename, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving file {filename}: {str(e)}")
            return False