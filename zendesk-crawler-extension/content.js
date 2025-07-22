// Zendesk Help Center Crawler - Content Script
class ZendeskCrawler {
  constructor() {
    this.isCrawling = false;
    this.visitedUrls = new Set();
    this.crawledData = [];
    this.baseUrl = window.location.origin;
    this.currentUrl = window.location.href;
    this.isZendeskHelpCenter = this.detectZendeskHelpCenter();
  }

  detectZendeskHelpCenter() {
    // Check if this is a Zendesk Help Center
    const url = window.location.href;
    const path = window.location.pathname;
    
    // Common Zendesk Help Center patterns
    const zendeskPatterns = [
      /\/hc\//,  // Standard Zendesk Help Center path
      /help\./,  // Help subdomains
      /support\./, // Support subdomains
      /docs\./,  // Docs subdomains
      /knowledge\./, // Knowledge base
      /zendesk\.com\/hc\//, // Official Zendesk
    ];
    
    return zendeskPatterns.some(pattern => 
      pattern.test(url) || pattern.test(path)
    );
  }

  // Check if URL is a Zendesk content link
  isZendeskContentLink(url) {
    const urlObj = new URL(url, this.baseUrl);
    const path = urlObj.pathname;
    
    // Accept root, categories, sections, articles
    if (/^\/hc\/[^\/]+$/.test(path)) return true;
    if (/^\/hc\/[^\/]+\/categories\/\d+-/.test(path)) return true;
    if (/^\/hc\/[^\/]+\/sections\/\d+-/.test(path)) return true;
    if (/^\/hc\/[^\/]+\/articles\/\d+-/.test(path)) return true;
    
    return false;
  }

  // Extract hierarchy from URL
  extractHierarchy(url) {
    const urlObj = new URL(url, this.baseUrl);
    const path = urlObj.pathname;
    const hierarchy = {category: null, section: null, article: null};
    
    // Category
    const categoryMatch = path.match(/\/categories\/(\d+)-([\w-]+)/);
    if (categoryMatch) {
      hierarchy.category = {id: categoryMatch[1], name: categoryMatch[2]};
    }
    
    // Section
    const sectionMatch = path.match(/\/sections\/(\d+)-([\w-]+)/);
    if (sectionMatch) {
      hierarchy.section = {id: sectionMatch[1], name: sectionMatch[2]};
    }
    
    // Article
    const articleMatch = path.match(/\/articles\/(\d+)-([\w-]+)/);
    if (articleMatch) {
      hierarchy.article = {id: articleMatch[1], name: articleMatch[2]};
    }
    
    return hierarchy;
  }

  // Extract metadata from page
  extractMetadata() {
    const metadata = {
      title: document.title,
      url: window.location.href,
      lastUpdated: null,
      breadcrumb: null,
      hierarchy: this.extractHierarchy(window.location.href)
    };

    // Try to find last updated date
    const dateSelectors = [
      'meta[property="article:modified_time"]',
      'meta[name="last-modified"]',
      '[data-last-updated]',
      '.last-updated',
      '.updated-date'
    ];

    for (const selector of dateSelectors) {
      const element = document.querySelector(selector);
      if (element) {
        const dateStr = element.getAttribute('content') || element.textContent;
        if (dateStr) {
          metadata.lastUpdated = dateStr.trim();
          break;
        }
      }
    }

    // Try to find breadcrumb
    const breadcrumbSelectors = [
      '.breadcrumb',
      '.breadcrumbs',
      '[class*="breadcrumb"]'
    ];

    for (const selector of breadcrumbSelectors) {
      const breadcrumb = document.querySelector(selector);
      if (breadcrumb) {
        metadata.breadcrumb = breadcrumb.textContent.trim();
        break;
      }
    }

    return metadata;
  }

  // Extract markdown content from the page
  extractMarkdownContent() {
    // Find the main content area
    const contentSelectors = [
      '.article-body',
      '.article-content',
      '.content',
      '.main-content',
      '[role="main"]',
      'main',
      '.article',
      '.post-content'
    ];
    
    let contentElement = null;
    for (const selector of contentSelectors) {
      contentElement = document.querySelector(selector);
      if (contentElement) break;
    }
    
    if (!contentElement) {
      contentElement = document.body;
    }
    
    // Convert HTML to markdown-like content
    let markdown = `# ${document.title}\n\n`;
    
    // Add metadata
    const metadata = this.extractMetadata();
    if (metadata.lastUpdated) {
      markdown += `**Last Updated:** ${metadata.lastUpdated}\n\n`;
    }
    if (metadata.breadcrumb) {
      markdown += `**Breadcrumb:** ${metadata.breadcrumb}\n\n`;
    }
    
    // Extract headings and content
    const headings = contentElement.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const paragraphs = contentElement.querySelectorAll('p, div, li');
    
    // Add headings
    headings.forEach(heading => {
      const level = parseInt(heading.tagName.charAt(1));
      const prefix = '#'.repeat(level);
      markdown += `${prefix} ${heading.textContent.trim()}\n\n`;
    });
    
    // Add paragraphs
    paragraphs.forEach(p => {
      if (p.textContent.trim() && !p.querySelector('h1, h2, h3, h4, h5, h6')) {
        markdown += `${p.textContent.trim()}\n\n`;
      }
    });
    
    return markdown;
  }

