# app/services/crawler.py
import httpx
from bs4 import BeautifulSoup
import validators
from urllib.parse import urljoin, urlparse
import time
from typing import List, Set, Dict, Any, Optional
import logging
from app.config import USER_AGENT, MAX_WEBSITES_TO_CRAWL, MAX_DEPTH
from app.models.schema import WebPage


class WebCrawler:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.pages: List[WebPage] = []
        self.headers = {
            "User-Agent": USER_AGENT
        }
        self.logger = logging.getLogger(__name__)

    async def crawl(self, start_url: str, max_pages: int = MAX_WEBSITES_TO_CRAWL, max_depth: int = MAX_DEPTH) -> List[
        WebPage]:
        """
        Crawl websites starting from the given URL up to a maximum number of pages
        """
        if not validators.url(start_url):
            self.logger.error(f"Invalid URL: {start_url}")
            return []

        self.visited_urls = set()
        self.pages = []

        await self._crawl_recursive(start_url, depth=0, max_depth=max_depth, max_pages=max_pages)

        return self.pages

    async def _crawl_recursive(self, url: str, depth: int, max_depth: int, max_pages: int) -> None:
        """
        Recursively crawl websites up to the specified depth
        """
        if depth > max_depth or len(self.pages) >= max_pages or url in self.visited_urls:
            return

        self.visited_urls.add(url)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract title
                title = soup.title.string if soup.title else url

                # Extract main content
                content = self._extract_main_content(soup)

                # Create WebPage object
                webpage = WebPage(
                    url=url,
                    title=title,
                    content=content,
                    metadata={
                        "crawled_at": time.time(),
                        "depth": depth,
                        "domain": urlparse(url).netloc
                    }
                )

                self.pages.append(webpage)

                # Extract links for further crawling
                if depth < max_depth and len(self.pages) < max_pages:
                    links = self._extract_links(soup, url)
                    for link in links:
                        if len(self.pages) >= max_pages:
                            break
                        await self._crawl_recursive(link, depth + 1, max_depth, max_pages)

        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from the webpage
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract links from the webpage
        """
        links = []
        base_domain = urlparse(base_url).netloc

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)

            # Validate URL and check if it's from the same domain
            if validators.url(full_url) and urlparse(full_url).netloc == base_domain:
                # Remove fragments and queries
                clean_url = full_url.split('#')[0].split('?')[0]
                if clean_url not in self.visited_urls:
                    links.append(clean_url)

        return links