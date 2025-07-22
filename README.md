# Zendesk Help Center Crawler & Processor

A complete solution for crawling Zendesk Help Centers and generating structured deliverables.

## 🎯 **What This Does**

This project provides **two complementary approaches** for crawling Zendesk Help Centers:

1. **Browser Extension** - Authenticated crawling using your existing session
2. **Python Script** - Automated crawling with Playwright (for non-authenticated portals)

Both approaches generate the same **three deliverables**:

1. **📋 Sitemap** - Site structure with article titles and last updated dates
2. **📁 Scraped Content** - Markdown files organized by portal structure with attachments
3. **🤖 Ollama Analysis** - Single sourcing opportunities and image reuse detection

## 🚀 **Quick Start**

### **Option A: Browser Extension (Recommended)**

**Best for:** Authenticated Zendesk portals with SSO/OIDC

1. **Install the browser extension:**
   ```bash
   # Load the extension in Chrome
   # Go to chrome://extensions/
   # Enable "Developer mode"
   # Click "Load unpacked" and select zendesk-crawler-extension/
   ```

2. **Navigate to your Zendesk Help Center** (e.g., `https://support.company.com/hc/en-us`)

3. **Click the extension icon** and click "Start Crawling"

4. **Export the data** and process it:
   ```bash
   python zendesk_processor.py zendesk_crawled_data.json processed_content
   ```

### **Option B: Python Script**

**Best for:** Public portals or when you need automated crawling

```bash
python doc_analyzer.py
# Enter your Zendesk URL and follow the prompts
```

## 📁 **Project Structure**

```
portal_analysis/
├── zendesk-crawler-extension/     # Browser extension
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   ├── content.js
│   ├── background.js
│   └── README.md
├── zendesk_processor.py           # Processes extension data
├── doc_analyzer.py               # Python crawler
├── rag_processor.py              # RAG-specific processor
└── README.md                     # This file
```

## 🎯 **Deliverables Generated**

### **1. Sitemap (`sitemap.md`)**
- **Site structure** organized by categories and sections
- **Article titles** and URLs
- **Last updated dates** for each article
- **Summary statistics** (total pages, date coverage, etc.)

### **2. Scraped Content (`content/` directory)**
```
content/
├── Category Name/
│   ├── Section Name/
│   │   ├── Article Title/
│   │   │   ├── 2024-01-15_article-title.md
│   │   │   └── attachments/
│   │   │       ├── image_1_screenshot.png
│   │   │       └── image_2_diagram.png
│   │   └── Another Article/
│   └── Another Section/
└── Another Category/
```

### **3. Ollama Analysis (`analysis_report.md`)**
- **Single-source opportunities** - Content that could be consolidated
- **Image reuse detection** - Same images used across multiple articles
- **AI-powered insights** using Llava model

## 🔧 **Installation**

### **Prerequisites**
```bash
pip install -r requirements.txt
```

### **Browser Extension Setup**
1. **Navigate to** `chrome://extensions/`
2. **Enable "Developer mode"**
3. **Click "Load unpacked"**
4. **Select the** `zendesk-crawler-extension/` folder

## 📖 **Usage Examples**

### **Browser Extension Workflow**

1. **Install the extension** (see Installation above)

2. **Navigate to your Zendesk Help Center**
   ```
   https://support.yourcompany.com/hc/en-us
   ```

3. **Click the extension icon** and click "Start Crawling"

4. **Wait for crawling to complete** (watch the progress)

5. **Click "Export Data"** to download the JSON file

6. **Process the data:**
   ```bash
   python zendesk_processor.py zendesk_crawled_data.json my_output
   ```

### **Python Script Workflow**

1. **Run the crawler:**
   ```bash
   python doc_analyzer.py
   ```

2. **Enter your Zendesk URL** when prompted

3. **Wait for crawling and analysis to complete**

4. **Check the generated files:**
   - `sitemap.md`
   - `crawled_content/` directory
   - `doc_analysis.json`
   - `doc_summary.md`

## 🔍 **Key Features**

