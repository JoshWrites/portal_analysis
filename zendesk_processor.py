#!/usr/bin/env python3
"""
Zendesk Help Center Processor
Takes browser extension JSON output and generates:
1. Sitemap with structure, titles, and dates
2. Scraped content in directory structure with attachments
3. Ollama-powered analysis for single sourcing and image reuse
"""

import json
import os
import re
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
from collections import defaultdict
import ollama
from rich.console import Console
from rich.progress import track
import hashlib
from PIL import Image
import io
import imagehash

console = Console()

class ZendeskProcessor:
    def __init__(self, json_file_path, output_dir="processed_content", ollama_model="llava"):
        self.json_file_path = json_file_path
        self.output_dir = Path(output_dir)
        self.ollama_model = ollama_model
        self.ollama_options = {"num_ctx": 8192}
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "content").mkdir(exist_ok=True)
        (self.output_dir / "attachments").mkdir(exist_ok=True)
        
        # Load crawled data
        self.crawled_data = self.load_crawled_data()
        
        # Processed data structures
        self.hierarchy = defaultdict(lambda: defaultdict(list))
        self.image_hashes = defaultdict(list)
        self.content_hashes = defaultdict(list)
        
    def load_crawled_data(self):
        """Load the JSON data from the browser extension"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            console.print(f"[green]Loaded {len(data)} pages from {self.json_file_path}[/green]")
            return data
        except Exception as e:
            console.print(f"[red]Error loading JSON file: {e}[/red]")
            return []
    
    def extract_hierarchy_from_url(self, url):
        """Extract category/section/article hierarchy from URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        hierarchy = {"category": None, "section": None, "article": None}
        
        # Category: /hc/en-us/categories/123-category-name
        category_match = re.search(r'/categories/(\d+)-([\w-]+)', path)
        if category_match:
            hierarchy["category"] = {
                "id": category_match.group(1),
                "name": category_match.group(2).replace('-', ' ')
            }
        
        # Section: /hc/en-us/sections/456-section-name
        section_match = re.search(r'/sections/(\d+)-([\w-]+)', path)
        if section_match:
            hierarchy["section"] = {
                "id": section_match.group(1),
                "name": section_match.group(2).replace('-', ' ')
            }
        
        # Article: /hc/en-us/articles/789-article-title
        article_match = re.search(r'/articles/(\d+)-([\w-]+)', path)
        if article_match:
            hierarchy["article"] = {
                "id": article_match.group(1),
                "name": article_match.group(2).replace('-', ' ')
            }
        
        return hierarchy
    
    def organize_by_hierarchy(self):
        """Organize pages by category/section/article hierarchy"""
        console.print("[blue]Organizing content by hierarchy...[/blue]")
        
        for page in self.crawled_data:
            hierarchy = self.extract_hierarchy_from_url(page['url'])
            
            category = hierarchy.get('category', {}).get('name', 'Uncategorized')
            section = hierarchy.get('section', {}).get('name', 'General')
            article = hierarchy.get('article', {}).get('name', 'Unknown')
            
            # Store in hierarchy structure
            if article != 'Unknown':
                self.hierarchy[category][section].append({
                    'title': page.get('title', 'Untitled'),
                    'url': page['url'],
                    'last_updated': page.get('metadata', {}).get('lastUpdated'),
                    'content': page.get('content', ''),
                    'images': page.get('images', []),
                    'hierarchy': hierarchy
                })
            elif section != 'General':
                # This is a section page
                self.hierarchy[category][section].append({
                    'title': page.get('title', 'Untitled'),
                    'url': page['url'],
                    'last_updated': page.get('metadata', {}).get('lastUpdated'),
                    'content': page.get('content', ''),
                    'images': page.get('images', []),
                    'hierarchy': hierarchy,
                    'is_section': True
                })
            else:
                # This is a category page
                self.hierarchy[category]['General'].append({
                    'title': page.get('title', 'Untitled'),
                    'url': page['url'],
                    'last_updated': page.get('metadata', {}).get('lastUpdated'),
                    'content': page.get('content', ''),
                    'images': page.get('images', []),
                    'hierarchy': hierarchy,
                    'is_category': True
                })
    
    def generate_sitemap(self):
        """Generate sitemap with structure, titles, and dates"""
        console.print("[blue]Generating sitemap...[/blue]")
        
        sitemap_file = self.output_dir / "sitemap.md"
        
        with open(sitemap_file, 'w', encoding='utf-8') as f:
            f.write("# Zendesk Help Center Sitemap\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total pages: {len(self.crawled_data)}\n\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n\n")
            total_pages = len(self.crawled_data)
            pages_with_dates = sum(1 for page in self.crawled_data 
                                 if page.get('metadata', {}).get('lastUpdated'))
            
            f.write(f"- **Total pages:** {total_pages}\n")
            f.write(f"- **Pages with dates:** {pages_with_dates}\n")
            f.write(f"- **Date coverage:** {(pages_with_dates/total_pages*100):.1f}%\n")
            f.write(f"- **Categories:** {len(self.hierarchy)}\n")
            
            total_sections = sum(len(sections) for sections in self.hierarchy.values())
            f.write(f"- **Sections:** {total_sections}\n\n")
            
            # Portal structure with articles
            f.write("## Portal Structure with Articles\n\n")
            
            for category, sections in sorted(self.hierarchy.items()):
                f.write(f"### {category}\n\n")
                
                for section_name, articles in sections.items():
                    if section_name != "General":
                        f.write(f"#### {section_name}\n\n")
                    
                    f.write("| Title | Last Updated | URL |\n")
                    f.write("|-------|--------------|-----|\n")
                    
                    # Sort articles by last updated date (newest first)
                    sorted_articles = sorted(
                        articles, 
                        key=lambda x: x.get('last_updated') or '1900-01-01',
                        reverse=True
                    )
                    
                    for article in sorted_articles:
                        title = article['title']
                        last_updated = article.get('last_updated') or "Unknown"
                        url = article['url']
                        f.write(f"| {title} | {last_updated} | {url} |\n")
                    
                    f.write("\n")
    
    def save_content_with_attachments(self):
        """Save content as markdown files with directory structure and attachments"""
        console.print("[blue]Saving content with attachments...[/blue]")
        
        for category, sections in self.hierarchy.items():
            category_dir = self.output_dir / "content" / self.sanitize_filename(category)
            category_dir.mkdir(parents=True, exist_ok=True)
            
            for section_name, articles in sections.items():
                if section_name != "General":
                    section_dir = category_dir / self.sanitize_filename(section_name)
                    section_dir.mkdir(exist_ok=True)
                else:
                    section_dir = category_dir
                
                for article in articles:
                    if article.get('is_category') or article.get('is_section'):
                        continue  # Skip category/section pages for now
                    
                    # Create safe filename
                    title = article['title']
                    safe_title = self.sanitize_filename(title)
                    
                    # Add date prefix if available
                    if article.get('last_updated'):
                        try:
                            date_obj = datetime.strptime(article['last_updated'][:10], '%Y-%m-%d')
                            filename = f"{date_obj.strftime('%Y-%m-%d')}_{safe_title}.md"
                        except:
                            filename = f"{safe_title}.md"
                    else:
                        filename = f"{safe_title}.md"
                    
                    # Create article directory
                    article_dir = section_dir / safe_title
                    article_dir.mkdir(exist_ok=True)
                    
                    # Save markdown content
                    markdown_file = article_dir / filename
                    with open(markdown_file, 'w', encoding='utf-8') as f:
                        f.write(f"# {title}\n\n")
                        f.write(f"**URL:** {article['url']}\n")
                        f.write(f"**Category:** {category}\n")
                        if section_name != "General":
                            f.write(f"**Section:** {section_name}\n")
                        f.write(f"**Last Updated:** {article.get('last_updated', 'Unknown')}\n\n")
                        f.write("## Content\n\n")
                        f.write(article['content'])
                    
                    
    
    def sanitize_filename(self, filename):
        """Create a safe filename"""
        # Remove invalid characters
        safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove extra spaces and dashes
        safe = re.sub(r'[-\s]+', '-', safe.strip())
        return safe
    
    def calculate_image_hash(self, image_data):
        """Calculate perceptual hash of image"""
        try:
            img = Image.open(io.BytesIO(image_data))
            return str(imagehash.average_hash(img))
        except:
            return hashlib.md5(image_data).hexdigest()
    
    def analyze_with_ollama(self, prompt, content):
        """Use Ollama to analyze content"""
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{
                    'role': 'user',
                    'content': f"{prompt}\n\nContent:\n{content[:3000]}"
                }],
                options=self.ollama_options
            )
            return response['message']['content']
        except Exception as e:
            console.print(f"[red]Ollama error: {e}[/red]")
            return None
    
    def find_single_source_opportunities(self):
        """Find content that could be single-sourced"""
        console.print("[blue]Analyzing for single-source opportunities...[/blue]")
        
        # Group content by similarity
        content_groups = defaultdict(list)
        
        for page in self.crawled_data:
            content = page.get('content', '')
            if len(content) < 100:  # Skip very short content
                continue
            
            # Create a simple hash of the first 500 characters
            content_hash = hashlib.md5(content[:500].encode()).hexdigest()[:8]
            content_groups[content_hash].append({
                'url': page['url'],
                'title': page.get('title', 'Untitled'),
                'content': content[:200] + '...' if len(content) > 200 else content
            })
        
        # Find groups with multiple similar pages
        single_source_candidates = []
        
        for hash_val, pages in content_groups.items():
            if len(pages) > 1:
                # Use Ollama to analyze similarity
                prompt = f"""
                Analyze these {len(pages)} pages and determine if they contain similar content 
                that could be single-sourced. Look for:
                - Installation instructions
                - Configuration steps  
                - API examples
                - Code snippets
                - Step-by-step procedures
                
                Pages:
                {chr(10).join(f"- {p['title']} ({p['url']})" for p in pages)}
                
                Content samples:
                {chr(10).join(f"Page {i+1}: {p['content']}" for i, p in enumerate(pages))}
                
                Answer with YES or NO and explain why.
                """
                
                analysis = self.analyze_with_ollama(prompt, "")
                if analysis and "YES" in analysis.upper():
                    single_source_candidates.append({
                        'pages': pages,
                        'analysis': analysis,
                        'hash': hash_val
                    })
        
        return single_source_candidates
    
    def find_image_reuse(self):
        """Find images that are reused across articles"""
        console.print("[blue]Analyzing image reuse...[/blue]")
        
        image_reuse = []
        
        for img_hash, images in self.image_hashes.items():
            if len(images) > 1:
                image_reuse.append({
                    'hash': img_hash,
                    'count': len(images),
                    'images': images
                })
        
        return image_reuse
    
    def generate_analysis_report(self):
        """Generate comprehensive analysis report"""
        console.print("[blue]Generating analysis report...[/blue]")
        
        # Find single-source opportunities
        single_source = self.find_single_source_opportunities()
        
        # Find image reuse
        image_reuse = self.find_image_reuse()
        
        # Generate report
        report_file = self.output_dir / "analysis_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Zendesk Help Center Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Single-source opportunities
            f.write("## Single-Source Opportunities\n\n")
            if single_source:
                f.write(f"Found {len(single_source)} potential single-source opportunities:\n\n")
                for i, candidate in enumerate(single_source, 1):
                    f.write(f"### Opportunity {i}\n\n")
                    f.write("**Pages with similar content:**\n")
                    for page in candidate['pages']:
                        f.write(f"- {page['title']} ({page['url']})\n")
                    f.write(f"\n**Analysis:** {candidate['analysis']}\n\n")
            else:
                f.write("No single-source opportunities found.\n\n")
            
            # Image reuse
            f.write("## Image Reuse Analysis\n\n")
            if image_reuse:
                f.write(f"Found {len(image_reuse)} images used multiple times:\n\n")
                for i, reuse in enumerate(image_reuse, 1):
                    f.write(f"### Image {i} (used {reuse['count']} times)\n\n")
                    for img in reuse['images']:
                        f.write(f"- **{img['article']}** ({img['url']})\n")
                        if img['alt']:
                            f.write(f"  - Alt text: {img['alt']}\n")
                    f.write("\n")
            else:
                f.write("No image reuse found.\n\n")
        
        console.print(f"[green]Analysis report saved to {report_file}[/green]")
    
    def process_all(self):
        """Run the complete processing pipeline"""
        console.print("[green]Starting Zendesk content processing...[/green]")
        
        # Step 1: Organize by hierarchy
        self.organize_by_hierarchy()
        
        # Step 2: Generate sitemap
        self.generate_sitemap()
        
        # Step 3: Save content with attachments
        self.save_content_with_attachments()
        
        # Step 4: Generate analysis report
        self.generate_analysis_report()
        
        console.print(f"\n[green]Processing complete![/green]")
        console.print(f"Output directory: {self.output_dir}")
        console.print("Files generated:")
        console.print(f"  - {self.output_dir}/sitemap.md")
        console.print(f"  - {self.output_dir}/content/ (organized markdown files)")
        console.print(f"  - {self.output_dir}/analysis_report.md")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        console.print("[red]Usage: python zendesk_processor.py <json_file> [output_dir][/red]")
        console.print("Example: python zendesk_processor.py zendesk_crawled_data.json processed_content")
        return
    
    json_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "processed_content"
    
    if not os.path.exists(json_file):
        console.print(f"[red]JSON file not found: {json_file}[/red]")
        return
    
    processor = ZendeskProcessor(json_file, output_dir)
    processor.process_all()

if __name__ == "__main__":
    main() 