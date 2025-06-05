#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import ollama
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
import re
from collections import defaultdict, deque
import imagehash
from PIL import Image
import io
import hashlib
from rich.console import Console
from rich.progress import track
from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

console = Console()

class GK8DocAnalyzer:
    def __init__(self, jwt_token, ollama_model="llama3.2-vision:11b", debug=False):
        self.jwt_token = jwt_token
        self.base_url = "https://docs.gk8.io"
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "User-Agent": "GK8-Doc-Analyzer/1.0"
        }
        self.visited_urls = set()
        self.content_data = []
        self.image_data = []
        self.ollama_model = ollama_model
        self.ollama_options = {
            "num_ctx": 8192  # Context size for Ollama
        }
        self.debug = debug
        
        # URL patterns to exclude (add more as needed)
        self.exclude_patterns = [
            r'/print/',  # Print versions
            r'/pdf/',    # PDF versions
            r'\.(pdf|zip|tar|gz)$',  # File downloads
        ]
        
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
            console.print("[red]Cannot analyze JavaScript content without browser automation[/red]")
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
    
    def _crawl_with_requests(self, url):
        """Fallback crawl using requests (session cookies not available, will likely fail)"""
        try:
            console.print(f"[yellow]Warning: Using requests fallback - session cookies not available[/yellow]")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            if self.debug:
                console.print(f"[dim]Requests response: {response.status_code}, content length: {len(response.content)}[/dim]")
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except Exception as e:
            console.print(f"[red]Requests crawl error for {url}:[/red] {e}")
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
        # (add more as you discover them in your portal)
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
            
    def crawl_page(self, url):
        """Crawl a single page"""
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
                soup = self._crawl_with_requests(normalized_url)
            
            if not soup:
                return {'url': normalized_url, 'title': '', 'content': '', 'images': [], 'links': []}
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
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
                elif self.debug:
                    console.print(f"[dim]Skipped: {normalized_link} (base_url check: {normalized_link.startswith(self.base_url)}, should_crawl: {self.should_crawl_url(normalized_link)})[/dim]")
            
            # Remove duplicates while preserving order
            links = list(dict.fromkeys(links))
            
            # Extract images
            images = []
            for img in soup.find_all('img'):
                img_url = urljoin(normalized_url, img.get('src', ''))
                images.append({
                    'url': img_url,
                    'alt': img.get('alt', ''),
                    'page_url': normalized_url
                })
            
            # Extract Mermaid diagrams
            mermaid_diagrams = self.extract_mermaid_diagrams(soup, normalized_url)
            
            # Store page data
            self.content_data.append({
                'url': normalized_url,
                'space': self.determine_space(normalized_url),
                'content': text_content,
                'links': links,
                'images': images,
                'mermaid_diagrams': mermaid_diagrams,
                'title': soup.find('title').text if soup.find('title') else ''
            })
            
            return links
            
        except Exception as e:
            console.print(f"[red]Error crawling {normalized_url}:[/red] {e}")
            return []
    
    def extract_mermaid_diagrams(self, soup, page_url):
        """Extract and analyze Mermaid diagrams from the page"""
        mermaid_diagrams = []
        
        # Common patterns for Mermaid diagrams
        # Pattern 1: <div class="mermaid">
        for div in soup.find_all('div', class_='mermaid'):
            mermaid_diagrams.append({
                'type': 'div.mermaid',
                'content': div.get_text(strip=True),
                'page_url': page_url
            })
        
        # Pattern 2: <pre><code class="language-mermaid">
        for code in soup.find_all('code', class_='language-mermaid'):
            mermaid_diagrams.append({
                'type': 'code.language-mermaid',
                'content': code.get_text(strip=True),
                'page_url': page_url
            })
        
        # Pattern 3: ```mermaid code blocks (in markdown)
        for pre in soup.find_all('pre'):
            text = pre.get_text(strip=True)
            if text.startswith('mermaid') or 'graph' in text or 'sequenceDiagram' in text:
                mermaid_diagrams.append({
                    'type': 'pre.mermaid',
                    'content': text,
                    'page_url': page_url
                })
        
        # Analyze diagram types
        for diagram in mermaid_diagrams:
            content = diagram['content']
            
            # Detect diagram type
            if 'graph TD' in content or 'graph LR' in content:
                diagram['diagram_type'] = 'flowchart'
            elif 'sequenceDiagram' in content:
                diagram['diagram_type'] = 'sequence'
            elif 'classDiagram' in content:
                diagram['diagram_type'] = 'class'
            elif 'stateDiagram' in content:
                diagram['diagram_type'] = 'state'
            elif 'gantt' in content:
                diagram['diagram_type'] = 'gantt'
            elif 'pie title' in content:
                diagram['diagram_type'] = 'pie'
            elif 'erDiagram' in content:
                diagram['diagram_type'] = 'er'
            else:
                diagram['diagram_type'] = 'unknown'
            
            # Calculate a simple hash for comparison
            diagram['hash'] = hashlib.md5(content.encode()).hexdigest()[:8]
        
        return mermaid_diagrams
    
    def _check_crawl_coverage(self):
        """Check for potential crawl issues"""
        console.print("\n[yellow]Checking crawl coverage...[/yellow]")
        
        # Check for orphaned pages (pages that were linked but not crawled)
        all_linked_urls = set()
        for page in self.content_data:
            all_linked_urls.update(page['links'])
        
        # Find URLs that were linked but not visited
        missed_urls = all_linked_urls - self.visited_urls
        
        if missed_urls:
            console.print(f"[red]Warning: {len(missed_urls)} URLs were linked but not crawled:[/red]")
            for url in list(missed_urls)[:5]:  # Show first 5
                console.print(f"  - {url}")
            if len(missed_urls) > 5:
                console.print(f"  ... and {len(missed_urls) - 5} more")
        else:
            console.print("[green]✓ All linked pages were successfully crawled[/green]")
        
        # Check for potential infinite paths
        path_depths = defaultdict(list)
        for url in self.visited_urls:
            path = urlparse(url).path
            depth = path.count('/')
            path_depths[depth].append(url)
        
        max_depth = max(path_depths.keys()) if path_depths else 0
        if max_depth > 10:
            console.print(f"[yellow]Note: Found very deep paths (max depth: {max_depth})[/yellow]")
            console.print("  Deepest URLs:")
            for url in path_depths[max_depth][:3]:
                console.print(f"  - {url}")
    
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
        
        # Detect potential missed pages
        self._check_crawl_coverage()
    
    def analyze_with_ollama(self, prompt, content):
        """Use Ollama to analyze content"""
        try:
            response = ollama.chat(
                model=self.ollama_model, 
                messages=[{
                    'role': 'user',
                    'content': f"{prompt}\n\nContent:\n{content[:3000]}"  # Limit content length
                }],
                options=self.ollama_options
            )
            return response['message']['content']
        except Exception as e:
            console.print(f"[red]Ollama error:[/red] {e}")
            return None
    
    def analyze_image_with_vision(self, image_path_or_url, prompt):
        """Use Llama 3.2 Vision to analyze images directly"""
        try:
            # Download image if it's a URL
            if image_path_or_url.startswith('http'):
                response = requests.get(image_path_or_url, headers=self.headers, timeout=10)
                image_data = response.content
            else:
                with open(image_path_or_url, 'rb') as f:
                    image_data = f.read()
            
            # Use Ollama's vision capabilities
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_data]  # Pass image directly to vision model
                }],
                options=self.ollama_options
            )
            return response['message']['content']
        except Exception as e:
            console.print(f"[red]Vision analysis error:[/red] {e}")
            return None
    
    def _extract_sections(self, content):
        """Extract sections based on common markdown/HTML headers"""
        sections = []
        
        # Common header patterns
        header_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^(.+)\n[=-]+$',     # Markdown underline headers
            r'<h[1-6][^>]*>(.+?)</h[1-6]>',  # HTML headers
            r'^(?:Installation|Configuration|Setup|Usage|Example|API|Reference|Getting Started|Prerequisites|Requirements|Troubleshooting).*$'  # Common section names
        ]
        
        lines = content.split('\n')
        current_section = {'start': 0, 'content': '', 'header': ''}
        current_pos = 0
        
        for i, line in enumerate(lines):
            current_pos += len(line) + 1  # +1 for newline
            
            # Check if this line is a header
            is_header = False
            header_text = ''
            
            for pattern in header_patterns:
                match = re.match(pattern, line.strip(), re.IGNORECASE | re.MULTILINE)
                if match:
                    is_header = True
                    header_text = match.group(1) if match.groups() else line.strip()
                    break
            
            if is_header and current_section['content'].strip():
                # Save previous section
                sections.append(current_section)
                # Start new section
                current_section = {
                    'start': current_pos,
                    'content': '',
                    'header': header_text
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def find_single_source_candidates(self):
        """Use AI to find content that should be single-sourced - with sliding window hash prefiltering"""
        console.print("\n[yellow]Finding single-source candidates...[/yellow]")
        
        # Step 1: Create sliding window hashes for each page
        console.print("[dim]Step 1: Creating sliding window hashes for deep content comparison...[/dim]")
        
        WINDOW_SIZE = 500  # Characters per window
        STEP_SIZE = 250    # Overlap between windows
        MIN_WINDOW_WORDS = 50  # Minimum words in a window to consider
        
        page_windows = {}
        
        for i, page in enumerate(self.content_data):
            content = page['content'].lower()
            windows = []
            
            # Extract meaningful sections using headers as hints
            sections = self._extract_sections(page['content'])
            
            # Create windows for full content
            for start in range(0, len(content) - WINDOW_SIZE + 1, STEP_SIZE):
                window_text = content[start:start + WINDOW_SIZE]
                word_count = len(window_text.split())
                
                if word_count >= MIN_WINDOW_WORDS:
                    window_hash = hashlib.md5(window_text.encode()).hexdigest()[:16]  # Shorter hash
                    windows.append({
                        'hash': window_hash,
                        'start': start,
                        'text': window_text,
                        'words': set(window_text.split()[:50])  # First 50 words for quick comparison
                    })
            
            # Also hash each section independently
            for section in sections:
                if len(section['content']) > 100:  # Meaningful section
                    section_hash = hashlib.md5(section['content'].lower().encode()).hexdigest()[:16]
                    windows.append({
                        'hash': section_hash,
                        'start': section['start'],
                        'text': section['content'].lower(),
                        'words': set(section['content'].lower().split()[:50]),
                        'is_section': True,
                        'header': section.get('header', '')
                    })
            
            page_windows[i] = {
                'url': page['url'],
                'space': page['space'],
                'windows': windows,
                'content_length': len(content)
            }
            
            if (i + 1) % 50 == 0:
                console.print(f"[dim]Processed {i + 1}/{len(self.content_data)} pages...[/dim]")
        
        # Step 2: Find matching windows between pages
        console.print("[dim]Step 2: Finding matching content windows across pages...[/dim]")
        
        # Build hash lookup for fast comparison
        window_lookup = defaultdict(list)
        for page_idx, page_data in page_windows.items():
            for window in page_data['windows']:
                window_lookup[window['hash']].append({
                    'page_idx': page_idx,
                    'window': window,
                    'url': page_data['url'],
                    'space': page_data['space']
                })
        
        # Find pages with matching windows
        page_pair_matches = defaultdict(lambda: {'matches': 0, 'sections': []})
        total_pages = len(self.content_data)
        
        for hash_val, occurrences in window_lookup.items():
            if len(occurrences) < 2:
                continue
                
            # Check each pair of pages with this matching window
            for i in range(len(occurrences)):
                for j in range(i + 1, len(occurrences)):
                    page1 = occurrences[i]
                    page2 = occurrences[j]
                    
                    # Skip if same space
                    if page1['space'] == page2['space']:
                        continue
                    
                    # Create consistent pair key
                    pair_key = tuple(sorted([page1['page_idx'], page2['page_idx']]))
                    
                    # Track this match
                    page_pair_matches[pair_key]['matches'] += 1
                    
                    # Track section matches specially
                    if page1['window'].get('is_section') or page2['window'].get('is_section'):
                        section_info = {
                            'hash': hash_val,
                            'header1': page1['window'].get('header', ''),
                            'header2': page2['window'].get('header', ''),
                            'preview': page1['window']['text'][:100]
                        }
                        page_pair_matches[pair_key]['sections'].append(section_info)
        
        # Convert to sorted list of potential pairs
        potential_pairs = []
        for (idx1, idx2), match_data in page_pair_matches.items():
            # Calculate similarity score based on matches
            match_count = match_data['matches']
            section_matches = len(match_data['sections'])
            
            # Higher weight for section matches
            similarity_score = min(100, match_count * 5 + section_matches * 20)
            
            if similarity_score >= 20:  # Lower threshold for window-based matching
                potential_pairs.append({
                    'indices': (idx1, idx2),
                    'score': similarity_score,
                    'window_matches': match_count,
                    'section_matches': section_matches,
                    'matched_sections': match_data['sections'][:3]  # Keep top 3 for reference
                })
        
        # Sort by similarity score (highest first)
        potential_pairs.sort(key=lambda x: x['score'], reverse=True)
        
        console.print(f"[green]Found {len(potential_pairs)} potentially similar page pairs out of {total_pages * (total_pages - 1) // 2} total[/green]")
        console.print(f"[green]Reduction: {100 - (len(potential_pairs) * 100 // (total_pages * (total_pages - 1) // 2)):.1f}% fewer AI calls needed[/green]")
        
        # Show some example matches
        if potential_pairs and self.debug:
            console.print("\n[dim]Top matching pairs:[/dim]")
            for pair in potential_pairs[:3]:
                idx1, idx2 = pair['indices']
                console.print(f"[dim]- {self.content_data[idx1]['url'].split('/')[-1]} <-> {self.content_data[idx2]['url'].split('/')[-1]}[/dim]")
                console.print(f"[dim]  Score: {pair['score']}, Windows: {pair['window_matches']}, Sections: {pair['section_matches']}[/dim]")
                if pair['matched_sections']:
                    console.print(f"[dim]  Matched section: {pair['matched_sections'][0]['header1'] or 'content'}[/dim]")
        
        # Step 3: AI analysis only on promising pairs
        candidates = []
        ai_calls_made = 0
        
        with console.status("[bold green]Analyzing similar content pairs with AI...") as status:
            for idx, pair in enumerate(potential_pairs):
                idx1, idx2 = pair['indices']
                page1 = self.content_data[idx1]
                page2 = self.content_data[idx2]
                
                status.update(f"[bold green]AI Analysis {idx+1}/{len(potential_pairs)} (score: {pair['score']}, matches: {pair['window_matches']})")
                
                # Build context-aware prompt
                prompt = f"""
                Compare these two documentation sections and identify if they contain 
                similar content that could be single-sourced. 
                
                IMPORTANT: These pages have {pair['window_matches']} matching content windows"""
                
                if pair['section_matches'] > 0:
                    prompt += f" and {pair['section_matches']} matching sections"
                    if pair['matched_sections']:
                        prompt += f" including: {', '.join(s['header1'] or s['preview'][:30] for s in pair['matched_sections'][:2])}"
                
                prompt += f"""
                
                Look for:
                - Installation instructions
                - Configuration steps
                - API examples
                - Code snippets
                - Step-by-step procedures
                - Troubleshooting guides
                
                Page 1 ({page1['space']}): {page1['url']}
                Content sample: {page1['content'][:1000]}
                
                Page 2 ({page2['space']}): {page2['url']}
                Content sample: {page2['content'][:1000]}
                
                If similar content exists, explain:
                1. What specific sections/content could be consolidated
                2. Estimated overlap percentage
                3. Which parts are identical vs slightly different
                """
                
                analysis = self.analyze_with_ollama(prompt, "")
                ai_calls_made += 1
                
                if analysis and "similar" in analysis.lower():
                    candidates.append({
                        'page1': page1['url'],
                        'page2': page2['url'],
                        'similarity_score': pair['score'],
                        'window_matches': pair['window_matches'],
                        'section_matches': pair['section_matches'],
                        'matched_sections': pair['matched_sections'],
                        'analysis': analysis
                    })
                
                # Update progress
                if ai_calls_made % 10 == 0:
                    console.print(f"[dim]Progress: {ai_calls_made} AI analyses complete, {len(candidates)} candidates found[/dim]")
        
        console.print(f"\n[green]Analysis complete! Made {ai_calls_made} AI calls instead of {total_pages * (total_pages - 1) // 2}[/green]")
        console.print(f"[green]Found {len(candidates)} single-sourcing opportunities[/green]")
        
        return candidates
    
    def find_variable_candidates(self):
        """Find text that should be variables (versions, product names, etc.)"""
        console.print("\n[yellow]Finding variable candidates...[/yellow]")
        
        all_content = "\n".join([page['content'][:500] for page in self.content_data[:10]])
        
        prompt = """
        Analyze this documentation content and identify:
        1. Version numbers that appear multiple times
        2. Product names that should be variables
        3. URLs or endpoints that contain versions
        4. Any other repeated values that should be variables
        
        List each finding with examples and count of occurrences.
        """
        
        return self.analyze_with_ollama(prompt, all_content)
    
    def analyze_images(self):
        """Analyze images for duplication using both hashing and vision AI"""
        console.print("\n[yellow]Analyzing images with vision AI...[/yellow]")
        
        image_hashes = defaultdict(list)
        image_analyses = []
        
        # First pass: collect and hash images
        for page in track(self.content_data, description="Processing images", total=len(self.content_data)):
            for img in page['images']:
                try:
                    # Skip SVG files as PIL can't handle them
                    if img['url'].lower().endswith('.svg'):
                        if self.debug:
                            console.print(f"[dim]Skipping SVG file: {img['url']}[/dim]")
                        continue
                    
                    # Download image
                    response = requests.get(img['url'], headers=self.headers, timeout=10)
                    img_data = Image.open(io.BytesIO(response.content))
                    
                    # Generate perceptual hash
                    hash_val = str(imagehash.average_hash(img_data))
                    
                    image_info = {
                        'url': img['url'],
                        'page': page['url'],
                        'alt': img['alt'],
                        'hash': hash_val
                    }
                    
                    image_hashes[hash_val].append(image_info)
                    
                    # Use vision AI to understand the image content
                    if len(image_analyses) < 20:  # Limit to first 20 for performance
                        vision_prompt = """
                        Analyze this documentation image and describe:
                        1. What type of image is it? (screenshot, diagram, logo, etc.)
                        2. What specific content does it show?
                        3. Could this image be reused in other contexts?
                        4. Are there any version-specific elements visible?
                        Be concise - 3-4 sentences max.
                        """
                        
                        analysis = self.analyze_image_with_vision(img['url'], vision_prompt)
                        if analysis:
                            image_info['ai_analysis'] = analysis
                            image_analyses.append(image_info)
                            
                except Exception as e:
                    console.print(f"[red]Error processing image {img['url']}:[/red] {e}")
        
        # Find duplicates and similar images
        duplicates = {k: v for k, v in image_hashes.items() if len(v) > 1}
        
        # Use AI to find semantically similar images (not just hash duplicates)
        similar_groups = []
        if len(image_analyses) > 1:
            console.print("[blue]Finding semantically similar images...[/blue]")
            
            for i, img1 in enumerate(image_analyses):
                for img2 in image_analyses[i+1:]:
                    if img1.get('ai_analysis') and img2.get('ai_analysis'):
                        prompt = f"""
                        Are these two images similar enough to be consolidated?
                        
                        Image 1: {img1['ai_analysis']}
                        Image 2: {img2['ai_analysis']}
                        
                        Answer with YES or NO and a brief reason.
                        """
                        
                        similarity = self.analyze_with_ollama(prompt, "")
                        if similarity and "YES" in similarity.upper():
                            similar_groups.append({
                                'image1': img1,
                                'image2': img2,
                                'reason': similarity
                            })
        
        return {
            'hash_duplicates': duplicates,
            'vision_insights': image_analyses[:20],  # First 20 analyzed
            'similar_images': similar_groups
        }
    
    def analyze_mermaid_diagrams(self):
        """Analyze Mermaid diagrams for duplication and patterns"""
        console.print("\n[yellow]Analyzing Mermaid diagrams...[/yellow]")
        
        all_diagrams = []
        diagram_hashes = defaultdict(list)
        
        # Collect all diagrams
        for page in self.content_data:
            for diagram in page.get('mermaid_diagrams', []):
                all_diagrams.append(diagram)
                # Group by hash for duplicate detection
                diagram_hashes[diagram['hash']].append({
                    'page': page['url'],
                    'type': diagram['diagram_type'],
                    'content': diagram['content'][:100] + '...' if len(diagram['content']) > 100 else diagram['content']
                })
        
        # Find duplicates
        duplicates = {k: v for k, v in diagram_hashes.items() if len(v) > 1}
        
        # Analyze with AI for semantic similarity
        similar_diagrams = []
        if len(all_diagrams) > 1 and self.ollama_model:
            console.print("[blue]Analyzing diagram similarity with AI...[/blue]")
            
            # Sample up to 10 diagrams for AI analysis
            sample_diagrams = all_diagrams[:10]
            
            for i, diag1 in enumerate(sample_diagrams):
                for diag2 in sample_diagrams[i+1:]:
                    if diag1['hash'] != diag2['hash']:  # Skip exact duplicates
                        prompt = f"""
                        Compare these two Mermaid diagrams and determine if they are similar enough to consolidate:
                        
                        Diagram 1 ({diag1['diagram_type']}):
                        {diag1['content'][:300]}
                        
                        Diagram 2 ({diag2['diagram_type']}):
                        {diag2['content'][:300]}
                        
                        Are these diagrams showing the same or very similar concepts? 
                        Could they be consolidated into a single diagram?
                        Answer with YES or NO and a brief explanation.
                        """
                        
                        analysis = self.analyze_with_ollama(prompt, "")
                        if analysis and "YES" in analysis.upper():
                            similar_diagrams.append({
                                'diagram1': {'page': diag1['page_url'], 'type': diag1['diagram_type']},
                                'diagram2': {'page': diag2['page_url'], 'type': diag2['diagram_type']},
                                'analysis': analysis
                            })
        
        # Statistics by diagram type
        type_counts = defaultdict(int)
        for diagram in all_diagrams:
            type_counts[diagram['diagram_type']] += 1
        
        return {
            'total_diagrams': len(all_diagrams),
            'diagram_types': dict(type_counts),
            'exact_duplicates': duplicates,
            'similar_diagrams': similar_diagrams
        }
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        console.print("\n[green]Generating report...[/green]")
        
        # Perform analyses
        single_source = self.find_single_source_candidates()
        variables = self.find_variable_candidates()
        image_analysis = self.analyze_images()
        mermaid_analysis = self.analyze_mermaid_diagrams()
        
        report = {
            "summary": {
                "total_pages": len(self.visited_urls),
                "spaces_analyzed": list(set([p['space'] for p in self.content_data])),
                "total_images": sum(len(p['images']) for p in self.content_data),
                "total_mermaid_diagrams": mermaid_analysis['total_diagrams']
            },
            "single_source_candidates": single_source,
            "variable_candidates": variables,
            "image_analysis": {
                "hash_duplicates": image_analysis['hash_duplicates'],
                "vision_insights": image_analysis['vision_insights'],
                "consolidation_opportunities": image_analysis['similar_images']
            },
            "mermaid_analysis": mermaid_analysis
        }
        
        # Save report
        with open("gk8_doc_analysis.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Create human-readable summary
        with open("gk8_doc_summary.md", "w") as f:
            f.write("# GK8 Documentation Analysis Report\n\n")
            f.write(f"## Summary\n")
            f.write(f"- Total pages analyzed: {report['summary']['total_pages']}\n")
            f.write(f"- Spaces: {', '.join(report['summary']['spaces_analyzed'])}\n")
            f.write(f"- Total images found: {report['summary']['total_images']}\n")
            f.write(f"- Total Mermaid diagrams found: {report['summary']['total_mermaid_diagrams']}\n\n")
            
            f.write("## Key Findings\n\n")
            
            # Single-source opportunities
            f.write("### Single-Source Opportunities\n")
            if single_source:
                for i, candidate in enumerate(single_source[:5], 1):
                    f.write(f"\n**Opportunity {i}:**\n")
                    f.write(f"- Page 1: `{candidate['page1']}`\n")
                    f.write(f"- Page 2: `{candidate['page2']}`\n")
                    f.write(f"- Analysis: {candidate['analysis']}\n")
            
            # Variable candidates
            f.write("\n### Variable Candidates\n")
            if variables:
                f.write(variables + "\n")
            
            # Image consolidation
            f.write("\n### Image Analysis\n")
            
            # Exact duplicates
            dup_count = sum(len(imgs)-1 for imgs in image_analysis['hash_duplicates'].values())
            f.write(f"\n**Exact Duplicates:** {dup_count} duplicate images found\n")
            
            if image_analysis['hash_duplicates']:
                f.write("\nTop duplicate images:\n")
                for hash_val, images in list(image_analysis['hash_duplicates'].items())[:3]:
                    f.write(f"\n- **{images[0]['url'].split('/')[-1]}** appears {len(images)} times:\n")
                    for img in images[:3]:
                        f.write(f"  - On page: `{img['page']}`\n")
            
            # Vision insights
            if image_analysis['vision_insights']:
                f.write("\n**AI Vision Insights:**\n")
                for img in image_analysis['vision_insights'][:5]:
                    f.write(f"\n- **{img['url'].split('/')[-1]}**\n")
                    f.write(f"  - Location: `{img['page']}`\n")
                    if img.get('ai_analysis'):
                        f.write(f"  - Analysis: {img['ai_analysis']}\n")
            
            # Similar images that could be consolidated
            if image_analysis['similar_images']:
                f.write(f"\n**Consolidation Opportunities:** {len(image_analysis['similar_images'])} similar image pairs found\n")
                for pair in image_analysis['similar_images'][:3]:
                    f.write(f"\n- Could consolidate:\n")
                    f.write(f"  - `{pair['image1']['url'].split('/')[-1]}`\n")
                    f.write(f"  - `{pair['image2']['url'].split('/')[-1]}`\n")
                    f.write(f"  - Reason: {pair['reason']}\n")
            
            # Mermaid diagram analysis
            f.write("\n## Mermaid Diagram Analysis\n")
            
            if mermaid_analysis['total_diagrams'] > 0:
                f.write(f"\n**Total Mermaid diagrams:** {mermaid_analysis['total_diagrams']}\n")
                
                # Diagram types breakdown
                f.write("\n**Diagram types found:**\n")
                for dtype, count in mermaid_analysis['diagram_types'].items():
                    f.write(f"- {dtype}: {count}\n")
                
                # Exact duplicates
                dup_count = sum(len(diagrams)-1 for diagrams in mermaid_analysis['exact_duplicates'].values())
                f.write(f"\n**Exact duplicate diagrams:** {dup_count}\n")
                
                if mermaid_analysis['exact_duplicates']:
                    f.write("\nDuplicate diagrams:\n")
                    for hash_val, diagrams in list(mermaid_analysis['exact_duplicates'].items())[:5]:
                        f.write(f"\n- **{diagrams[0]['type']} diagram** (hash: {hash_val[:8]})\n")
                        f.write(f"  Appears on {len(diagrams)} pages:\n")
                        for diag in diagrams[:3]:
                            f.write(f"  - `{diag['page']}`\n")
                        if len(diagrams) > 3:
                            f.write(f"  - ... and {len(diagrams)-3} more\n")
                
                # Similar diagrams
                if mermaid_analysis['similar_diagrams']:
                    f.write(f"\n**Similar diagrams that could be consolidated:** {len(mermaid_analysis['similar_diagrams'])}\n")
                    for sim in mermaid_analysis['similar_diagrams'][:3]:
                        f.write(f"\n- Could consolidate:\n")
                        f.write(f"  - {sim['diagram1']['type']} on `{sim['diagram1']['page']}`\n")
                        f.write(f"  - {sim['diagram2']['type']} on `{sim['diagram2']['page']}`\n")
                        f.write(f"  - Reason: {sim['analysis'][:100]}...\n")
            else:
                f.write("\nNo Mermaid diagrams found in the documentation.\n")
        
        console.print("[green]Report saved to gk8_doc_analysis.json and gk8_doc_summary.md[/green]")

def main():
    """Main function that runs the entire analysis"""
    # Get JWT token
    JWT_TOKEN = input("Enter your JWT token: ")
    
    # Ask about debug mode
    debug_mode = input("Enable debug mode? (y/n): ").lower() == 'y'
    
    # Initialize analyzer with Llama 3.2 Vision
    console.print("[blue]Initializing analyzer with Llama 3.2 Vision...[/blue]")
    analyzer = GK8DocAnalyzer(JWT_TOKEN, ollama_model="llama3.2-vision:11b", debug=debug_mode)
    
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
    
    console.print("[green]Starting GK8 documentation analysis...[/green]")
    console.print(f"[yellow]Using model:[/yellow] llama3.2-vision:11b with 8K context")
    console.print(f"[yellow]Debug mode:[/yellow] {'Enabled' if debug_mode else 'Disabled'}")
    console.print(f"[yellow]Targeting:[/yellow]")
    for url in start_urls:
        console.print(f"  - {url}")
    
    # Step 1: Crawl all pages
    console.print("\n[blue]Step 1: Crawling pages...[/blue]")
    analyzer.crawl_all(start_urls)
    
    # Step 2: Generate analysis report
    console.print("\n[blue]Step 2: Analyzing content with Vision AI...[/blue]")
    analyzer.generate_report()
    
    console.print("\n[green]Analysis complete![/green]")
    console.print("Check these files for results:")
    console.print("  - gk8_doc_analysis.json (detailed data)")
    console.print("  - gk8_doc_summary.md (human-readable report)")


# This is the entry point when running the script
if __name__ == "__main__":
    main()