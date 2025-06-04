# Documentation Portal Analyzer

A comprehensive tool for analyzing documentation websites, with special support for JavaScript-rendered portals that require authentication. Uses AI-powered analysis to identify content duplication, suggest single-sourcing opportunities, and analyze documentation structure.

## Features

### 🔍 **Comprehensive Crawling**
- **JavaScript Support**: Uses Playwright to crawl modern, JavaScript-rendered documentation sites
- **Session-Based Authentication**: Handles JWT tokens and maintains browser sessions
- **Intelligent Link Discovery**: Breadth-first search with duplicate detection
- **Multi-Space Support**: Analyzes different documentation sections (APIs, guides, references)

### 🤖 **AI-Powered Analysis**
- **Content Similarity Detection**: Uses Ollama/Llama 3.2 Vision to find duplicate content across spaces
- **Single-Sourcing Recommendations**: Identifies content that should be consolidated
- **Variable Detection**: Finds hardcoded values that should be variables (versions, URLs, etc.)
- **Image Analysis**: Detects duplicate images and analyzes visual content

### 📊 **Progress Tracking & Reporting**
- **Real-time Progress**: Live progress bars with time estimates
- **Detailed Statistics**: Crawl coverage, timing, and space breakdown
- **Comprehensive Reports**: JSON data export and markdown summaries
- **Visual Feedback**: Rich console output with color coding

### 🖼️ **Media Analysis**
- **Image Duplicate Detection**: Perceptual hashing to find similar images
- **Vision AI Analysis**: Describes image content and reusability
- **Mermaid Diagram Extraction**: Identifies and categorizes diagrams
- **SVG Handling**: Proper handling of vector graphics

## Prerequisites

- **Python 3.8+**
- **Ollama** with Llama 3.2 Vision model installed
- **Documentation portal access** (JWT tokens, credentials, etc.)

## Installation

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

5. **Set up Ollama** (if not already installed):
   ```bash
   # Install Ollama following instructions at https://ollama.ai
   ollama pull llama3.2-vision:11b
   ```

## Usage

### Basic Analysis

1. **Run the analyzer**:
   ```bash
   ./doc_analyzer.py
   ```

2. **Provide authentication**:
   - Enter your JWT token when prompted
   - Choose 'n' for debug mode (use only for troubleshooting)

3. **Specify URLs to crawl**:
   - Enter documentation URLs one per line
   - Press Enter on empty line to start with defaults
   - The tool will discover and crawl linked pages automatically

### Authentication Methods

The tool supports various authentication patterns:

- **JWT URL Parameters**: `https://docs.example.com?jwt=token&reload`
- **Bearer Token Headers**: Automatic header injection
- **Session Cookies**: Maintains authentication state across requests

### Example Output

```
Crawl complete!
Completed at: 23:00:07 (Duration: 0:19:52)
Statistics:
  • Pages crawled: 338
  • Total links found: 426
  • Duplicate links skipped: 91
  • Unique pages by space:
    - api-v15: 243 pages
    - guides-v15: 59 pages
    - reference: 31 pages
    - general: 5 pages

Step 2: Analyzing content with Vision AI...
Finding single-source candidates... 1250/57003 (2%)
Processing images ████████████████ 45/338 13% 0:02:30 < 0:16:45
```

The tool provides comprehensive progress tracking throughout all phases, including real-time status updates, completion percentages, and time estimates.

## Configuration

### Custom URL Patterns
Modify the `should_crawl_url()` and `determine_space()` methods to customize:
- Which URLs to include/exclude
- How to categorize different documentation sections
- Authentication requirements

### Ollama Configuration
The analyzer uses these default settings:
- **Model**: `llama3.2-vision:11b`
- **Context Size**: 8192 tokens
- **Vision Analysis**: Limited to first 20 images for performance

## Output Files

The analyzer generates several output files:

- **`doc_analysis.json`**: Raw analysis data in JSON format
- **`doc_summary.md`**: Human-readable markdown report
- **Console Output**: Real-time progress and statistics

## Common Use Cases

### 1. **Documentation Audit**
- Identify duplicate content across different sections
- Find outdated or inconsistent information
- Analyze content distribution and coverage

### 2. **Content Consolidation**
- Discover single-sourcing opportunities
- Identify shared components and examples
- Reduce maintenance overhead

### 3. **Portal Migration**
- Inventory existing content before migration
- Understand site structure and dependencies
- Plan content reorganization

### 4. **Quality Assurance**
- Find broken internal links
- Identify missing images or media
- Validate content completeness

## Troubleshooting

### Common Issues

**Browser/Authentication Issues**:
- Ensure JWT token is valid and not expired
- Check that Playwright can access the documentation portal
- Verify network connectivity and firewall settings

**Ollama Connection Issues**:
- Confirm Ollama is running: `ollama list`
- Check model availability: `ollama pull llama3.2-vision:11b`
- Verify sufficient VRAM for vision model

**Performance Issues**:
- Large sites may take significant time to crawl
- Consider limiting scope with URL filters
- Monitor system resources during analysis

### Debug Mode

Debug mode is available for troubleshooting crawling issues:
```bash
# When prompted, enter 'y' for debug mode (only when needed)
Enable debug mode? (y/n): y
```

Debug mode provides additional details:
- Detailed crawling progress and link discovery
- Authentication status and session validation
- Content size warnings and error details
- Verbose logging for all operations

**Note**: Debug mode generates significant console output and should only be used when diagnosing issues.

## Contributing

This tool is designed to be extensible for different documentation platforms:

1. **Add new authentication methods** in `_authenticate()`
2. **Customize URL patterns** in `should_crawl_url()`
3. **Extend space detection** in `determine_space()`
4. **Add new analysis types** following existing patterns

## Dependencies

- **playwright**: JavaScript-rendered content crawling
- **beautifulsoup4**: HTML parsing and content extraction
- **ollama**: AI analysis and vision processing
- **rich**: Enhanced console output and progress tracking
- **requests**: HTTP requests and session management
- **imagehash**: Image duplicate detection
- **pillow**: Image processing and analysis
- **pandas**: Data analysis and export

## License

This project is provided as-is for documentation analysis purposes.