# Documentation Portal Analysis Toolset

A comprehensive suite of tools for analyzing and processing documentation websites, with special support for JavaScript-rendered portals that require authentication. This toolset helps documentation teams identify content duplication, prepare content for RAG systems, and maintain documentation quality.

## Choose Your Tool

### **Documentation Analysis Tool** (doc_analyzer.py)
**Best for:** Finding duplicate content, identifying single-sourcing opportunities
**You need:** Gaming PC with graphics card, 16GB+ RAM
**What it does:**
- Analyzes documentation using AI to find duplicate content
- Identifies single-sourcing opportunities to reduce maintenance
- Finds duplicate images and diagrams
- Discovers hard-coded values that should be variables

### **RAG Content Processor** (rag_processor.py)  
**Best for:** Preparing documentation for chatbots and knowledge bases
**You need:** Any modern computer, 8GB+ RAM
**What it does:**
- Transforms documentation into optimized chunks for RAG systems
- Cleans HTML content while preserving semantic structure
- Creates intelligently-sized chunks with metadata
- Generates markdown files ready for knowledge bases

---

**Pick the tool that matches your goal and computer specs, then follow the guide for that specific tool below.**

## Important Access Requirement

**You must have valid access credentials to your documentation portal.** These tools require authentication to access protected documentation. Without proper credentials (e.g., JWT token), the tools will only be able to scrape publicly accessible pages, which may result in incomplete or minimal analysis.

<details>
<summary><strong>How to Find Your JWT Token</strong> (click to expand if you need help identifying your JWT token)</summary>

Your JWT token is usually found in the URL when you're logged into your documentation portal. Here's how to identify it:

**Example URL after logging in:**
```
https://docs.yourcompany.com/dashboard?jwt=eyJhbGciOiJIUzI1NiIs...SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c&other=params
```

**Your JWT token is this part:**
```
eyJhbGciOiJIUzI1NiIs...SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
                    ↑ JWT token starts here ↑                                    ↑ JWT token ends here ↑
```

