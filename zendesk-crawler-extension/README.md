# Zendesk Help Center Crawler - Browser Extension

A Chrome browser extension that automatically detects and crawls any Zendesk Help Center using your existing authenticated session. Works with any company's Zendesk Help Center - just navigate to the site and start crawling!

## Features

- **Authenticated Crawling**: Uses your existing login session (no OIDC/SSO issues)
- **Automatic Discovery**: Finds and crawls categories, sections, and articles
- **Content Extraction**: Extracts text, links, images, and metadata
- **Hierarchy Mapping**: Identifies category/section/article relationships
- **Export Functionality**: Exports data as JSON for further processing

## Installation

### Method 1: Load Unpacked Extension (Recommended)

1. **Download the extension files** to your computer
2. **Open Chrome** and go to `chrome://extensions/`
3. **Enable "Developer mode"** (toggle in top right)
4. **Click "Load unpacked"** and select the `zendesk-crawler-extension` folder
5. **The extension should appear** in your extensions list

### Method 2: From Source

1. **Clone or download** this repository
2. **Navigate to the extension folder**: `cd zendesk-crawler-extension`
3. **Follow Method 1** above

## Usage

### Prerequisites

- **Chrome browser** (or Chromium-based browser)
- **Access to any Zendesk Help Center** (you should be logged in)
- **The extension automatically detects Zendesk Help Centers** - no configuration needed

### Steps

1. **Navigate to any Zendesk Help Center**
   - Examples: 
     - `https://support.yourcompany.com/hc/en-us`
     - `https://help.yourcompany.com/`
     - `https://docs.yourcompany.com/`
     - `https://knowledge.yourcompany.com/`
   - Make sure you're logged in
   - The extension will automatically detect if it's a Zendesk Help Center

2. **Click the extension icon** in your browser toolbar
   - You should see the "Zendesk Crawler" popup

3. **Click "Start Crawling"**
   - The extension will begin crawling the current page
   - It will automatically discover and visit linked pages
   - Progress is shown in real-time

4. **Monitor Progress**
   - Watch the status updates in the popup
   - Check the browser console for detailed logs
   - The extension will crawl categories → sections → articles

5. **Export Data**
   - Click "Export Data" to download the crawled content as JSON
   - The file will be saved as `zendesk_crawled_data_YYYY-MM-DD.json`

### What Gets Crawled

- **Categories**: `/hc/en-us/categories/123-category-name`
- **Sections**: `/hc/en-us/sections/456-section-name`
- **Articles**: `/hc/en-us/articles/789-article-title`
- **Root pages**: `/hc/en-us`

### What Gets Extracted

For each page:
- **Title**: Page title
- **Content**: Full text content
- **Links**: All Zendesk content links found
- **Images**: All images with URLs and alt text
- **Metadata**: Last updated date, breadcrumbs, hierarchy info

## Data Structure

The exported JSON contains an array of page objects:

```json
[
  {
    "url": "https://support.company.com/hc/en-us/articles/123-article",
    "title": "Article Title",
    "content": "Full article content...",
    "links": [
      {
        "url": "https://support.company.com/hc/en-us/sections/456-section",
        "text": "Section Name"
      }
    ],
    "images": [
      {
        "url": "https://support.company.com/image.png",
        "alt": "Image description",
        "title": "Image title"
      }
    ],
    "metadata": {
      "title": "Article Title",
      "url": "https://support.company.com/hc/en-us/articles/123-article",
      "lastUpdated": "2024-01-15",
      "breadcrumb": "Home > Category > Section",
      "hierarchy": {
        "category": {"id": "123", "name": "category-name"},
        "section": {"id": "456", "name": "section-name"},
        "article": {"id": "789", "name": "article-title"}
      }
    }
  }
]
```

## Troubleshooting

### Extension Not Working

1. **Check if you're on a Zendesk Help Center page**
   - URL should contain `zendesk.com/hc/`
   - Extension only works on Help Center pages

2. **Check browser console for errors**
   - Press F12 to open developer tools
   - Look for error messages in the Console tab

3. **Verify permissions**
   - Go to `chrome://extensions/`
   - Find the extension and click "Details"
   - Ensure all permissions are granted

### No Content Found

1. **Make sure you're logged in**
   - The extension uses your existing session
   - If you're not logged in, content may be limited

2. **Check the page structure**
   - Some Zendesk instances may have custom layouts
   - The extension looks for standard Zendesk patterns

### Crawling Stops Unexpectedly

1. **Check the console logs**
   - Look for error messages
   - The extension logs detailed information

2. **Try starting from a different page**
   - Start from the main Help Center page (`/hc/en-us`)
   - Or try a specific category page

## Development

### File Structure

```
zendesk-crawler-extension/
├── manifest.json          # Extension configuration
├── popup.html            # Extension popup UI
├── popup.js              # Popup functionality
├── content.js            # Content script (runs on pages)
├── background.js         # Background service worker
├── icons/                # Extension icons
└── README.md            # This file
```

### Modifying the Extension

1. **Edit the files** as needed
2. **Go to `chrome://extensions/`**
3. **Click the refresh icon** on the extension
4. **Test your changes**

### Adding Features

- **New content types**: Modify `content.js` extraction logic
- **Different export formats**: Update `popup.js` export function
- **Additional metadata**: Extend `extractMetadata()` in `content.js`

## Security Notes

- **No data is sent to external servers**
- **All data is stored locally** in Chrome's storage
- **The extension only accesses Zendesk Help Center pages**
- **Your login credentials are never accessed**

## Support

For issues or questions:
1. **Check the browser console** for error messages
2. **Verify you're on a Zendesk Help Center page**
3. **Ensure you're logged in** to the Help Center
4. **Try refreshing the extension** in `chrome://extensions/`

## License

This extension is provided as-is for educational and development purposes. 