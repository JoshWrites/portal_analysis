# Zendesk Help Center Crawler Extension

A Chrome extension for crawling Zendesk Help Centers and exporting content as structured markdown files with attachments.

## Features

### 🎯 **Core Functionality**
- **Automatic Detection**: Detects Zendesk Help Center pages automatically
- **Comprehensive Crawling**: Crawls all articles, categories, and sections
- **Hierarchy Preservation**: Maintains the original Help Center structure
- **Media Extraction**: Downloads images, PDFs, videos, and other attachments

### 📁 **Structured Export**
- **Directory Structure**: Creates folders that mirror the Help Center hierarchy
- **Markdown Files**: Each article becomes a properly formatted markdown file
- **Attachment Directories**: Media files are organized in `{article_name}_attachments` folders
- **Single Download**: Everything packaged in one downloadable ZIP file

### 🔧 **Export Structure**
```
zendesk_help_center_export.zip/
├── README.md                           # Site structure overview
├── Category_Name/
│   └── Section_Name/
│       └── Article_Name/
│           ├── Article_Name.md         # Article content
│           └── Article_Name_attachments/
│               ├── media_1.jpg         # Downloaded images
│               ├── media_2.pdf         # Downloaded PDFs
│               └── media_1.jpg.url     # Original URLs for reference
```

## Installation

1. **Download the Extension**
   ```bash
   git clone <repository-url>
   cd zendesk-crawler-extension
   ```

2. **Load in Chrome**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `zendesk-crawler-extension` folder

3. **Verify Installation**
   - The extension icon should appear in your toolbar
   - Navigate to any Zendesk Help Center to test

## Usage

### 🚀 **Getting Started**

1. **Navigate to a Zendesk Help Center**
   - Go to any Zendesk Help Center (e.g., `https://help.example.com`)
   - The extension will automatically detect it

2. **Start Crawling**
   - Click the extension icon
   - Click "Start Crawling"
   - Watch the progress as it crawls all articles

3. **Export Data**
   - Click "Export Data" when crawling is complete
   - Choose where to save the ZIP file
   - Extract and explore the structured content

### 📊 **Progress Tracking**

- **Pages Crawled**: Shows total articles processed
- **Links Found**: Shows internal links discovered
- **Content Size**: Shows total content size in KB
- **Real-time Updates**: Counters update as crawling progresses

### 📁 **Export Contents**

The exported ZIP file contains:

- **README.md**: Complete site structure with links
- **Structured Directories**: Organized by category → section → article
- **Markdown Files**: Clean, formatted content for each article
- **Media Files**: Downloaded images, PDFs, videos, and documents
- **URL References**: Original URLs for all media files

## Technical Details

### 🔍 **Content Detection**
- Automatically detects Zendesk Help Center URLs
- Supports various Zendesk URL patterns
- Extracts hierarchy from URLs and page content

### 📝 **Content Processing**
- Converts HTML to clean markdown
- Preserves headings, lists, and formatting
- Extracts metadata (last updated, breadcrumbs)
- Handles images, videos, PDFs, and documents

### 🖼️ **Media Handling**
- Downloads images and other media files
- Organizes attachments by article
- Preserves original file extensions
- Provides fallback URL references

### 🏗️ **Architecture**
- **Popup**: User interface and export functionality
- **Content Script**: Crawling logic and content extraction
- **Background Script**: State management and persistence
- **Storage**: Chrome storage for data persistence

## Python Integration

The exported data is designed to work with Python processing scripts:

```python
# Example usage with zendesk_processor.py
from zendesk_processor import process_export

# Process the exported ZIP file
process_export('zendesk_help_center_export.zip')
```

## Troubleshooting

### ❓ **Common Issues**

1. **Extension Not Detecting Zendesk**
   - Ensure you're on a valid Zendesk Help Center
   - Check that the URL contains `/hc/` or similar patterns
   - Try refreshing the page

2. **Crawling Not Starting**
   - Make sure you're on a Zendesk Help Center page
   - Check browser console for errors
   - Try reloading the extension

3. **Export Fails**
   - Ensure you have crawled some data first
   - Check that you have sufficient disk space
   - Verify Chrome download permissions

4. **Media Not Downloading**
   - Some media may be blocked by CORS policies
   - Check the `.url` files for original URLs
   - Manual download may be required for some files

### 🔧 **Debug Mode**

Enable debug logging by opening the browser console:
1. Press F12 to open Developer Tools
2. Go to Console tab
3. Look for extension-related logs

## Development

### 📁 **File Structure**
```
zendesk-crawler-extension/
├── manifest.json          # Extension configuration
├── popup.html            # Extension popup UI
├── popup.js              # Popup logic and export
├── content.js            # Content crawling logic
├── background.js         # Background service worker
└── README.md            # This file
```

### 🛠️ **Modifying the Extension**

1. **Adding New Media Types**
   - Edit `content.js` to add new selectors
   - Update `getMediaFilename()` in `popup.js`

2. **Changing Export Structure**
   - Modify `createStructuredExport()` in `popup.js`
   - Update `organizeDataByHierarchy()` for new organization

3. **Enhancing Crawling**
   - Modify `content.js` for new content extraction
   - Update `isZendeskContentLink()` for new URL patterns

## License

This extension is provided as-is for educational and development purposes.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review browser console for error messages
3. Ensure you're using a supported Zendesk Help Center

---

**Happy Crawling! 🕷️** 