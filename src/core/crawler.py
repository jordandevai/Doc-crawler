import asyncio
from typing import Set, List, Optional, AsyncGenerator
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from collections import deque
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

@dataclass
class CrawlResult:
    """Data class to hold the result of crawling a single URL."""
    url: str
    content: Optional[str]
    title: Optional[str]
    status_code: int
    links: List[str]
    error: Optional[str] = None
    is_redirect: bool = False

class Crawler:
    """An asynchronous, concurrent web crawler."""

    def __init__(
        self,
        respect_robots: bool = True,
        concurrency_limit: int = 10,
        user_agent: str = "Doc-Crawler/1.1 (+https://github.com/your/repo)"
    ):
        self.respect_robots = respect_robots
        self.client = httpx.AsyncClient(
            headers={'User-Agent': user_agent},
            timeout=20.0,
            follow_redirects=True
        )
        self.robots_cache: dict[str, Optional[RobotFileParser]] = {}
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def close(self):
        """Closes the httpx client session."""
        await self.client.aclose()

    def _normalize_url(self, url: str) -> str:
        """Normalizes a URL by lowercasing the scheme/netloc and removing fragments."""
        parsed = urlparse(url)
        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            '', '', ''  # Remove params, query, fragment
        ))

    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Checks if a URL is valid and belongs to the same domain."""
        parsed = urlparse(url)
        return all([
            parsed.scheme in ['http', 'https'],
            parsed.netloc,
            parsed.netloc.lower() == base_domain.lower()
        ])

    async def _can_fetch(self, url: str) -> bool:
        """Checks if crawling is allowed by the domain's robots.txt file."""
        if not self.respect_robots:
            return True

        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        if domain not in self.robots_cache:
            robots_url = urljoin(domain, "/robots.txt")
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self.robots_cache[domain] = rp
            except Exception:
                self.robots_cache[domain] = None
                return True  # Fail open if robots.txt is unreadable

        rp = self.robots_cache[domain]
        return rp.can_fetch(self.client.headers['User-Agent'], url) if rp else True

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extracts and normalizes all valid links from a parsed HTML document."""
        links = []
        base_domain = urlparse(base_url).netloc
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            normalized_url = self._normalize_url(absolute_url)
            if self._is_valid_url(normalized_url, base_domain):
                links.append(normalized_url)
        return links

    async def _fetch_page(self, url: str) -> CrawlResult:
        """Fetches and processes a single web page."""
        if not await self._can_fetch(url):
            return CrawlResult(url=url, status_code=403, content=None, title=None,
                               links=[], error="Blocked by robots.txt")
        try:
            async with self.semaphore:
                response = await self.client.get(url)
                response.raise_for_status()

            final_url = self._normalize_url(str(response.url))
            is_redirect = self._normalize_url(url) != final_url

            soup = BeautifulSoup(response.content, 'lxml')
            title = soup.find('title').get_text(strip=True) if soup.title else "No Title"
            links = self._extract_links(soup, final_url)

            return CrawlResult(
                url=final_url,
                content=str(soup),
                title=title,
                links=links,
                status_code=response.status_code,
                is_redirect=is_redirect
            )
        except httpx.HTTPStatusError as e:
            return CrawlResult(url=url, status_code=e.response.status_code,
                               content=None, title=None, links=[], error=str(e))
        except Exception as e:
            return CrawlResult(url=url, status_code=0, content=None, title=None,
                               links=[], error=str(e))

    async def crawl(
        self,
        start_url: str,
        max_depth: int,
        delay: float,
        cancel_event: asyncio.Event
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Crawls a website starting from `start_url` up to `max_depth`.

        Yields:
            CrawlResult for each page processed.
        """
        start_url = self._normalize_url(start_url)
        queue = deque([(start_url, 0)])
        visited: Set[str] = {start_url}

        while queue:
            if cancel_event.is_set():
                break

            url, depth = queue.popleft()

            result = await self._fetch_page(url)
            yield result

            if result.error:
                continue

            if depth < max_depth:
                for link in result.links:
                    if link not in visited:
                        visited.add(link)
                        queue.append((link, depth + 1))
            
            if delay > 0:
                await asyncio.sleep(delay)