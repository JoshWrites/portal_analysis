# Documentation Portal Analysis Toolset

A comprehensive suite of tools for analyzing and processing documentation websites, with special support for JavaScript-rendered portals that require authentication. This toolset helps documentation teams identify content duplication, prepare content for RAG systems, and maintain documentation quality.

## 🎯 Purpose Overview

### **doc_analyzer.py** - Documentation Analysis Tool
Crawls and analyzes documentation to identify:
- Duplicate content across different documentation spaces
- Single-sourcing opportunities to reduce maintenance
- Image and diagram duplication
- Hard-coded values that should be variables

### **rag_processor.py** - RAG Content Processor
Transforms documentation into optimized chunks for RAG systems:
- Cleans HTML content while preserving semantic structure
- Creates intelligently-sized chunks with metadata
- Generates markdown files ready for knowledge bases
- Maintains context and relationships between chunks

## ⚠️ Important Access Requirement

**You must have valid access credentials to your documentation portal.** These tools require authentication to access protected documentation. Without proper credentials (e.g., JWT token), the tools will only be able to scrape publicly accessible pages, which may result in incomplete or minimal analysis.

## 🌐 Portal Compatibility

These tools are designed for documentation portals with the following characteristics:

### **Ideal For:**
- **JavaScript-rendered documentation sites** (React, Vue, Angular-based)
- **Static site generators** with authentication (Docusaurus, GitBook, MkDocs)
- **Enterprise documentation portals** with JWT/session-based security
- **API documentation platforms** (Swagger UI, Redoc, custom solutions)
- **Knowledge bases** with structured content and navigation

### **Key Requirements:**
- **JWT token authentication** (passed via URL parameters or headers)
- **HTML-based content** (not PDF-only or binary formats)
- **Consistent URL structure** for content categorization
- **Server-side or client-side rendering** (both supported via Playwright)

### **Authentication Support:**
The tools currently support JWT authentication where tokens are passed as URL parameters (e.g., `?jwt=token`). The authentication flow:
1. Initial request with JWT token establishes session
2. Browser cookies maintain authentication state
3. Subsequent requests use session cookies

### **Not Suitable For:**
- Sites requiring CAPTCHA or 2FA interaction
- Documentation behind complex SSO flows (without JWT)
- Binary-only documentation (PDFs without HTML)
- Rate-limited APIs without HTML documentation

## 💻 Hardware Requirements

### doc_analyzer.py - Documentation Analysis Tool

#### Minimum Requirements:
- **CPU**: 4 cores (for Ollama LLM inference)
- **RAM**: 16GB (8GB for Ollama model + system overhead)
- **GPU**: Discrete GPU with 8GB VRAM
  - NVIDIA: GTX 1070 or newer
  - AMD: RX 6600 or newer (requires ROCm installation)
- **Storage**: 20GB free (for Ollama model storage)
- **Network**: Stable broadband connection

#### Recommended Requirements:
- **CPU**: 8+ cores (faster LLM inference)
- **RAM**: 32GB (smooth operation with large documentation)
- **GPU**: Discrete GPU with 12GB+ VRAM
  - NVIDIA: RTX 3060 12GB, RTX 4060 Ti 16GB, or better
  - AMD: RX 6700 XT, RX 7600 XT or better (requires ROCm installation)
- **Storage**: 50GB+ free (model + analysis outputs)
- **Network**: High-speed connection (faster crawling)

### rag_processor.py - RAG Content Processor

#### Minimum Requirements:
- **CPU**: 2 cores
- **RAM**: 8GB
- **GPU**: None required (CPU-only tool)
- **Storage**: 10GB free
- **Network**: Stable broadband connection

#### Recommended Requirements:
- **CPU**: 4+ cores (faster processing)
- **RAM**: 16GB (handle larger documentation sets)
- **GPU**: Not needed
- **Storage**: 20GB+ free (for output chunks)
- **Network**: High-speed connection