  // Extract content from current page
  extractPageContent() {
    const content = {
      url: window.location.href,
      title: document.title,
      content: this.extractMarkdownContent(),
      links: [],
      images: [],
      metadata: this.extractMetadata()
    };

    // Extract all links
    const links = document.querySelectorAll('a[href]');
    for (const link of links) {
      const href = link.getAttribute('href');
      if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:')) {
        const absoluteUrl = new URL(href, window.location.href).href;
        if (this.isZendeskContentLink(absoluteUrl)) {
          content.links.push({
            url: absoluteUrl,
            text: link.textContent.trim()
          });
        }
      }
    }

    // Extract images
    const images = document.querySelectorAll('img[src]');
    for (const img of images) {
      const src = img.getAttribute('src');
      if (src) {
        const absoluteUrl = new URL(src, window.location.href).href;
        content.images.push({
          url: absoluteUrl,
          alt: img.getAttribute('alt') || '',
          title: img.getAttribute('title') || ''
        });
      }
    }

    return content;
  }

  // Start crawling from current page
  async startCrawling() {
    if (this.isCrawling) return;
    
    this.isCrawling = true;
    this.visitedUrls.clear();
    this.crawledData = [];
    
    console.log('Starting Zendesk crawler...');
    
    // Update status
    chrome.storage.local.set({crawlingStatus: 'crawling'});
    
    try {
      // Start from current page and crawl all linked pages
      await this.crawlAllPages(window.location.href);
      console.log('Crawling completed!');
    } catch (error) {
      console.error('Crawling error:', error);
      chrome.storage.local.set({crawlingStatus: 'error'});
    }
    
    this.isCrawling = false;
    chrome.storage.local.set({crawlingStatus: 'idle'});
  }

  // Crawl all pages recursively
  async crawlAllPages(startUrl) {
    const urlsToCrawl = [startUrl];
    const crawledUrls = new Set();
    
    while (urlsToCrawl.length > 0 && this.isCrawling) {
      const currentUrl = urlsToCrawl.shift();
      
      if (crawledUrls.has(currentUrl)) continue;
      crawledUrls.add(currentUrl);
      
      console.log('Crawling:', currentUrl);
      
      // Get page content using fetch (no navigation)
      const pageData = await this.fetchPageContent(currentUrl);
      if (pageData) {
        this.crawledData.push(pageData);
        
        // Save to storage
        chrome.storage.local.set({crawledData: this.crawledData});
        
        // Find new links to crawl
        const newLinks = pageData.links
          .map(link => link.url)
          .filter(url => !crawledUrls.has(url) && this.isZendeskContentLink(url))
          .slice(0, 20); // Limit to prevent infinite crawling
        
        urlsToCrawl.push(...newLinks);
        
        console.log(`Found ${newLinks.length} new links to crawl`);
      }
    }
  }

  // Fetch page content without navigating
  async fetchPageContent(url) {
    try {
      const response = await fetch(url);
      const html = await response.text();
      
      // Create a temporary DOM to parse the content
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      
      // Extract content using the same logic as extractPageContent
      const content = {
        url: url,
        title: doc.title,
        content: this.extractMarkdownFromDocument(doc),
        links: [],
        images: [],
        metadata: this.extractMetadataFromDocument(doc, url)
      };

      // Extract links
      const links = doc.querySelectorAll('a[href]');
      for (const link of links) {
        const href = link.getAttribute('href');
        if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:')) {
          const absoluteUrl = new URL(href, url).href;
          if (this.isZendeskContentLink(absoluteUrl)) {
            content.links.push({
              url: absoluteUrl,
              text: link.textContent.trim()
            });
          }
        }
      }

      // Extract images
      const images = doc.querySelectorAll('img[src]');
      for (const img of images) {
        const src = img.getAttribute('src');
        if (src) {
          const absoluteUrl = new URL(src, url).href;
          content.images.push({
            url: absoluteUrl,
            alt: img.getAttribute('alt') || '',
            title: img.getAttribute('title') || ''
          });
        }
      }

      return content;
    } catch (error) {
      console.error('Error fetching page:', url, error);
      return null;
    }
  }

  // Extract markdown from a document (not current page)
  extractMarkdownFromDocument(doc) {
    // Find the main content area
    const contentSelectors = [
      '.article-body',
      '.article-content',
      '.content',
      '.main-content',
      '[role="main"]',
      'main',
      '.article',
      '.post-content'
    ];
    
    let contentElement = null;
    for (const selector of contentSelectors) {
      contentElement = doc.querySelector(selector);
      if (contentElement) break;
    }
    
    if (!contentElement) {
      contentElement = doc.body;
    }
    
    // Convert HTML to markdown-like content
    let markdown = `# ${doc.title}\n\n`;
    
    // Add metadata
    const metadata = this.extractMetadataFromDocument(doc, doc.URL || '');
    if (metadata.lastUpdated) {
      markdown += `**Last Updated:** ${metadata.lastUpdated}\n\n`;
    }
    if (metadata.breadcrumb) {
      markdown += `**Breadcrumb:** ${metadata.breadcrumb}\n\n`;
    }
    
    // Extract headings and content
    const headings = contentElement.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const paragraphs = contentElement.querySelectorAll('p, div, li');
    
    // Add headings
    headings.forEach(heading => {
      const level = parseInt(heading.tagName.charAt(1));
      const prefix = '#'.repeat(level);
      markdown += `${prefix} ${heading.textContent.trim()}\n\n`;
    });
    
    // Add paragraphs
    paragraphs.forEach(p => {
      if (p.textContent.trim() && !p.querySelector('h1, h2, h3, h4, h5, h6')) {
        markdown += `${p.textContent.trim()}\n\n`;
      }
    });
    
    return markdown;
  }

  // Extract metadata from a document (not current page)
  extractMetadataFromDocument(doc, url) {
    const metadata = {
      title: doc.title,
      url: url,
      lastUpdated: null,
      breadcrumb: null,
      hierarchy: this.extractHierarchy(url)
    };

    // Try to find last updated date
    const dateSelectors = [
      'meta[property="article:modified_time"]',
      'meta[name="last-modified"]',
      '[data-last-updated]',
      '.last-updated',
      '.updated-date'
    ];

    for (const selector of dateSelectors) {
      const element = doc.querySelector(selector);
      if (element) {
        const dateStr = element.getAttribute('content') || element.textContent;
        if (dateStr) {
          metadata.lastUpdated = dateStr.trim();
          break;
        }
      }
    }

    // Try to find breadcrumb
    const breadcrumbSelectors = [
      '.breadcrumb',
      '.breadcrumbs',
      '[class*="breadcrumb"]'
    ];

    for (const selector of breadcrumbSelectors) {
      const breadcrumb = doc.querySelector(selector);
      if (breadcrumb) {
        metadata.breadcrumb = breadcrumb.textContent.trim();
        break;
      }
    }

    return metadata;
  }



  // Crawl a single page
  async crawlPage(url) {
    if (this.visitedUrls.has(url)) return;
    
    this.visitedUrls.add(url);
    console.log('Crawling:', url);
    
    // Extract content from current page
    const pageData = this.extractPageContent();
    this.crawledData.push(pageData);
    
    // Save to storage
    chrome.storage.local.set({crawledData: this.crawledData});
    
    // Find and crawl linked pages
    const linksToCrawl = pageData.links
      .map(link => link.url)
      .filter(linkUrl => !this.visitedUrls.has(linkUrl))
      .slice(0, 10); // Limit to prevent infinite crawling
    
    for (const linkUrl of linksToCrawl) {
      if (!this.isCrawling) break; // Check if stopped
      
      try {
        // Navigate to the link
        window.location.href = linkUrl;
        
        // Wait for page to load
        await new Promise(resolve => {
          const checkLoaded = () => {
            if (document.readyState === 'complete') {
              resolve();
            } else {
              setTimeout(checkLoaded, 100);
            }
          };
          checkLoaded();
        });
        
        // Crawl the new page
        await this.crawlPage(linkUrl);
        
      } catch (error) {
        console.error('Error crawling link:', linkUrl, error);
      }
    }
  }

  // Stop crawling
  stopCrawling() {
    this.isCrawling = false;
    console.log('Crawling stopped');
  }
}

// Initialize crawler
const crawler = new ZendeskCrawler();

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Content script received message:', request);
  
  if (request.action === 'checkZendesk') {
    console.log('Checking Zendesk, isZendeskHelpCenter:', crawler.isZendeskHelpCenter);
    sendResponse({isZendesk: crawler.isZendeskHelpCenter});
  } else if (request.action === 'startCrawling') {
    console.log('Starting crawling...');
    crawler.startCrawling();
    sendResponse({success: true});
  } else if (request.action === 'stopCrawling') {
    console.log('Stopping crawling...');
    crawler.stopCrawling();
    sendResponse({success: true});
  }
  
  return true; // Keep message channel open for async response
});

console.log('Zendesk Crawler content script loaded');
console.log('Window location:', window.location.href);
console.log('Document ready state:', document.readyState);
console.log('Frame type:', window !== window.top ? 'iframe' : 'main frame');

if (crawler.isZendeskHelpCenter) {
  console.log('✅ Detected Zendesk Help Center:', window.location.href);
} else {
  console.log('ℹ️ Not on a Zendesk Help Center:', window.location.href);
} 