#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
import re
from collections import defaultdict, deque
import hashlib
from rich.console import Console
from rich.progress import track
from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime
from pathlib import Path
import yaml

console = Console()

class GK8RagProcessor:
    def __init__(self, jwt_token, output_dir="rag_output", 
                 chunk_size_target=1000, debug=False):
        self.jwt_token = jwt_token
        self.base_url = "https://docs.gk8.io"
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "User-Agent": "GK8-RAG-Processor/1.0"
        }
        self.visited_urls = set()
        self.content_data = []
        self.output_dir = Path(output_dir)
        self.debug = debug
        
        # Chunking configuration
        self.CHUNK_SIZE_MIN = 300
        self.CHUNK_SIZE_TARGET = chunk_size_target
        self.CHUNK_SIZE_MAX = 1500
        self.CHUNK_OVERLAP = 100
        self.OUTPUT_FORMAT = "markdown"
        self.PRESERVE_LINKS = True
        self.INCLUDE_IMAGES = True
        
        # URL patterns to exclude (add more as needed)
        self.exclude_patterns = [
            r'/print/',  # Print versions
            r'/pdf/',    # PDF versions
            r'\.(pdf|zip|tar|gz)$',  # File downloads
        ]
        
        # Content selectors for cleaning
        self.REMOVE_SELECTORS = [
            'nav', 'footer', 'header', '.sidebar', '.navigation',
            '.breadcrumb', '.page-header', '.social-links',
            '.advertisement', '.cookie-notice', '.toc', '.table-of-contents',
            '.edit-page', '.last-updated', '.contributors'
        ]
        
        self.CLEAN_SELECTORS = [
            'script', 'style', 'meta', 'link[rel="stylesheet"]',
            'noscript', 'iframe'
        ]
        
        self.PRESERVE_SELECTORS = [
            'main', 'article', '.content', 'pre', 'code',
            'table', 'ul', 'ol', 'blockquote', '.main-content',
            '.doc-content', '.markdown-body'
        ]
        
        # Initialize output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Playwright for JavaScript-rendered content
        self.playwright = None
        self.browser = None
        self.page = None
        self.authenticated = False
        self._init_playwright()
    
    def _init_playwright(self):
        """Initialize Playwright for JavaScript-rendered content"""
        try:
            console.print("[dim]Starting Playwright browser...[/dim]")
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            self.page = self.browser.new_page()
            
            # Set timeouts
            self.page.set_default_timeout(15000)  # 15 seconds
            
            # Authenticate immediately after browser setup
            self._authenticate()
            
            console.print("[green]✓ Playwright browser ready and authenticated[/green]")
                
        except Exception as e:
            console.print(f"[red]Playwright setup failed:[/red] {str(e)[:100]}...")
            console.print("[red]Cannot process JavaScript content without browser automation[/red]")
            self._cleanup_playwright()
    
    def _authenticate(self):
        """Authenticate once using JWT to establish session cookies"""
        try:
            console.print("[dim]Authenticating with JWT...[/dim]")
            
            # Initial authentication request with JWT and reload parameter
            auth_url = f"https://docs.gk8.io?jwt={self.jwt_token}&reload"
            self.page.goto(auth_url)
            
            # Wait for authentication to complete and page to load
            self.page.wait_for_load_state("networkidle")
            
            # Additional wait to ensure session cookies are set
            time.sleep(2)
            
            # Verify authentication worked by checking if we're not on a login page
            page_content = self.page.content()
            if "login" in page_content.lower() or len(page_content) < 100000:
                raise Exception("Authentication may have failed - got login page or minimal content")
            
            self.authenticated = True
            console.print("[green]✓ Authentication successful - session established[/green]")
            
        except Exception as e:
            console.print(f"[red]Authentication failed:[/red] {e}")
            self.authenticated = False
    
    def _cleanup_playwright(self):
        """Cleanup Playwright resources"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        finally:
            self.playwright = None
            self.browser = None
            self.page = None
    
    def __del__(self):
        """Cleanup Playwright resources"""
        self._cleanup_playwright()
    
    def _crawl_with_playwright(self, url):
        """Crawl page using Playwright with session cookies (no JWT needed)"""
        try:
            # Navigate to page using session cookies (no JWT parameter needed)
            self.page.goto(url)
            
            # Wait for page to load completely
            self.page.wait_for_load_state("networkidle")
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Get page source after JavaScript execution
            page_source = self.page.content()
            
            if self.debug:
                console.print(f"[dim]Playwright page loaded, content length: {len(page_source)}[/dim]")
            
            # Check if we got logged out (minimal content = login page)
            if len(page_source) < 50000:
                console.print(f"[yellow]Warning: Small content size ({len(page_source)}) - possible session expiry[/yellow]")
            
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            console.print(f"[red]Playwright crawl error for {url}:[/red] {e}")
            return None
    
    def normalize_url(self, url):
        """Normalize URL to avoid duplicates"""
        # Parse the URL
        parsed = urlparse(url)
        
        # Remove fragment (anchor)
        parsed = parsed._replace(fragment='')
        
        # Remove trailing slash from path (except for root)
        path = parsed.path
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')
        parsed = parsed._replace(path=path)
        
        # Reconstruct URL
        normalized = urlunparse(parsed)
        
        # Remove common tracking parameters if needed
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign']
        if parsed.query:
            # Parse query parameters
            params = parse_qs(parsed.query, keep_blank_values=True)
            # Remove tracking parameters
            for param in tracking_params:
                params.pop(param, None)
            # Reconstruct query string
            if params:
                query = urlencode(params, doseq=True)
                normalized = urlunparse(parsed._replace(query=query))
            else:
                normalized = urlunparse(parsed._replace(query=''))
        
        return normalized
    
    def should_crawl_url(self, url):
        """Check if URL matches our target spaces and versions"""
        # Normalize the URL first
        normalized_url = self.normalize_url(url)
        
        # Skip if already visited (using normalized URL)
        if normalized_url in self.visited_urls:
            return False
        
        # Must be within our base domain
        if not normalized_url.startswith(self.base_url):
            return False
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if re.search(pattern, normalized_url):
                if self.debug:
                    console.print(f"[dim]Excluding {normalized_url} (matches pattern: {pattern})[/dim]")
                return False
            
        # Check if it's a v15 API URL or general (non-versioned) URL
        if "/api-v15/" in normalized_url:
            return True
        elif "/api-v" in normalized_url:  # Other API versions - skip
            if self.debug:
                console.print(f"[dim]Skipping non-v15 API URL: {normalized_url}[/dim]")
            return False
        else:  # General space
            return True
    
    def determine_space(self, url):
        """Determine which space a URL belongs to"""
        if "/api-v15/" in url:
            return "api-v15"
        elif "/guides-v15/" in url:
            return "guides-v15"
        elif "/reference/" in url:
            return "reference"
        elif "/api-v" in url:
            # Extract version number
            match = re.search(r'/api-v(\d+)/', url)
            if match:
                return f"api-v{match.group(1)}"
            return "api-other"
        elif "/guides-v" in url:
            # Extract version number
            match = re.search(r'/guides-v(\d+)/', url)
            if match:
                return f"guides-v{match.group(1)}"
            return "guides-other"
        # Add logic for other spaces
        return "general"
    
    def crawl_page(self, url):
        """Crawl a single page and store raw content"""
        # Normalize URL before processing
        normalized_url = self.normalize_url(url)
        
        # Check again if we should crawl (in case called directly)
        if normalized_url in self.visited_urls:
            return []
            
        try:
            self.visited_urls.add(normalized_url)
            console.print(f"[blue]Crawling:[/blue] {normalized_url}")
            
            # Use Playwright for JavaScript-rendered content if available and authenticated
            if self.page and self.authenticated:
                soup = self._crawl_with_playwright(normalized_url)
            else:
                console.print("[red]Error: Playwright not available or not authenticated[/red]")
                return []
            
            if not soup:
                return []
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.text.strip() if title_elem else ''
            
            # Extract ALL links (not just the first one!)
            all_links = soup.find_all('a', href=True)
            if self.debug:
                console.print(f"[dim]Found {len(all_links)} total <a> tags on page[/dim]")
            
            links = []
            for link in all_links:
                href = link['href']
                
                # Skip javascript links, mailto, etc.
                if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                    
                # Convert relative URLs to absolute
                absolute_url = urljoin(normalized_url, href)
                
                # Normalize the URL
                normalized_link = self.normalize_url(absolute_url)
                
                if self.debug:
                    console.print(f"[dim]Checking link: {href} -> {normalized_link}[/dim]")
                
                # Check if we should crawl it
                if normalized_link.startswith(self.base_url) and self.should_crawl_url(normalized_link):
                    links.append(normalized_link)
            
            # Remove duplicates while preserving order
            links = list(dict.fromkeys(links))
            
            # Store page data with raw soup for later processing
            self.content_data.append({
                'url': normalized_url,
                'space': self.determine_space(normalized_url),
                'title': title,
                'soup': soup,  # Store the soup object for later processing
                'links': links
            })
            
            return links
            
        except Exception as e:
            console.print(f"[red]Error crawling {normalized_url}:[/red] {e}")
            return []
    
    def crawl_all(self, start_urls):
        """Crawl all pages using breadth-first search to ensure complete coverage"""
        # Record start time
        start_time = datetime.now()
        
        # Normalize start URLs
        normalized_starts = [self.normalize_url(url) for url in start_urls]
        
        # Use deque for efficient BFS
        url_queue = deque(normalized_starts)
        queued_urls = set(normalized_starts)  # Track what's been queued
        
        # Statistics
        crawl_stats = {
            'total_links_found': 0,
            'duplicate_links_skipped': 0,
            'out_of_scope_skipped': 0
        }
        
        console.print(f"[yellow]Starting BFS crawl from {len(normalized_starts)} seed URLs[/yellow]")
        console.print(f"[dim]Start time: {start_time.strftime('%H:%M:%S')}[/dim]")
        
        with console.status("[bold green]Crawling...") as status:
            while url_queue:
                # Get next URL from queue (FIFO for BFS)
                current_url = url_queue.popleft()
                
                # Skip if already visited (shouldn't happen with our logic, but safety check)
                if current_url in self.visited_urls:
                    crawl_stats['duplicate_links_skipped'] += 1
                    continue
                
                status.update(f"[bold green]Crawling... Queue: {len(url_queue)} | Visited: {len(self.visited_urls)}")
                
                # Crawl the page and get new links
                new_links = self.crawl_page(current_url)
                crawl_stats['total_links_found'] += len(new_links)
                
                # Add new links to queue
                for link in new_links:
                    if link not in queued_urls and link not in self.visited_urls:
                        url_queue.append(link)
                        queued_urls.add(link)
                    else:
                        crawl_stats['duplicate_links_skipped'] += 1
                
                # Show progress every 10 pages
                if len(self.visited_urls) % 10 == 0:
                    console.print(f"[dim]Progress: {len(self.visited_urls)} pages crawled, {len(url_queue)} in queue[/dim]")
        
        # Final statistics with timing
        end_time = datetime.now()
        duration = end_time - start_time
        
        console.print(f"\n[green]Crawl complete![/green]")
        console.print(f"[dim]Completed at: {end_time.strftime('%H:%M:%S')} (Duration: {duration})[/dim]")
        console.print(f"[blue]Statistics:[/blue]")
        console.print(f"  • Pages crawled: {len(self.visited_urls)}")
        console.print(f"  • Total links found: {crawl_stats['total_links_found']}")
        console.print(f"  • Duplicate links skipped: {crawl_stats['duplicate_links_skipped']}")
        console.print(f"  • Unique pages by space:")
        
        space_counts = defaultdict(int)
        for page in self.content_data:
            space_counts[page['space']] += 1
        
        for space, count in space_counts.items():
            console.print(f"    - {space}: {count} pages")
    
    def clean_content(self, soup):
        """Remove navigation, ads, footers while preserving semantic content"""
        # Create a copy to avoid modifying the original
        soup_copy = BeautifulSoup(str(soup), 'html.parser')
        
        # Remove unwanted elements
        for selector in self.REMOVE_SELECTORS:
            for element in soup_copy.select(selector):
                element.decompose()
        
        # Clean but don't remove certain elements
        for selector in self.CLEAN_SELECTORS:
            for element in soup_copy.select(selector):
                element.decompose()
        
        return soup_copy
    
    def extract_breadcrumb(self, soup):
        """Extract breadcrumb navigation if available"""
        breadcrumb_selectors = [
            '.breadcrumb', '.breadcrumbs', 'nav[aria-label="breadcrumb"]',
            '[class*="breadcrumb"]', 'ol.breadcrumb', 'ul.breadcrumb'
        ]
        
        for selector in breadcrumb_selectors:
            breadcrumb = soup.select_one(selector)
            if breadcrumb:
                # Extract text from breadcrumb items
                items = []
                for item in breadcrumb.find_all(['li', 'a', 'span']):
                    text = item.get_text(strip=True)
                    if text and text not in items:  # Avoid duplicates
                        items.append(text)
                
                if items:
                    return ' > '.join(items)
        
        return None
    
    def extract_metadata(self, soup, url, title):
        """Extract rich metadata for each chunk"""
        metadata = {
            'page_url': url,
            'page_title': title,
            'space': self.determine_space(url),
            'last_modified': datetime.now().isoformat(),  # Default to now
            'breadcrumb_path': self.extract_breadcrumb(soup),
            'content_type': 'documentation'  # Default
        }
        
        # Try to determine content type from URL or content
        url_lower = url.lower()
        if any(term in url_lower for term in ['api', 'reference', 'endpoint']):
            metadata['content_type'] = 'api'
        elif any(term in url_lower for term in ['guide', 'tutorial', 'getting-started']):
            metadata['content_type'] = 'guide'
        elif any(term in url_lower for term in ['example', 'sample', 'demo']):
            metadata['content_type'] = 'example'
        elif any(term in url_lower for term in ['reference', 'specification']):
            metadata['content_type'] = 'reference'
        
        # Extract related links from the content
        related_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(('http://', 'https://')) and self.base_url in href:
                # Internal link
                related_links.append(href)
            elif not href.startswith(('http://', 'https://', '#', 'javascript:', 'mailto:')):
                # Relative link - make it absolute
                absolute_link = urljoin(url, href)
                if self.base_url in absolute_link:
                    related_links.append(absolute_link)
        
        # Remove duplicates and limit to 10
        metadata['related_links'] = list(dict.fromkeys(related_links))[:10]
        
        return metadata
    
    def extract_sections(self, soup):
        """Identify logical content sections based on headers"""
        sections = []
        
        # Find all headers
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headers:
            # No headers, treat entire content as one section
            content = soup.get_text(separator='\n', strip=True)
            if content:
                sections.append({
                    'level': 0,
                    'title': 'Content',
                    'content': content,
                    'element': soup
                })
            return sections
        
        # Process headers and their content
        for i, header in enumerate(headers):
            level = int(header.name[1])  # h1 -> 1, h2 -> 2, etc.
            title = header.get_text(strip=True)
            
            # Find content between this header and the next
            content_elements = []
            current = header.next_sibling
            
            while current:
                # Stop if we hit another header of same or higher level
                if hasattr(current, 'name'):
                    if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        next_level = int(current.name[1])
                        if next_level <= level:
                            break
                    content_elements.append(current)
                current = current.next_sibling
            
            # Create a new soup with header and its content
            section_soup = BeautifulSoup('<div></div>', 'html.parser')
            section_div = section_soup.div
            section_div.append(BeautifulSoup(str(header), 'html.parser'))
            
            for elem in content_elements:
                if hasattr(elem, 'name'):
                    section_div.append(BeautifulSoup(str(elem), 'html.parser'))
            
            content = section_div.get_text(separator='\n', strip=True)
            
            if content:  # Only add non-empty sections
                sections.append({
                    'level': level,
                    'title': title,
                    'content': content,
                    'element': section_div
                })
        
        return sections
    
    def estimate_tokens(self, text):
        """Rough token counting for chunk sizing (approximation)"""
        # Simple approximation: ~4 characters per token on average
        # This is rough but good enough for chunking purposes
        return len(text) // 4
    
    def create_chunks(self, content, metadata, base_title=""):
        """Split content into logical chunks preserving context"""
        chunks = []
        sections = self.extract_sections(content)
        
        if not sections:
            return chunks
        
        current_chunk = {
            'content': '',
            'sections': [],
            'token_count': 0
        }
        
        for section in sections:
            section_tokens = self.estimate_tokens(section['content'])
            
            # If this section alone is too large, split it
            if section_tokens > self.CHUNK_SIZE_MAX:
                # First, save current chunk if it has content
                if current_chunk['content']:
                    chunks.append(current_chunk)
                    current_chunk = {
                        'content': '',
                        'sections': [],
                        'token_count': 0
                    }
                
                # Split large section into smaller chunks
                paragraphs = section['content'].split('\n\n')
                temp_content = f"# {section['title']}\n\n" if section['title'] != 'Content' else ""
                temp_tokens = self.estimate_tokens(temp_content)
                
                for para in paragraphs:
                    para_tokens = self.estimate_tokens(para)
                    
                    if temp_tokens + para_tokens > self.CHUNK_SIZE_TARGET:
                        # Save current temp chunk
                        if temp_content.strip():
                            chunks.append({
                                'content': temp_content.strip(),
                                'sections': [section['title']],
                                'token_count': temp_tokens
                            })
                        temp_content = f"# {section['title']}\n\n{para}\n\n"
                        temp_tokens = self.estimate_tokens(temp_content)
                    else:
                        temp_content += f"{para}\n\n"
                        temp_tokens += para_tokens
                
                # Add remaining content
                if temp_content.strip():
                    chunks.append({
                        'content': temp_content.strip(),
                        'sections': [section['title']],
                        'token_count': temp_tokens
                    })
                    
            # If adding this section would exceed target, start new chunk
            elif current_chunk['token_count'] + section_tokens > self.CHUNK_SIZE_TARGET:
                # Save current chunk if it meets minimum size
                if current_chunk['token_count'] >= self.CHUNK_SIZE_MIN:
                    chunks.append(current_chunk)
                    # Start new chunk with overlap
                    overlap_content = self._get_overlap_content(current_chunk['content'])
                    current_chunk = {
                        'content': overlap_content + f"\n\n# {section['title']}\n\n{section['content']}",
                        'sections': [section['title']],
                        'token_count': self.estimate_tokens(overlap_content) + section_tokens
                    }
                else:
                    # Current chunk too small, add section anyway
                    if section['title'] != 'Content':
                        current_chunk['content'] += f"\n\n# {section['title']}\n\n{section['content']}"
                    else:
                        current_chunk['content'] += f"\n\n{section['content']}"
                    current_chunk['sections'].append(section['title'])
                    current_chunk['token_count'] += section_tokens
            else:
                # Add section to current chunk
                if section['title'] != 'Content':
                    current_chunk['content'] += f"\n\n# {section['title']}\n\n{section['content']}"
                else:
                    current_chunk['content'] += f"\n\n{section['content']}"
                current_chunk['sections'].append(section['title'])
                current_chunk['token_count'] += section_tokens
        
        # Add final chunk if it has content
        if current_chunk['content'].strip():
            chunks.append(current_chunk)
        
        # Add metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk['metadata'] = metadata.copy()
            chunk['metadata']['chunk_index'] = i + 1
            chunk['metadata']['total_chunks'] = len(chunks)
            chunk['metadata']['section_titles'] = chunk['sections']
            
            # Clean up content
            chunk['content'] = chunk['content'].strip()
        
        return chunks
    
    def _get_overlap_content(self, content):
        """Get the last N tokens of content for overlap"""
        words = content.split()
        overlap_words = self.CHUNK_OVERLAP * 4 // 5  # Rough conversion from tokens to words
        if len(words) > overlap_words:
            return ' '.join(words[-overlap_words:])
        return content
    
    def process_single_page(self, page_data):
        """Process one page into chunks"""
        url = page_data['url']
        title = page_data['title']
        soup = page_data['soup']
        
        console.print(f"[blue]Processing:[/blue] {url}")
        
        # Clean the content
        clean_soup = self.clean_content(soup)
        
        # Extract metadata
        metadata = self.extract_metadata(soup, url, title)
        
        # Create chunks
        chunks = self.create_chunks(clean_soup, metadata, title)
        
        return chunks
    
    def save_chunk(self, chunk, space, page_title):
        """Save individual chunk to file"""
        # Create directory structure
        space_dir = self.output_dir / space
        space_dir.mkdir(exist_ok=True)
        
        # Create a safe filename
        safe_title = re.sub(r'[^\w\s-]', '', page_title.lower())
        safe_title = re.sub(r'[-\s]+', '-', safe_title)[:50]
        
        chunk_index = chunk['metadata']['chunk_index']
        filename = f"{safe_title}-{chunk_index:02d}.md"
        filepath = space_dir / filename
        
        # Prepare frontmatter
        frontmatter = {
            'title': chunk['metadata'].get('section_titles', [''])[0] if chunk['metadata'].get('section_titles') else page_title,
            'page_url': chunk['metadata']['page_url'],
            'space': chunk['metadata']['space'],
            'breadcrumb': chunk['metadata'].get('breadcrumb_path', ''),
            'content_type': chunk['metadata']['content_type'],
            'chunk_index': chunk['metadata']['chunk_index'],
            'total_chunks': chunk['metadata']['total_chunks'],
            'token_count': chunk['token_count']
        }
        
        # Add related pages if any
        if chunk['metadata'].get('related_links'):
            frontmatter['related_links'] = chunk['metadata']['related_links']
        
        # Write file with YAML frontmatter
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("---\n")
            yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
            f.write("---\n\n")
            f.write(chunk['content'])
        
        return str(filepath)
    
    def process_all_pages(self):
        """Main processing orchestrator"""
        console.print(f"\n[yellow]Processing {len(self.content_data)} pages into RAG chunks...[/yellow]")
        
        all_chunks = []
        chunk_files = []
        
        for page_data in track(self.content_data, description="Processing pages"):
            chunks = self.process_single_page(page_data)
            
            for chunk in chunks:
                # Save chunk to file
                filepath = self.save_chunk(
                    chunk, 
                    chunk['metadata']['space'],
                    page_data['title']
                )
                chunk_files.append({
                    'filepath': filepath,
                    'url': page_data['url'],
                    'space': chunk['metadata']['space'],
                    'chunk_index': chunk['metadata']['chunk_index'],
                    'total_chunks': chunk['metadata']['total_chunks']
                })
                all_chunks.append(chunk)
        
        console.print(f"[green]✓ Processed {len(all_chunks)} chunks from {len(self.content_data)} pages[/green]")
        
        return chunk_files
    
    def generate_index(self, chunk_files):
        """Create sitemap/index of all chunks"""
        console.print("[yellow]Generating index...[/yellow]")
        
        index_path = self.output_dir / "index.md"
        
        # Group files by space
        files_by_space = defaultdict(list)
        for file_info in chunk_files:
            files_by_space[file_info['space']].append(file_info)
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# RAG Documentation Index\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"Total chunks: {len(chunk_files)}\n\n")
            
            for space, files in sorted(files_by_space.items()):
                f.write(f"\n## {space}\n\n")
                
                # Group by URL
                files_by_url = defaultdict(list)
                for file_info in files:
                    files_by_url[file_info['url']].append(file_info)
                
                for url, url_files in sorted(files_by_url.items()):
                    f.write(f"\n### {url}\n")
                    f.write(f"Chunks: {len(url_files)}\n\n")
                    
                    for file_info in sorted(url_files, key=lambda x: x['chunk_index']):
                        relative_path = os.path.relpath(file_info['filepath'], self.output_dir)
                        f.write(f"- [{relative_path}]({relative_path}) (chunk {file_info['chunk_index']}/{file_info['total_chunks']})\n")
        
        console.print(f"[green]✓ Index generated at {index_path}[/green]")


def main():
    """Main function that runs the entire processing pipeline"""
    # Get JWT token
    JWT_TOKEN = input("Enter your JWT token: ")
    
    # Ask about debug mode
    debug_mode = input("Enable debug mode? (y/n): ").lower() == 'y'
    
    # Ask about output directory
    output_dir = input("Output directory (default: rag_output): ").strip()
    if not output_dir:
        output_dir = "rag_output"
    
    # Initialize processor
    console.print("[blue]Initializing RAG processor...[/blue]")
    processor = GK8RagProcessor(JWT_TOKEN, output_dir=output_dir, debug=debug_mode)
    
    # Get URLs to crawl
    console.print("\n[yellow]Enter URLs to crawl (one per line, empty line to finish):[/yellow]")
    console.print("[dim]Default URLs if none provided:[/dim]")
    console.print("[dim]  - https://docs.gk8.io[/dim]")
    console.print("[dim]  - https://docs.gk8.io/api-v15[/dim]")
    
    start_urls = []
    while True:
        url = input("> ").strip()
        if not url:
            break
        if url.startswith("http"):
            start_urls.append(url)
        else:
            console.print(f"[red]Invalid URL: {url}. URLs must start with http:// or https://[/red]")
    
    # Use default URLs if none provided
    if not start_urls:
        start_urls = [
            "https://docs.gk8.io",  # General space
            "https://docs.gk8.io/api-v15"  # API v15 space
        ]
        console.print("\n[dim]Using default URLs.[/dim]")
    
    console.print("[green]Starting GK8 RAG document processing...[/green]")
    console.print(f"[yellow]Output directory:[/yellow] {output_dir}")
    console.print(f"[yellow]Debug mode:[/yellow] {'Enabled' if debug_mode else 'Disabled'}")
    console.print(f"[yellow]Targeting:[/yellow]")
    for url in start_urls:
        console.print(f"  - {url}")
    
    # Step 1: Crawl all pages
    console.print("\n[blue]Step 1: Crawling pages...[/blue]")
    processor.crawl_all(start_urls)
    
    # Step 2: Process content into chunks
    console.print("\n[blue]Step 2: Processing content into RAG chunks...[/blue]")
    chunk_files = processor.process_all_pages()
    
    # Step 3: Generate index
    console.print("\n[blue]Step 3: Generating index...[/blue]")
    processor.generate_index(chunk_files)
    
    console.print("\n[green]Processing complete![/green]")
    console.print(f"RAG-ready documentation saved to: {output_dir}/")
    console.print("You can now import these markdown files into Msty's Knowledge Stack.")


# This is the entry point when running the script
if __name__ == "__main__":
    main()