### GPU Notes:
- **NVIDIA GPUs**: Work out-of-the-box with Ollama after CUDA drivers installation
- **AMD GPUs**: Require ROCm installation for Ollama GPU acceleration
- **Intel Arc GPUs**: Currently not supported by Ollama
- The doc_analyzer tool benefits significantly from GPU acceleration for the Vision LLM model

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
./doc_analyzer.py
# Enter JWT token when prompted
# Provide URLs to analyze
```

### For RAG Processing:
```bash
./rag_processor.py
# Enter JWT token when prompted
# Specify output directory (default: rag_output)
# Provide URLs to process
```

<details>
<summary><h2>📊 Documentation Analyzer (doc_analyzer.py)</h2></summary>

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
   - `doc_analysis.json`: Complete analysis data
   - `doc_summary.md`: Human-readable findings

### Usage Example
```bash
./doc_analyzer.py

Enter your JWT token: eyJhbGciOiJIUzI1NiIs...
Enable debug mode? (y/n): n
Enter URLs to crawl (one per line, empty line to finish):
> https://docs.yourcompany.com
> https://docs.yourcompany.com/api/v2
> 

Starting documentation analysis...
Step 1: Crawling pages...
Pages crawled: 338
Step 2: Analyzing content with Vision AI...
Found 47 single-sourcing opportunities
Analysis complete!
```

### Next Steps with Output

1. **Review the Summary** (`doc_summary.md`):
   - Prioritize high-similarity content pairs
   - Identify quick wins for consolidation
   - Plan content refactoring

2. **Deep Dive with JSON** (`doc_analysis.json`):
   ```python
   import json
   with open('doc_analysis.json') as f:
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
<summary><h2>🤖 RAG Processor (rag_processor.py)</h2></summary>

### Overview
The RAG Processor transforms your documentation into optimized chunks for use with Retrieval-Augmented Generation systems like Msty's Knowledge Stack or custom RAG implementations.

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
   ├── api-v2/
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
./rag_processor.py

Enter your JWT token: eyJhbGciOiJIUzI1NiIs...
Enable debug mode? (y/n): n
Output directory (default: rag_output): my_docs
Enter URLs to crawl (one per line, empty line to finish):
> https://docs.yourcompany.com
> 

Starting RAG document processing...
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
page_url: "https://docs.yourcompany.com/api/auth"
space: "api"
breadcrumb: "API Documentation > Authentication > Overview"
content_type: "api"
chunk_index: 1
total_chunks: 3
token_count: 842
related_links:
  - "https://docs.yourcompany.com/api/auth/jwt"
  - "https://docs.yourcompany.com/api/auth/oauth"
---

# Authentication Overview

