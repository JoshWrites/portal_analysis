# Documentation Portal Analysis Toolset

A comprehensive suite of tools for analyzing and processing documentation websites, with special support for JavaScript-rendered portals that require authentication. This toolset helps documentation teams identify content duplication, prepare content for RAG systems, and maintain documentation quality.

## 🎯 Purpose Overview

### **gk8_doc_analyzer.py** - Documentation Analysis Tool
Crawls and analyzes documentation to identify:
- Duplicate content across different documentation spaces
- Single-sourcing opportunities to reduce maintenance
- Image and diagram duplication
- Hard-coded values that should be variables

### **gk8_rag_processor.py** - RAG Content Processor
Transforms documentation into optimized chunks for RAG systems:
- Cleans HTML content while preserving semantic structure
- Creates intelligently-sized chunks with metadata
- Generates markdown files ready for knowledge bases
- Maintains context and relationships between chunks

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd portal_analysis
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

5. **Set up Ollama** (only for doc_analyzer):
   ```bash
   # Install Ollama following instructions at https://ollama.ai
   ollama pull llama3.2-vision:11b
   ```

## 🚀 Quick Start

### For Documentation Analysis:
```bash
./gk8_doc_analyzer.py
# Enter JWT token when prompted
# Provide URLs or use defaults
```

### For RAG Processing:
```bash
./gk8_rag_processor.py
# Enter JWT token when prompted
# Specify output directory (default: rag_output)
# Provide URLs or use defaults
```

<details>
<summary><h2>📊 Documentation Analyzer (gk8_doc_analyzer.py)</h2></summary>

### Overview
The Documentation Analyzer uses AI to comprehensively analyze your documentation portal, identifying opportunities for content consolidation and improvement.

### Key Features
- **JavaScript Support**: Uses Playwright to handle modern SPAs and dynamic content
- **Smart Crawling**: BFS algorithm with intelligent URL normalization
- **AI Analysis**: Leverages Llama 3.2 Vision for content and image analysis
- **Sliding Window Analysis**: Efficiently compares content across pages
- **Rich Reporting**: Generates both JSON data and markdown summaries

### How It Works

1. **Authentication & Setup**
   - Uses JWT token to authenticate with the portal
   - Establishes browser session with Playwright
   - Maintains cookies for subsequent requests

2. **Crawling Phase**
   ```
   Starting BFS crawl from 2 seed URLs
   Crawling... Queue: 45 | Visited: 123
   Progress: 280 pages crawled, 58 in queue
   ```

3. **Analysis Phase**
   - **Content Hashing**: Creates sliding window hashes for deep comparison
   - **AI Evaluation**: Uses Ollama to analyze similar content pairs
   - **Image Analysis**: Perceptual hashing + vision AI for images
   - **Diagram Extraction**: Identifies and compares Mermaid diagrams

4. **Output Generation**
   - `gk8_doc_analysis.json`: Complete analysis data
   - `gk8_doc_summary.md`: Human-readable findings

### Usage Example
```bash
./gk8_doc_analyzer.py

Enter your JWT token: eyJhbGciOiJIUzI1NiIs...
Enable debug mode? (y/n): n
Enter URLs to crawl (one per line, empty line to finish):
> https://docs.example.com
> https://docs.example.com/api-v15
> 

Starting GK8 documentation analysis...
Step 1: Crawling pages...
Pages crawled: 338
Step 2: Analyzing content with Vision AI...
Found 47 single-sourcing opportunities
Analysis complete!
```

### Next Steps with Output

1. **Review the Summary** (`gk8_doc_summary.md`):
   - Prioritize high-similarity content pairs
   - Identify quick wins for consolidation
   - Plan content refactoring

2. **Deep Dive with JSON** (`gk8_doc_analysis.json`):
   ```python
   import json
   with open('gk8_doc_analysis.json') as f:
       data = json.load(f)
   
   # Find pages with most duplication
   for candidate in data['single_source_candidates']:
       if candidate['similarity_score'] > 80:
           print(f"High similarity: {candidate['page1']} <-> {candidate['page2']}")
   ```

3. **Image Consolidation**:
   - Replace duplicate images with single source
   - Update image references across documentation
   - Consider creating a shared assets library

4. **Variable Extraction**:
   - Create configuration files for version numbers
   - Implement variable substitution in build process
   - Update hard-coded values identified in report
</details>

<details>
<summary><h2>🤖 RAG Processor (gk8_rag_processor.py)</h2></summary>

### Overview
The RAG Processor transforms your documentation into optimized chunks for use with Retrieval-Augmented Generation systems like Msty's Knowledge Stack.