### **Browser Extension Advantages**
- ✅ **Uses your existing login session** (no authentication issues)
- ✅ **Access to fully rendered content** (JavaScript executed)
- ✅ **Real-time progress tracking**
- ✅ **No browser automation complexity**
- ✅ **Works with SSO/OIDC portals**

### **Python Script Advantages**
- ✅ **Fully automated** (no manual intervention)
- ✅ **Advanced analysis** with Ollama AI
- ✅ **Comprehensive reporting**
- ✅ **Image analysis** and duplicate detection
- ✅ **Mermaid diagram extraction**

### **Processor Features**
- ✅ **Hierarchical organization** by category/section/article
- ✅ **Attachment downloading** and local storage
- ✅ **Image hash analysis** for reuse detection
- ✅ **AI-powered content analysis**
- ✅ **Markdown export** with metadata

## 🛠 **Configuration**

### **Browser Extension**
- **Permissions:** Only accesses Zendesk Help Center pages
- **Storage:** All data stored locally in Chrome
- **Export:** JSON format for further processing

### **Python Script**
- **Model:** Uses Llava for AI analysis
- **Authentication:** Supports OIDC/SSO via Playwright
- **Output:** Multiple formats (JSON, Markdown, HTML)

### **Processor**
- **Model:** Configurable Ollama model (default: Llava)
- **Structure:** Mirrors Zendesk portal hierarchy
- **Attachments:** Downloads and organizes images

## 🔧 **Troubleshooting**

### **Browser Extension Issues**

**Extension not working:**
1. Check if you're on a Zendesk Help Center page (`zendesk.com/hc/`)
2. Verify you're logged in to the Help Center
3. Check browser console for errors (F12)

**No content found:**
1. Ensure you're logged in
2. Try starting from the main Help Center page
3. Check if the portal uses custom layouts

### **Python Script Issues**

**Authentication problems:**
1. Use the browser extension instead
2. Check if your portal requires SSO
3. Verify the URL format

**Crawling issues:**
1. Enable debug mode for detailed logs
2. Check if the portal is accessible
3. Verify network connectivity

### **Processor Issues**

**JSON file not found:**
1. Export data from the browser extension first
2. Check the file path is correct
3. Verify the JSON file is valid

**Ollama errors:**
1. Ensure Ollama is running: `ollama serve`
2. Check if the Llava model is installed: `ollama pull llava`
3. Verify network connectivity

## 📊 **Output Examples**

### **Sitemap Structure**
```markdown
# Zendesk Help Center Sitemap

## Getting Started
### Installation
| Title | Last Updated | URL |
|-------|--------------|-----|
| Installing the App | 2024-01-15 | https://support.company.com/hc/articles/123 |
| First Time Setup | 2024-01-10 | https://support.company.com/hc/articles/124 |

### Configuration
| Title | Last Updated | URL |
|-------|--------------|-----|
| API Configuration | 2024-01-12 | https://support.company.com/hc/articles/125 |
```

### **Content Directory**
```
processed_content/
├── Getting Started/
│   ├── Installation/
│   │   ├── Installing the App/
│   │   │   ├── 2024-01-15_installing-the-app.md
│   │   │   └── attachments/
│   │   │       ├── image_1_install_screenshot.png
│   │   │       └── image_2_setup_diagram.png
```

### **Analysis Report**
```markdown
# Zendesk Help Center Analysis Report

## Single-Source Opportunities

### Opportunity 1
**Pages with similar content:**
- Installing the App (https://support.company.com/hc/articles/123)
- First Time Setup (https://support.company.com/hc/articles/124)

**Analysis:** YES - Both pages contain similar installation steps that could be consolidated into a single guide.

## Image Reuse Analysis

### Image 1 (used 3 times)
- **Installing the App** (https://support.company.com/image1.png)
- **First Time Setup** (https://support.company.com/image1.png)
- **Configuration Guide** (https://support.company.com/image1.png)
```

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

## 📄 **License**

This project is provided as-is for educational and development purposes.

## 🆘 **Support**

For issues or questions:
1. **Check the troubleshooting section** above
2. **Review the browser console** for error messages
3. **Verify you're on a Zendesk Help Center page**
4. **Ensure you're logged in** to the Help Center