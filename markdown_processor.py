#!/usr/bin/env python3
"""
Markdown-based Zendesk Help Center Processor
Takes browser extension markdown export and generates:
1. Sitemap with structure, titles, and dates
2. Content analysis for single sourcing opportunities
3. Ollama-powered analysis for content insights

NEW: Auto-merge functionality for chunked downloads
"""

import os
import re
import json
import zipfile
import glob
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import ollama
from rich.console import Console
from rich.progress import track
import hashlib
from PIL import Image
import io
import imagehash

console = Console()

class MarkdownProcessor:
    def __init__(self, markdown_dir, output_dir=None, ollama_model="llava"):
        self.markdown_dir = Path(markdown_dir)
        # If no output_dir specified, create analysis folder inside the source directory
        if output_dir is None:
            self.output_dir = self.markdown_dir / "analysis"
        else:
            self.output_dir = Path(output_dir)
        
        self.ollama_model = ollama_model
        self.ollama_options = {"num_ctx": 8192}
        
        # Create output directories - put analysis inside the source folder
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "content").mkdir(exist_ok=True)
        (self.output_dir / "attachments").mkdir(exist_ok=True)
        
        # Processed data structures
        self.hierarchy = defaultdict(lambda: defaultdict(list))
        self.content_hashes = defaultdict(list)
        self.all_files = []
        
    def detect_chunk_folders(self, input_dir):
        """
        Find chunk folders in input directory.
        
        Args:
            input_dir (str): Directory to scan
            
        Returns:
            dict: {run_id: [chunk_files]} for each session with multiple chunks
        """
        input_path = Path(input_dir)
        chunk_sessions = defaultdict(list)
        
        # Look for new organized chunk structure: zendesk_chunks/{run_id}/chunk_*.zip
        chunk_dirs = list(input_path.glob("zendesk_chunks/*"))
        
        for chunk_dir in chunk_dirs:
            if chunk_dir.is_dir():
                run_id = chunk_dir.name
                chunk_files = list(chunk_dir.glob("chunk_*.zip"))
                if chunk_files:
                    chunk_sessions[run_id].extend(chunk_files)
        
        # Also look for legacy pattern: zendesk_chunk_{run_id}_*.zip
        legacy_files = list(input_path.glob("zendesk_chunk_*.zip"))
        for legacy_file in legacy_files:
            # Extract run_id from filename: zendesk_chunk_2025-01-23_14-30-45_1.zip
            filename = legacy_file.name
            if filename.startswith("zendesk_chunk_") and filename.endswith(".zip"):
                # Extract run_id (everything between zendesk_chunk_ and the last _)
                parts = filename.replace("zendesk_chunk_", "").replace(".zip", "").split("_")
                if len(parts) >= 2:
                    # Reconstruct run_id (e.g., "2025-01-23_14-30-45")
                    run_id = "_".join(parts[:-1])  # Everything except the chunk number
                    chunk_sessions[run_id].append(legacy_file)
        
        # Filter to only sessions with multiple chunks
        return {run_id: files for run_id, files in chunk_sessions.items() if len(files) > 1}
    
    def extract_session_info(self, chunk_files):
        """Extract session information from chunk files."""
        for chunk_file in chunk_files:
            try:
                with zipfile.ZipFile(chunk_file, 'r') as zip_file:
                    if 'session_info.json' in zip_file.namelist():
                        session_data = zip_file.read('session_info.json').decode('utf-8')
                        return json.loads(session_data)
            except Exception as e:
                console.print(f"[yellow]Warning: Error reading session info from {chunk_file}: {e}[/yellow]")
        return None
    
    def merge_chunk_session(self, run_id, chunk_files, output_dir):
        """
        Merge all chunks for a specific run session.
        
        Args:
            run_id (str): Session identifier
            chunk_files (list): List of chunk file paths
            output_dir (str): Directory for merged output
            
        Returns:
            bool: Success status
        """
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Track all files to avoid duplicates
            all_files = set()
            file_counts = defaultdict(int)
            
            console.print(f"[blue]Merging {len(chunk_files)} chunk files for run {run_id}...[/blue]")
            
            for chunk_file in track(chunk_files, description="Processing chunks"):
                try:
                    with zipfile.ZipFile(chunk_file, 'r') as zip_file:
                        for file_info in zip_file.filelist:
                            # Skip README files from chunks (we'll create a new one)
                            if file_info.filename == 'README.md':
                                continue
                            
                            # Extract file
                            zip_file.extract(file_info, output_dir)
                            all_files.add(file_info.filename)
                            file_counts[file_info.filename] += 1
                            
                except Exception as e:
                    console.print(f"[red]Error processing {chunk_file}: {e}[/red]")
                    return False
            
            # Create merged README
            self.create_merged_readme(run_id, chunk_files, output_dir, file_counts)
            
            # Report duplicates
            duplicates = {f: c for f, c in file_counts.items() if c > 1}
            if duplicates:
                console.print(f"[yellow]Found {len(duplicates)} duplicate files[/yellow]")
                for file_path, count in duplicates.items():
                    console.print(f"[yellow]  {file_path}: {count} copies[/yellow]")
            
            console.print(f"[green]Successfully merged {len(all_files)} unique files[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error merging chunks: {e}[/red]")
            return False
    
    def create_merged_readme(self, run_id, chunk_files, output_dir, file_counts):
        """Create a comprehensive README for the merged output."""
        
        # Extract session info from chunks
        session_info = self.extract_session_info(chunk_files)
        
        readme_content = f"""# Zendesk Help Center - Merged Output

## Summary
- **Run ID:** {run_id}
- **Total Chunk Files:** {len(chunk_files)}
- **Total Unique Articles:** {len(file_counts)}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Output Directory:** {output_dir}
"""
        
        if session_info:
            readme_content += f"""
## Session Information
- **Run ID:** {session_info.get('runId', run_id)}
- **Base URL:** {session_info.get('baseUrl', 'Unknown')}
- **Total Chunks:** {session_info.get('totalChunks', len(chunk_files))}
- **Crawl Started:** {session_info.get('timestamp', 'Unknown')}
"""
        
        readme_content += f"""
## Chunk Files Processed
"""
        
        for chunk_file in chunk_files:
            readme_content += f"- {Path(chunk_file).name}\n"
        
        readme_content += f"""
## File Structure
The merged output maintains the original category/section structure from Zendesk:

```
{output_dir}/
├── API/
│   └── General/
│       └── [API articles...]
├── FAQ/
│   └── General/
│       └── [FAQ articles...]
├── Settings/
│   └── General/
│       └── [Settings articles...]
└── [Other categories...]
```

## Duplicate Files
"""
        
        duplicates = {f: c for f, c in file_counts.items() if c > 1}
        if duplicates:
            readme_content += f"Found {len(duplicates)} files that appeared in multiple chunks:\n"
            for file_path, count in duplicates.items():
                readme_content += f"- {file_path}: {count} copies\n"
        else:
            readme_content += "No duplicate files found.\n"
        
        # Write README
        readme_path = os.path.join(output_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        console.print(f"[green]Created merged README: {readme_path}[/green]")
    
    def auto_merge_chunks(self, input_dir):
        """
        Detect and merge chunk folders in input directory.
        
        Args:
            input_dir (str): Directory to scan for chunks
            
        Returns:
            str: Path to merged directory (or original if no chunks found)
        """
        console.print("[blue]Checking for chunk folders...[/blue]")
        
        # Detect chunk sessions
        chunk_sessions = self.detect_chunk_folders(input_dir)
        
        if not chunk_sessions:
            console.print("[green]No chunk folders detected, proceeding with original directory[/green]")
            return input_dir
        
        console.print(f"[yellow]Found {len(chunk_sessions)} chunk sessions with multiple chunks[/yellow]")
        
        # Process each session
        merged_dirs = []
        for run_id, chunk_files in chunk_sessions.items():
            console.print(f"[blue]Processing session: {run_id} ({len(chunk_files)} chunks)[/blue]")
            
            # Create merged output directory
            merged_dir = Path(input_dir) / f"merged_{run_id}"
            
            if self.merge_chunk_session(run_id, chunk_files, merged_dir):
                merged_dirs.append(merged_dir)
                console.print(f"[green]Successfully merged session {run_id} to {merged_dir}[/green]")
            else:
                console.print(f"[red]Failed to merge session {run_id}[/red]")
        
        if merged_dirs:
            # If we have multiple merged sessions, we need to handle this
            if len(merged_dirs) == 1:
                return str(merged_dirs[0])
            else:
                # Multiple sessions - create a combined directory
                combined_dir = Path(input_dir) / "merged_combined"
                console.print(f"[blue]Combining {len(merged_dirs)} merged sessions...[/blue]")
                
                # Copy all files from merged directories to combined directory
                for merged_dir in merged_dirs:
                    if merged_dir.exists():
                        for file_path in merged_dir.rglob("*"):
                            if file_path.is_file():
                                relative_path = file_path.relative_to(merged_dir)
                                target_path = combined_dir / relative_path
                                target_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(file_path, target_path)
                
                console.print(f"[green]Combined all sessions into {combined_dir}[/green]")
                return str(combined_dir)
        
        # Fallback to original directory
        return input_dir

    def scan_markdown_files(self):
        """Scan all markdown files in the directory structure"""
        console.print("[blue]Scanning markdown files...[/blue]")
        
        for file_path in self.markdown_dir.rglob("*.md"):
            if file_path.name == "README.md":
                continue  # Skip the main README file
                
            self.all_files.append(file_path)
        
        console.print(f"[green]Found {len(self.all_files)} markdown files[/green]")
        return self.all_files
    
    def extract_metadata_from_filename(self, file_path):
        """Extract metadata from the markdown filename"""
        # Example: "Home_–_IRONSCALES.md" -> title: "Home", category: "IRONSCALES"
        filename = file_path.stem  # Remove .md extension
        
        # Split by "–" (em dash) which separates title from category
        if "–" in filename:
            parts = filename.split("–")
            title = parts[0].strip().replace("_", " ")
            category = parts[1].strip() if len(parts) > 1 else "Unknown"
        else:
            title = filename.replace("_", " ")
            category = "Unknown"
        
        return {
            "title": title,
            "category": category,
            "filename": file_path.name,
            "path": str(file_path),
            "relative_path": str(file_path.relative_to(self.markdown_dir))
        }
    
    def extract_content_from_markdown(self, file_path):
        """Extract content and metadata from markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first heading
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem.replace("_", " ")
            
            # Extract URL if present (look for URL pattern in content)
            url_match = re.search(r'\*\*URL:\*\*\s*(https?://[^\s]+)', content)
            url = url_match.group(1) if url_match else None
            
            # Extract last updated date if present
            date_match = re.search(r'\*\*Last Updated:\*\*\s*([^\n]+)', content)
            last_updated = date_match.group(1) if date_match else "Unknown"
            
            # Extract category from path
            path_parts = file_path.relative_to(self.markdown_dir).parts
            category = path_parts[0] if len(path_parts) > 0 else "Uncategorized"
            section = path_parts[1] if len(path_parts) > 1 else "General"
            
            return {
                "title": title,
                "url": url,
                "last_updated": last_updated,
                "category": category,
                "section": section,
                "content": content,
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(self.markdown_dir))
            }
            
        except Exception as e:
            console.print(f"[red]Error reading {file_path}: {e}[/red]")
            return None
    
    def organize_by_hierarchy(self):
        """Organize files by category/section hierarchy"""
        console.print("[blue]Organizing content by hierarchy...[/blue]")
        
        for file_path in track(self.all_files, description="Processing files"):
            metadata = self.extract_content_from_markdown(file_path)
            if metadata:
                category = metadata['category']
                section = metadata['section']
                
                self.hierarchy[category][section].append(metadata)
        
        console.print(f"[green]Organized into {len(self.hierarchy)} categories[/green]")
    
    def generate_sitemap(self):
        """Generate sitemap from the organized content in tree-like format"""
        console.print("[blue]Generating sitemap...[/blue]")
        
        sitemap_file = self.output_dir / "sitemap.md"
        
        with open(sitemap_file, 'w', encoding='utf-8') as f:
            f.write("# Zendesk Help Center Sitemap\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Articles: {len(self.all_files)}\n\n")
            
            # Summary statistics
            total_categories = len(self.hierarchy)
            total_sections = sum(len(sections) for sections in self.hierarchy.values())
            total_articles = len(self.all_files)
            
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Categories:** {total_categories}\n")
            f.write(f"- **Total Sections:** {total_sections}\n")
            f.write(f"- **Total Articles:** {total_articles}\n\n")
            
            # Tree-like structure
            f.write("## Site Structure\n\n")
            f.write("```\n")
            
            # Extract date from folder name (format: zendesk_help_center_2025-07-22 (3))
            folder_name = self.markdown_dir.name
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', folder_name)
            if date_match:
                export_date = date_match.group(1)
                # Convert to human-readable format
                try:
                    parsed_date = datetime.strptime(export_date, '%Y-%m-%d')
                    human_date = parsed_date.strftime('%B %d, %Y')
                except:
                    human_date = export_date
            else:
                human_date = "Unknown"
            
            f.write(f"Data exported: {human_date}\n")
            f.write(f"Articles analyzed: {len(self.all_files)}\n")
            f.write(f"../\n")
            
            for category, sections in sorted(self.hierarchy.items()):
                f.write(f"├── {category}/\n")
                
                for i, (section, articles) in enumerate(sorted(sections.items())):
                    # Check if this is the last section in this category
                    is_last_section = i == len(sections) - 1
                    section_prefix = "└── " if is_last_section else "├── "
                    article_prefix = "    " if is_last_section else "│   "
                    
                    f.write(f"{article_prefix}{section_prefix}{section}/\n")
                    
                    for j, article in enumerate(sorted(articles, key=lambda x: x['title'])):
                        # Check if this is the last article in this section
                        is_last_article = j == len(articles) - 1
                        article_prefix_final = "    " if is_last_section else "│   "
                        article_prefix_final += "    " if is_last_article else "├── "
                        
                        # Truncate title if too long
                        title = article['title']
                        if len(title) > 50:
                            title = title[:47] + "..."
                        
                        # Create relative link to the actual markdown file
                        relative_path = f"../{article['relative_path']}"
                        f.write(f"{article_prefix_final}[{title}.md]({relative_path})\n")
                        
                        # Add metadata as comments
                        if article['last_updated'] != "Unknown":
                            f.write(f"{article_prefix_final}    # Last Updated: {article['last_updated']}\n")
                
                f.write("\n")
            
            f.write("```\n")
        
        console.print(f"[green]Sitemap saved to {sitemap_file}[/green]")
    
    def analyze_with_ollama(self, prompt, content):
        """Analyze content using Ollama"""
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": f"{prompt}\n\nContent:\n{content}"}],
                options=self.ollama_options
            )
            return response['message']['content']
        except Exception as e:
            console.print(f"[red]Ollama analysis failed: {e}[/red]")
            return "Analysis failed"
    
    def find_single_source_opportunities(self):
        """Find potential single-source opportunities using content similarity"""
        console.print("[blue]Finding single-source opportunities...[/blue]")
        
        opportunities = []
        
        # Group articles by category and section
        for category, sections in self.hierarchy.items():
            for section, articles in sections.items():
                if len(articles) < 2:
                    continue
                
                # Compare articles within the same section
                for i, article1 in enumerate(articles):
                    for j, article2 in enumerate(articles[i+1:], i+1):
                        # Calculate content similarity
                        similarity = self.calculate_content_similarity(
                            article1['content'], 
                            article2['content']
                        )
                        
                        if similarity > 0.7:  # 70% similarity threshold
                            # Analyze with Ollama
                            combined_content = f"Article 1: {article1['title']}\n{article1['content'][:1000]}...\n\nArticle 2: {article2['title']}\n{article2['content'][:1000]}..."
                            
                            analysis = self.analyze_with_ollama(
                                "Are these two articles similar enough to be consolidated into a single article? Answer YES or NO and explain why.",
                                combined_content
                            )
                            
                            opportunities.append({
                                'pages': [article1, article2],
                                'similarity': similarity,
                                'analysis': analysis
                            })
        
        return opportunities
    
    def calculate_content_similarity(self, content1, content2):
        """Calculate similarity between two content pieces"""
        # Simple word-based similarity
        words1 = set(re.findall(r'\w+', content1.lower()))
        words2 = set(re.findall(r'\w+', content2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def generate_analysis_report(self):
        """Generate comprehensive analysis report"""
        console.print("[blue]Generating analysis report...[/blue]")
        
        # Find single-source opportunities
        single_source = self.find_single_source_opportunities()
        
        # Generate report
        report_file = self.output_dir / "analysis_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Zendesk Help Center Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Content statistics
            f.write("## Content Statistics\n\n")
            f.write(f"- **Total Articles:** {len(self.all_files)}\n")
            f.write(f"- **Total Categories:** {len(self.hierarchy)}\n")
            
            category_counts = {cat: sum(len(articles) for articles in sections.values()) 
                             for cat, sections in self.hierarchy.items()}
            
            f.write("- **Articles by Category:**\n")
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  - {category}: {count} articles\n")
            f.write("\n")
            
            # Single-source opportunities
            f.write("## Single-Source Opportunities\n\n")
            if single_source:
                f.write(f"Found {len(single_source)} potential single-source opportunities:\n\n")
                for i, candidate in enumerate(single_source, 1):
                    f.write(f"### Opportunity {i}\n\n")
                    f.write("**Pages with similar content:**\n")
                    for page in candidate['pages']:
                        f.write(f"- {page['title']} ({page['category']}/{page['section']})\n")
                    f.write(f"\n**Similarity Score:** {candidate['similarity']:.2%}\n")
                    f.write(f"\n**Analysis:** {candidate['analysis']}\n\n")
            else:
                f.write("No single-source opportunities found.\n\n")
        
        console.print(f"[green]Analysis report saved to {report_file}[/green]")
    
    def process_all(self):
        """Run the complete processing pipeline"""
        console.print("[green]Starting markdown content processing...[/green]")
        
        # Phase 1: Auto-merge chunks if detected
        console.print("[blue]Phase 1: Checking for chunk folders...[/blue]")
        processed_dir = self.auto_merge_chunks(str(self.markdown_dir))
        
        # Update markdown_dir to point to the processed directory
        original_markdown_dir = self.markdown_dir
        self.markdown_dir = Path(processed_dir)
        
        console.print(f"[blue]Processing directory: {self.markdown_dir}[/blue]")
        
        # Step 1: Scan markdown files
        self.scan_markdown_files()
        
        # Step 2: Organize by hierarchy
        self.organize_by_hierarchy()
        
        # Step 3: Generate sitemap
        self.generate_sitemap()
        
        # Step 4: Generate analysis report
        self.generate_analysis_report()
        
        console.print(f"\n[green]Processing complete![/green]")
        console.print(f"Output directory: {self.output_dir}")
        console.print("Files generated:")
        console.print(f"  - {self.output_dir}/sitemap.md")
        console.print(f"  - {self.output_dir}/analysis_report.md")
        
        # If we processed chunks, provide additional info
        if processed_dir != str(original_markdown_dir):
            console.print(f"[blue]Note: Processed chunks from {original_markdown_dir} -> {processed_dir}[/blue]")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        console.print("[red]Usage: python markdown_processor.py <markdown_dir> [output_dir][/red]")
        console.print("Example: python markdown_processor.py '/Users/jlevine/Downloads/zendesk_help_center_2025-07-22 (3)'")
        console.print("Note: If no output_dir specified, analysis will be placed inside the source directory")
        console.print("\n[blue]NEW: Auto-merge functionality for chunked downloads[/blue]")
        console.print("The processor will automatically detect and merge chunk folders before analysis.")
        return
    
    markdown_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(markdown_dir):
        console.print(f"[red]Markdown directory not found: {markdown_dir}[/red]")
        return
    
    console.print(f"[blue]Processing directory: {markdown_dir}[/blue]")
    console.print("[blue]Auto-merge enabled: Will detect and merge chunk folders automatically[/blue]")
    
    processor = MarkdownProcessor(markdown_dir, output_dir)
    processor.process_all()

if __name__ == "__main__":
    main() 