**To get your token:**
1. Log into your documentation portal in a web browser
2. Look at the URL in your browser's address bar
3. Find the part that says `jwt=` followed by a long string of characters
4. Copy everything after `jwt=` up to the next `&` (or end of URL if there's no `&`)
5. That's your JWT token - paste it when the tool asks for it

**Common JWT token locations:**
- In the URL: `?jwt=YOUR_TOKEN_HERE`
- In cookies (check browser developer tools → Application → Cookies)
- In local storage (check browser developer tools → Application → Local Storage)

</details>


## Hardware Requirements

<details>
<summary><strong>System Requirements</strong> (click to expand to check if your computer can run these tools)</summary>

### For Documentation Analysis Tool (doc_analyzer.py)
**This tool uses AI and needs more powerful hardware:**

**Your computer needs:**
- **Modern processor** - Intel i5/i7 or AMD Ryzen 5/7 from the last 5 years
- **16GB RAM minimum** (32GB recommended for large documentation sites)
- **Gaming graphics card** with 8GB+ memory (NVIDIA GTX 1070 or newer recommended)
- **20-50GB free disk space** (for the AI model and analysis results)
- **Stable internet connection**

**Not sure about your graphics card?**
- Check Windows Settings → System → Display → Advanced display settings
- Or look up your computer model online to see specs
- **No gaming graphics card?** The tool might run slowly on CPU only, but it will still work

### For RAG Content Processor (rag_processor.py)  
**This tool is much lighter and works on most computers:**

**Your computer needs:**
- **Any modern computer** from the last 5 years
- **8GB RAM minimum** (16GB recommended for large sites)
- **No special graphics card needed**
- **10-20GB free disk space**
- **Stable internet connection**

### What kind of computer do I have?
**Windows:** Settings → System → About  
**Mac:** Apple Menu → About This Mac  
**Don't worry if your specs aren't perfect** - start with smaller documentation sites to test, and consider using only the RAG processor if your computer struggles with the AI analysis tool.

### Software Requirements
- **Python 3.8 or newer** - Download from [python.org](https://python.org)
- **Playwright** - For controlling web browsers automatically
- **BeautifulSoup4** - For reading HTML content
- **Rich** - For pretty console output
- **PyYAML** - For handling configuration files
- **Ollama + Llama 3.2 Vision** - AI model (only needed for doc_analyzer.py)

</details>

## Installation

### Prerequisites
- **Python 3.8 or newer** - Download from [python.org](https://python.org) if not installed
- **Command line/Terminal access** - Use Terminal on Mac/Linux or Command Prompt on Windows

### Step-by-Step Setup

<details>
<summary><strong>What is a Python virtual environment?</strong> (click to expand for explanation)</summary>

A virtual environment is like a separate workspace for this project that keeps its files separate from other Python projects on your computer. Think of it as creating a dedicated folder where all the tools needed for this project will be installed, without affecting anything else on your system.

**Why do we need it?**
- Prevents conflicts between different projects
- Keeps your system clean and organized
- Makes it easy to share the project with others

</details>

1. **Download the project files**:
   ```bash
   git clone <repository-url>
   cd portal_analysis
   ```
   *If you don't have git, you can download the project as a ZIP file and extract it.*

2. **Create a dedicated workspace** (virtual environment):
   ```bash
   python3 -m venv venv
   ```
   *This creates a folder called 'venv' where all project tools will be stored.*

3. **Activate the workspace**:
   ```bash
   # On Mac/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```
   *You'll know it worked when you see (venv) at the start of your command line.*

4. **Install the required tools**:
   ```bash
   pip install -r requirements.txt
   ```
   *This downloads and installs all the tools the project needs.*

5. **Install web browser for automation**:
   ```bash
   playwright install chromium
   ```
   *This installs a special browser that the tools can control automatically.*

6. **Set up AI analysis** (only needed for doc_analyzer.py):
   - Visit [ollama.ai](https://ollama.ai) and follow their installation instructions
   - After installing Ollama, run:
   ```bash
   ollama pull llama3.2-vision:11b
   ```
   *This downloads an AI model for analyzing documentation content.*

## Quick Start

### Before You Begin
1. **Make sure your virtual environment is activated** - you should see `(venv)` at the start of your command line
2. **Have your JWT token ready** - see the expandable section above if you need help finding it
3. **Be logged into your documentation portal** in a web browser

### For Documentation Analysis:
```bash
python doc_analyzer.py
```

**What happens next:**
1. The tool will ask for your JWT token - paste it and press Enter
2. It will ask if you want debug mode - type `n` and press Enter (unless you're troubleshooting)
3. Enter the URLs you want to analyze, one per line
4. Press Enter on an empty line when you're done adding URLs
5. The tool will start crawling and analyzing your documentation
6. Results will be saved as `doc_analysis.json` and `doc_summary.md`

### For RAG Processing:
```bash
python rag_processor.py
```

**What happens next:**
1. The tool will ask for your JWT token - paste it and press Enter
2. It will ask if you want debug mode - type `n` and press Enter (unless you're troubleshooting)
3. It will ask for an output directory - press Enter to use the default (`rag_output`)
4. Enter the URLs you want to process, one per line
5. Press Enter on an empty line when you're done adding URLs
6. The tool will create markdown files in the output directory, ready for your knowledge base

<details>
<summary><h2>Documentation Analyzer (doc_analyzer.py)</h2></summary>

### Overview
The Documentation Analyzer uses AI to comprehensively analyze your documentation portal, identifying opportunities for content consolidation and improvement.

### Key Features
- **JavaScript Support**: Uses Playwright to handle modern SPAs and dynamic content
- **Smart Crawling**: BFS algorithm with intelligent URL normalization
- **AI Analysis**: Leverages Llama 3.2 Vision for content and image analysis
- **Sliding Window Analysis**: Efficiently compares content across pages
- **Rich Reporting**: Generates both JSON data and markdown summaries

### How It Works

1. **Crawling Phase**
   ```
   Starting BFS crawl from 2 seed URLs
   Crawling... Queue: 45 | Visited: 123
   Progress: 280 pages crawled, 58 in queue
   ```

2. **Analysis Phase**
   - **Content Hashing**: Creates sliding window hashes for deep comparison
   - **AI Evaluation**: Uses Ollama to analyze similar content pairs
   - **Image Analysis**: Perceptual hashing + vision AI for images
   - **Diagram Extraction**: Identifies and compares Mermaid diagrams

3. **Output Generation**
   - `doc_analysis.json`: Complete analysis data
   - `doc_summary.md`: Human-readable findings

### Usage Example
```bash
./doc_analyzer.py

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
<summary><h2>RAG Processor (rag_processor.py)</h2></summary>

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

## Common Configuration

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

## Troubleshooting Common Issues

<details>
<summary><strong>Common Problems and Solutions</strong> (click to expand)</summary>

### "Command not found" or "python is not recognized"
**Problem:** Your system can't find Python
**Solutions:**
- Make sure Python is installed from [python.org](https://python.org)
- Try `python3` instead of `python`
- On Windows, try `py` instead of `python`
- Restart your command line/terminal after installing Python

### "Permission denied" errors
**Problem:** Your user account doesn't have permission to install things
**Solutions:**
- On Mac/Linux: Try adding `sudo` before the command (e.g., `sudo pip install...`)
- On Windows: Run Command Prompt as Administrator
- Use `pip install --user` instead of just `pip install`

### "(venv) doesn't appear in my command line"
**Problem:** Virtual environment isn't activated
**Solutions:**
- Make sure you ran the activation command for your operating system
- Try running the activation command again
- Navigate to the project folder first, then activate


### Tool runs but finds no pages
**Problem:** Authentication isn't working or URLs are incorrect
**Solutions:**
- Verify you can access the URLs in your browser while logged in
- Try visiting the URLs with `?jwt=YOUR_TOKEN` manually in your browser
- Check that the URLs don't require additional authentication steps
- Make sure the URLs contain actual documentation content

### "ModuleNotFoundError" or import errors
**Problem:** Required packages aren't installed
**Solutions:**
- Make sure your virtual environment is activated (you should see `(venv)`)
- Run `pip install -r requirements.txt` again
- Try `pip install --upgrade pip` first, then retry the installation

### Tool is very slow or uses too much memory
**Problem:** Large documentation site or insufficient resources
**Solutions:**
- Start with a smaller set of URLs to test
- Close other applications to free up memory
- Consider using the RAG processor first (it's less resource-intensive)
- For doc_analyzer: ensure you have enough GPU memory for the AI model

### Can't install Ollama or AI model download fails
**Problem:** Network issues or system compatibility
**Solutions:**
- Check your internet connection
- Try downloading during off-peak hours
- Ensure you have enough disk space (20GB+ recommended)
- Check Ollama's system requirements on their website

</details>


## Extending the Tools

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

## Contributing

Feel free to extend these tools for your specific needs:
- Add new authentication methods
- Customize content cleaning rules
- Implement additional output formats
- Create specialized analyzers

## License

This project is provided as-is for documentation analysis and processing purposes.