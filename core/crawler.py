from typing import Set, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
import httpx
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass


@dataclass
class CrawlResult:
    url: str
    content: str
    title: str
    links: List[str]
    status_code: int
    error: Optional[str] = None


class Crawler:
    def __init__(self, max_depth: int = 2, delay: float = 1.0, respect_robots: bool = True):
        self.max_depth = max_depth
        self.delay = delay
        self.respect_robots = respect_robots
        self.visited: Set[str] = set()
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                'User-Agent': 'Doc-Crawler/1.0 (+https://github.com/user/doc-crawler)'
            }
        )
        self.robots_cache = {}
        
    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()
    
    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        return urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            parsed.params,
            parsed.query,
            ''
        ))
    
    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ['http', 'https']:
            return False
        if not parsed.netloc:
            return False
        return parsed.netloc.lower() == base_domain.lower()
    
    def _can_fetch(self, url: str) -> bool:
        if not self.respect_robots:
            return True
            
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if domain not in self.robots_cache:
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self.robots_cache[domain] = rp
            except:
                self.robots_cache[domain] = None
        
        robots_parser = self.robots_cache[domain]
        if robots_parser:
            return robots_parser.can_fetch('*', url)
        return True
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            normalized_url = self._normalize_url(absolute_url)
            
            if (self._is_valid_url(normalized_url, base_domain) and 
                normalized_url not in self.visited):
                links.append(normalized_url)
        
        return links
    
    def _fetch_page(self, url: str) -> CrawlResult:
        try:
            if not self._can_fetch(url):
                return CrawlResult(
                    url=url,
                    content='',
                    title='',
                    links=[],
                    status_code=403,
                    error='Blocked by robots.txt'
                )
            
            response = self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else ''
            
            for script in soup(['script', 'style', 'nav', 'footer', 'aside']):
                script.decompose()
            
            main_content = soup.find('main') or soup.find('article') or soup.body or soup
            content = main_content.get_text(separator='\n', strip=True) if main_content else ''
            
            links = self._extract_links(soup, url)
            
            return CrawlResult(
                url=url,
                content=content,
                title=title,
                links=links,
                status_code=response.status_code
            )
            
        except Exception as e:
            return CrawlResult(
                url=url,
                content='',
                title='',
                links=[],
                status_code=0,
                error=str(e)
            )
    
    def crawl(self, start_url: str) -> List[CrawlResult]:
        results = []
        queue = [(self._normalize_url(start_url), 0)]
        
        while queue:
            url, depth = queue.pop(0)
            
            if url in self.visited or depth > self.max_depth:
                continue
            
            self.visited.add(url)
            
            if self.delay > 0:
                time.sleep(self.delay)
            
            result = self._fetch_page(url)
            results.append(result)
            
            if depth < self.max_depth and not result.error:
                for link in result.links:
                    if link not in self.visited:
                        queue.append((link, depth + 1))
        
        return results