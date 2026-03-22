"""
Documentation Crawler

Crawls documentation sites, extracts content, and prepares for analysis.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Chrome browser UA — many doc sites (Next.js, Nuxt) block bots but serve full HTML to browsers
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class Page:
    """Represents a crawled documentation page."""
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: str = ""
    structured_content: Optional[Dict[str, Any]] = None
    heading_hierarchy: Optional[List[Dict]] = None
    code_blocks: Optional[List[Dict]] = None
    links: Optional[List[str]] = None
    last_modified: Optional[str] = None


class DocumentationCrawler:
    """Crawls documentation sites and extracts structured content."""
    
    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        respect_robots_txt: bool = True,
        delay: float = 1.0,
    ):
        self.start_url = start_url
        self.max_pages = max_pages
        self.respect_robots_txt = respect_robots_txt
        self.delay = delay
        self.visited: set = set()
        self.pages: List[Page] = []
        self.client: Optional[httpx.AsyncClient] = None
        
        # Parse base URL
        parsed = urlparse(start_url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.domain = parsed.netloc
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": BROWSER_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def crawl(self) -> List[Page]:
        """Crawl the documentation site."""
        logger.info(f"Starting crawl of {self.start_url}")
        
        # Discover URLs to crawl
        urls = await self._discover_urls()
        logger.info(f"Discovered {len(urls)} URLs to crawl")
        
        # Crawl each URL
        for url in urls[:self.max_pages]:
            if url in self.visited:
                continue
            
            page = await self._fetch_and_parse(url)
            if page:
                self.pages.append(page)
                self.visited.add(url)
            
            # Politeness delay
            await asyncio.sleep(self.delay)
        
        logger.info(f"Crawled {len(self.pages)} pages")
        return self.pages
    
    async def _discover_urls(self) -> List[str]:
        """Discover URLs to crawl via sitemap or link extraction."""
        urls = []
        
        # Try sitemap.xml
        sitemap_urls = await self._parse_sitemap()
        if sitemap_urls:
            urls.extend(sitemap_urls)
        
        # Try sitemap_index.xml
        if not urls:
            sitemap_index_urls = await self._parse_sitemap_index()
            if sitemap_index_urls:
                urls.extend(sitemap_index_urls)
        
        # Fallback: extract links from start page
        if not urls:
            links = await self._extract_links_from_page(self.start_url)
            urls.extend(links)
        
        # Always include start URL
        if self.start_url not in urls:
            urls.insert(0, self.start_url)
        
        return urls
    
    async def _parse_sitemap(self) -> List[str]:
        """Parse sitemap.xml for URLs."""
        try:
            sitemap_url = urljoin(self.base_url, "/sitemap.xml")
            response = await self.client.get(sitemap_url)
            
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.content)
            
            # Handle both sitemap index and URL set
            urls = []
            for elem in root.iter():
                if elem.tag.endswith("loc"):
                    url = elem.text.strip() if elem.text else ""
                    if self._is_same_domain(url):
                        urls.append(url)
            
            return urls
        except Exception as e:
            logger.warning(f"Failed to parse sitemap: {e}")
            return []
    
    async def _parse_sitemap_index(self) -> List[str]:
        """Parse sitemap_index.xml for URLs."""
        try:
            sitemap_index_url = urljoin(self.base_url, "/sitemap_index.xml")
            response = await self.client.get(sitemap_index_url)
            
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.content)
            
            urls = []
            for elem in root.iter():
                if elem.tag.endswith("loc"):
                    sitemap_url = elem.text.strip() if elem.text else ""
                    # Fetch individual sitemap
                    try:
                        sitemap_response = await self.client.get(sitemap_url)
                        if sitemap_response.status_code == 200:
                            sitemap_root = ET.fromstring(sitemap_response.content)
                            for url_elem in sitemap_root.iter():
                                if url_elem.tag.endswith("loc"):
                                    page_url = url_elem.text.strip() if url_elem.text else ""
                                    if self._is_same_domain(page_url):
                                        urls.append(page_url)
                    except Exception as e:
                        logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
            
            return urls
        except Exception as e:
            logger.warning(f"Failed to parse sitemap index: {e}")
            return []
    
    async def _extract_links_from_page(self, url: str, max_links: int = 50) -> List[str]:
        """Extract links from a page."""
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                
                if self._is_same_domain(full_url) and self._is_valid_path(full_url):
                    links.append(full_url)
                
                if len(links) >= max_links:
                    break
            
            return links
        except Exception as e:
            logger.warning(f"Failed to extract links from {url}: {e}")
            return []
    
    async def _fetch_and_parse(self, url: str) -> Optional[Page]:
        """Fetch and parse a single page."""
        try:
            logger.debug(f"Fetching {url}")
            response = await self.client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: {response.status_code}")
                return None
            
            content_type = response.headers.get('content-type', '')

            if 'text/html' in content_type or 'xhtml' in content_type or not content_type:
                # Default to HTML parsing (most doc sites serve HTML)
                return self._parse_html(response.text, url)
            elif 'text/markdown' in content_type or 'text/plain' in content_type:
                return Page(url=url, content=response.text)
            else:
                # Try HTML parsing as fallback — many servers mis-report content type
                logger.info(f"Unexpected content type for {url}: {content_type}, trying HTML parse")
                return self._parse_html(response.text, url)
        
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _parse_html(self, html: str, url: str) -> Page:
        """Parse HTML content and extract structured data.

        Key: find the content container FIRST, then clean noise inside it.
        Never remove elements from the full soup before locating content,
        because class-name removal (e.g. 'sidebar') can destroy parent wrappers.
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)

        # Extract description
        description = None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content')
        else:
            first_p = soup.find('p')
            if first_p:
                description = first_p.get_text(strip=True)[:200]

        # --- Find content container FIRST (before any cleanup) ---
        main_content = (
            soup.find('article') or
            soup.find('main') or
            soup.find('div', role='main') or
            soup.find('div', class_=re.compile(
                r'(docs-content|documentation|page-content|markdown-body|'
                r'article-content|post-content|entry-content|Content-article)',
                re.IGNORECASE
            )) or
            soup.find('div', class_='content')
        )

        if not main_content:
            # Fallback: use body but remove obvious noise
            main_content = soup.find('body')
            if main_content:
                for tag in main_content.find_all(['nav', 'footer', 'aside', 'header', 'script', 'style', 'noscript']):
                    tag.decompose()
        else:
            # Clean noise INSIDE the content container only
            for tag in main_content.find_all(['nav', 'footer', 'script', 'style', 'noscript']):
                tag.decompose()

        content = main_content.get_text(separator='\n', strip=True) if main_content else ""

        # Extract heading hierarchy from content container (not full page)
        search_scope = main_content or soup
        headings = []
        for level in range(1, 7):
            for h in search_scope.find_all(f'h{level}'):
                headings.append({
                    'level': level,
                    'text': h.get_text(strip=True),
                })

        # Extract code blocks from content container
        code_blocks = []
        for pre in search_scope.find_all('pre'):
            code = pre.find('code')
            if code:
                language = None
                classes = code.get('class', [])
                for cls in classes:
                    if cls.startswith('language-') or cls.startswith('lang-'):
                        language = cls.split('-', 1)[1]
                        break
                code_blocks.append({
                    'language': language,
                    'code': code.get_text(strip=True),
                })

        # Extract links
        links = []
        for a in search_scope.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(url, href)
            if self._is_same_domain(full_url):
                links.append(full_url)

        return Page(
            url=url,
            title=title,
            description=description,
            content=content,
            heading_hierarchy=headings,
            code_blocks=code_blocks,
            links=list(set(links)),
        )
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is on the same domain."""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain
        except Exception:
            return False
    
    def _is_valid_path(self, url: str) -> bool:
        """Check if URL path should be crawled."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Skip common non-content paths
        skip_patterns = [
            '/assets/', '/images/', '/css/', '/js/',
            '/api/', '/admin/', '/login/', '/logout/',
            '.pdf', '.jpg', '.png', '.gif', '.css', '.js',
        ]
        
        for pattern in skip_patterns:
            if pattern in path:
                return False
        
        return True