### Key Features
- **Smart Chunking**: Respects semantic boundaries and section headers
- **Context Preservation**: Maintains relationships between chunks
- **Rich Metadata**: Includes breadcrumbs, content type, and related links
- **Clean Output**: Removes navigation while preserving content structure
- **YAML Frontmatter**: Machine-readable metadata for each chunk

### How It Works

1. **Content Crawling**
   - Same robust crawling as the analyzer
   - Stores raw HTML for processing
   - Maintains URL relationships

2. **Processing Pipeline**
   ```
   For each page:
   ├── Clean HTML (remove nav, ads, etc.)
   ├── Extract metadata (breadcrumbs, links)
   ├── Identify sections (headers, content blocks)
   ├── Create chunks (300-1500 tokens each)
   └── Save as markdown with frontmatter
   ```

3. **Chunk Generation**
   - **Size Targets**: 300-1500 tokens per chunk
   - **Overlap**: 100 tokens between chunks for context
   - **Boundaries**: Respects headers and code blocks
   - **Metadata**: Full context for each chunk

4. **Output Structure**
   ```
   rag_output/
   ├── api-v15/
   │   ├── authentication-overview-01.md
   │   ├── authentication-overview-02.md
   │   └── jwt-configuration-01.md
   ├── guides/
   │   ├── getting-started-01.md
   │   └── advanced-usage-01.md
   └── index.md
   ```

### Usage Example
```bash
./gk8_rag_processor.py

Enter your JWT token: eyJhbGciOiJIUzI1NiIs...
Enable debug mode? (y/n): n
Output directory (default: rag_output): my_docs
Enter URLs to crawl (one per line, empty line to finish):
> 

Starting GK8 RAG document processing...
Step 1: Crawling pages...
Pages crawled: 156
Step 2: Processing content into RAG chunks...
Processed 523 chunks from 156 pages
Step 3: Generating index...
Processing complete!
```

### Chunk Format Example
```yaml
---
title: "Authentication Overview"
page_url: "https://docs.example.com/api-v15/auth"
space: "api-v15"
breadcrumb: "API v15 > Authentication > Overview"
content_type: "api"
chunk_index: 1
total_chunks: 3
token_count: 842
related_links:
  - "https://docs.example.com/api-v15/auth/jwt"
  - "https://docs.example.com/api-v15/auth/oauth"
---

# Authentication Overview

The API uses JWT tokens for authentication. All requests must include a valid token in the Authorization header...
```

### Next Steps with Output

1. **Import to Msty Knowledge Stack**:
   - Open Msty and create a new Knowledge Stack
   - Import the markdown files from `rag_output/`
   - Configure chunking settings if needed
   - Test retrieval with sample queries

2. **Custom Processing**:
   ```python
   import os
   import yaml
   
   # Read all chunks and analyze
   for root, dirs, files in os.walk('rag_output'):
       for file in files:
           if file.endswith('.md'):
               with open(os.path.join(root, file)) as f:
                   # Parse frontmatter
                   content = f.read()
                   frontmatter, text = content.split('---\n', 2)[1:]
                   metadata = yaml.safe_load(frontmatter)
                   
                   # Process based on content type
                   if metadata['content_type'] == 'api':
                       # Special handling for API docs
                       pass
   ```

3. **Quality Assurance**:
   - Review the index.md for completeness
   - Check chunk sizes are appropriate
   - Verify metadata accuracy
   - Test retrieval performance

4. **Integration Options**:
   - **LangChain**: Load markdown files as documents
   - **LlamaIndex**: Import with metadata intact
   - **Custom RAG**: Use chunks with your embedding model
   - **Vector Databases**: Index with metadata filters
</details>

## 🛠️ Common Configuration

### Authentication Setup
Both tools support various authentication methods:
- **JWT URL Parameters**: `?jwt=token&reload`
- **Bearer Token Headers**: Automatic injection
- **Session Cookies**: Maintained across requests

### URL Filtering
Customize which pages to crawl by modifying:
```python
# In either tool
def should_crawl_url(self, url):
    # Add your custom logic
    if "/internal/" in url:
        return False
    return True
```

### Space Detection
Define how to categorize your documentation:
```python
def determine_space(self, url):
    if "/api/" in url:
        return "api-docs"
    elif "/tutorials/" in url:
        return "tutorials"
    return "general"
```

## 📝 Requirements

- **Python 3.8+**
- **Playwright** for JavaScript rendering
- **BeautifulSoup4** for HTML parsing
- **Rich** for console output
- **PyYAML** for metadata handling
- **Ollama + Llama 3.2 Vision** (analyzer only)

## 🤝 Contributing

Feel free to extend these tools for your specific needs:
- Add new authentication methods
- Customize content cleaning rules
- Implement additional output formats
- Create specialized analyzers

## 📄 License

This project is provided as-is for documentation analysis and processing purposes.