The API uses JWT tokens for authentication. All requests must include a valid token in the Authorization header...
```

### Next Steps with Output

1. **Import to Knowledge Systems**:
   - **Msty**: Import markdown files into Knowledge Stack
   - **LangChain**: Load as documents with metadata
   - **LlamaIndex**: Use as knowledge base
   - **Custom RAG**: Process with your embedding pipeline

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
   - **Vector Databases**: Index with metadata filters
   - **Search Systems**: Use metadata for faceted search
   - **ChatBots**: Provide contextual documentation answers
   - **Support Systems**: Enhanced ticket resolution
</details>

## 🛠️ Common Configuration

### Authentication Setup
Both tools support JWT authentication where tokens are passed as URL parameters:
```python
# Current implementation
auth_url = f"{base_url}?jwt={jwt_token}&reload"
```

To adapt for other authentication methods, modify the `_authenticate()` method in either tool.

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

## 🔧 Extending the Tools

### Adding Authentication Methods
To support OAuth, SAML, or other authentication:
1. Modify `_authenticate()` method
2. Update session/cookie handling
3. Adjust the initial authentication URL pattern

### Custom Content Processing
To handle specific documentation formats:
1. Update `clean_content()` for your HTML structure
2. Modify `extract_sections()` for custom layouts
3. Adjust chunking logic in `create_chunks()`

### Output Format Customization
To generate different output formats:
1. Modify `save_chunk()` for new file formats
2. Update metadata structure in `extract_metadata()`
3. Adjust the index generation logic

## 🤝 Contributing

Feel free to extend these tools for your specific needs:
- Add new authentication methods
- Customize content cleaning rules
- Implement additional output formats
- Create specialized analyzers

## 📄 License

This project is provided as-is for documentation analysis and processing purposes.

# Portal Analysis Tools

This repository contains tools for analyzing and processing documentation portals, with support for OIDC authentication (Azure AD/Entra ID) for Zendesk Help Center.

## Features

### Document Analyzer (`doc_analyzer.py`)
- **OIDC Authentication**: Supports Azure AD/Entra ID authentication for Zendesk Help Center
- **Interactive Browser Authentication**: Opens browser window for user to complete OIDC login flow
- **Content Analysis**: Analyzes documentation content using Llava AI vision model
- **Image Analysis**: Processes and analyzes images in documentation
- **Mermaid Diagram Detection**: Identifies and analyzes Mermaid diagrams
- **Duplicate Detection**: Finds duplicate content and similar diagrams
- **Comprehensive Reporting**: Generates detailed analysis reports
- **Sitemap Generation**: Creates documentation sitemap with article titles and last updated dates

### RAG Processor (`rag_processor.py`)
- **OIDC Authentication**: Same authentication support as document analyzer
- **Content Chunking**: Splits documentation into RAG-ready chunks
- **Markdown Output**: Generates clean markdown files for knowledge bases
- **Metadata Preservation**: Maintains links, structure, and metadata
- **Index Generation**: Creates comprehensive index of all processed content

## Authentication Support

### OIDC Authentication (Azure AD/Entra ID)
The tools now support OIDC authentication for Zendesk Help Center:

1. **Interactive Login**: Browser window opens for user to complete Azure AD login
2. **Session Management**: Maintains authenticated session for crawling
3. **Automatic Detection**: Detects login requirements and guides user through process
4. **Session Persistence**: Uses session cookies for subsequent requests

### How It Works
1. Script launches browser in non-headless mode
2. Navigates to Zendesk Help Center URL
3. Detects login buttons/links automatically
4. Opens OIDC authentication flow
5. Waits for user to complete Azure AD login
6. Verifies authentication success
7. Maintains session for content crawling

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Document Analyzer

```bash
python doc_analyzer.py
```

The script will:
1. Prompt for your Zendesk Help Center URL
2. Open browser for OIDC authentication
3. Allow you to specify URLs to analyze (or use the main help center)
4. Crawl and analyze content with Llava AI vision model
5. Generate analysis reports and documentation sitemap

### RAG Processor

```bash
python rag_processor.py
```

The script will:
1. Prompt for your Zendesk Help Center URL
2. Open browser for OIDC authentication
3. Allow you to specify URLs to process (or use the main help center)
4. Crawl content and split into RAG-ready chunks
5. Generate markdown files and index

## Configuration

### Zendesk Help Center URL
Provide your Zendesk Help Center URL in the format:
```
https://yourcompany.zendesk.com/hc
```

### Authentication Flow
1. Enter your Zendesk Help Center URL when prompted
2. Browser window will open automatically
3. Complete the Azure AD/Entra ID login process
4. Script will detect successful authentication
5. Content crawling will begin automatically

## Output Files

### Document Analyzer Output
- `doc_analysis.json`: Detailed analysis data
- `doc_summary.md`: Human-readable analysis report
- `sitemap.md`: Documentation sitemap with article titles and last updated dates

### RAG Processor Output
- `rag_output/`: Directory containing processed chunks
- `rag_output/index.md`: Index of all processed content
- Individual markdown files for each content chunk

## Requirements

- Python 3.8+
- Playwright (for browser automation)
- Ollama (for AI analysis)
- Rich (for console output)
- BeautifulSoup (for HTML parsing)
- PIL (for image processing)

## Troubleshooting

### Authentication Issues
- Ensure your Zendesk Help Center is configured with Azure AD/Entra ID
- Check that you have proper access to the help center
- Verify the URL format is correct
- Complete the full OIDC flow in the browser window

### Browser Issues
- Script requires browser automation (Playwright)
- Browser window must remain open during authentication
- Ensure no popup blockers are active

### Content Access
- Verify you have access to the content you're trying to analyze
- Check that the URLs are accessible from your authenticated session
- Some content may require additional permissions

## Migration from JWT Authentication

The tools have been updated from JWT-based authentication to OIDC authentication:

### Changes Made
- Removed JWT token parameter
- Added Zendesk URL parameter
- Implemented interactive browser authentication
- Updated authentication flow for OIDC
- Enhanced session management

### Benefits
- Better security with Azure AD integration
- No need to manage JWT tokens
- Standard enterprise authentication flow
- Improved session persistence

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your Zendesk Help Center
5. Submit a pull request

## License

This project is licensed under the MIT License.