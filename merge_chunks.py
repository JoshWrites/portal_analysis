#!/usr/bin/env python3
"""
Zendesk Chunk Merger

This script merges downloaded chunk files from the Zendesk crawler into a single
organized folder structure. It looks for chunk files with the same run ID and
combines them into a unified output.

Usage:
    python merge_chunks.py [run_id] [output_dir]
    
Examples:
    python merge_chunks.py 2025-01-23_14-30-45 merged_output
    python merge_chunks.py 2025-01-23_14-30-45  # Uses default output dir
"""

import os
import sys
import zipfile
import glob
import shutil
import json
from pathlib import Path
from collections import defaultdict
import argparse

def find_chunk_files(run_id=None):
    """Find all chunk files, optionally filtered by run ID."""
    if run_id:
        # Look for new directory structure first
        pattern = f"zendesk_chunks/{run_id}/chunk_*.zip"
        alt_pattern = f"zendesk_chunk_{run_id}_*.zip"  # Legacy pattern
    else:
        # Look for any chunk files
        pattern = "zendesk_chunks/*/chunk_*.zip"
        alt_pattern = "zendesk_chunk_*.zip"  # Legacy pattern
    
    # Look in Downloads folder and current directory
    search_paths = [
        os.path.expanduser("~/Downloads"),
        os.getcwd()
    ]
    
    chunk_files = []
    for search_path in search_paths:
        if os.path.exists(search_path):
            # Try primary pattern first
            files = glob.glob(os.path.join(search_path, pattern))
            if not files and 'alt_pattern' in locals():
                # Try alternative pattern
                files = glob.glob(os.path.join(search_path, alt_pattern))
            chunk_files.extend(files)
    
    return sorted(chunk_files)

def extract_chunk_info(zip_path):
    """Extract information from a chunk file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Read README to get chunk info
            if 'README.md' in zip_file.namelist():
                readme_content = zip_file.read('README.md').decode('utf-8')
                return {
                    'path': zip_path,
                    'readme': readme_content,
                    'files': zip_file.namelist()
                }
    except Exception as e:
        print(f"Error reading {zip_path}: {e}")
        return None

def extract_session_info(chunk_files):
    """Extract session information from chunk files."""
    for chunk_file in chunk_files:
        try:
            with zipfile.ZipFile(chunk_file, 'r') as zip_file:
                if 'session_info.json' in zip_file.namelist():
                    session_data = zip_file.read('session_info.json').decode('utf-8')
                    return json.loads(session_data)
        except Exception as e:
            print(f"Error reading session info from {chunk_file}: {e}")
    return None

def merge_chunks(chunk_files, output_dir):
    """Merge all chunk files into a single organized structure."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Track all files to avoid duplicates
    all_files = set()
    file_counts = defaultdict(int)
    
    print(f"Merging {len(chunk_files)} chunk files into {output_dir}")
    
    for chunk_file in chunk_files:
        print(f"Processing: {os.path.basename(chunk_file)}")
        
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
            print(f"Error processing {chunk_file}: {e}")
    
    # Create merged README
    create_merged_readme(chunk_files, output_dir, file_counts)
    
    print(f"\nMerge complete!")
    print(f"Total unique files: {len(all_files)}")
    print(f"Total chunk files processed: {len(chunk_files)}")
    
    # Report duplicates
    duplicates = {f: c for f, c in file_counts.items() if c > 1}
    if duplicates:
        print(f"Duplicate files found: {len(duplicates)}")
        for file_path, count in duplicates.items():
            print(f"  {file_path}: {count} copies")

def create_merged_readme(chunk_files, output_dir, file_counts):
    """Create a comprehensive README for the merged output."""
    
    # Extract session info from chunks
    session_info = extract_session_info(chunk_files)
    
    readme_content = f"""# Zendesk Help Center - Merged Output

## Summary
- **Total Chunk Files:** {len(chunk_files)}
- **Total Unique Articles:** {len(file_counts)}
- **Generated:** {Path().cwd()}
- **Output Directory:** {output_dir}
"""
    
    if session_info:
        readme_content += f"""
## Session Information
- **Run ID:** {session_info.get('runId', 'Unknown')}
- **Base URL:** {session_info.get('baseUrl', 'Unknown')}
- **Total Chunks:** {session_info.get('totalChunks', len(chunk_files))}
- **Crawl Started:** {session_info.get('timestamp', 'Unknown')}
"""
    
    readme_content += f"""
## Chunk Files Processed
"""
    
    for chunk_file in chunk_files:
        chunk_info = extract_chunk_info(chunk_file)
        if chunk_info:
            readme_content += f"- {os.path.basename(chunk_file)}\n"
            # Extract run ID and chunk number from filename
            filename = os.path.basename(chunk_file)
            if '_' in filename:
                parts = filename.replace('.zip', '').split('_')
                if len(parts) >= 4:
                    run_id = f"{parts[2]}_{parts[3]}"
                    chunk_num = parts[4]
                    readme_content += f"  - Run ID: {run_id}\n"
                    readme_content += f"  - Chunk: {chunk_num}\n"
    
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
    
    print(f"Created merged README: {readme_path}")

def main():
    parser = argparse.ArgumentParser(description='Merge Zendesk crawler chunk files')
    parser.add_argument('run_id', nargs='?', help='Run ID to filter chunks (e.g., 2025-01-23_14-30-45)')
    parser.add_argument('output_dir', nargs='?', default='merged_zendesk_output', 
                       help='Output directory for merged files')
    
    args = parser.parse_args()
    
    # Find chunk files
    chunk_files = find_chunk_files(args.run_id)
    
    if not chunk_files:
        print("No chunk files found!")
        if args.run_id:
            print(f"Looking for files matching: zendesk_chunk_{args.run_id}_*.zip")
        else:
            print("Looking for files matching: zendesk_chunk_*.zip")
        print("\nSearch paths:")
        print("- ~/Downloads")
        print("- Current directory")
        return 1
    
    print(f"Found {len(chunk_files)} chunk files:")
    for chunk_file in chunk_files:
        print(f"  {os.path.basename(chunk_file)}")
    
    # Merge chunks
    merge_chunks(chunk_files, args.output_dir)
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 