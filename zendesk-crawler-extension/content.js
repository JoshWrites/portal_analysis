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

  // Extract content from current page
  extractPageContent() {
    const content = {
      url: window.location.href,
      title: document.title,
      content: document.body.innerText || document.body.textContent || '',
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
      await this.crawlPage(window.location.href);
      console.log('Crawling completed!');
    } catch (error) {
      console.error('Crawling error:', error);
      chrome.storage.local.set({crawlingStatus: 'error'});
    }
    
    this.isCrawling = false;
    chrome.storage.local.set({crawlingStatus: 'idle'});
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
  if (request.action === 'checkZendesk') {
    sendResponse({isZendesk: crawler.isZendeskHelpCenter});
  } else if (request.action === 'startCrawling') {
    crawler.startCrawling();
    sendResponse({success: true});
  } else if (request.action === 'stopCrawling') {
    crawler.stopCrawling();
    sendResponse({success: true});
  }
});

console.log('Zendesk Crawler content script loaded');
if (crawler.isZendeskHelpCenter) {
  console.log('✅ Detected Zendesk Help Center:', window.location.href);
} else {
  console.log('ℹ️ Not on a Zendesk Help Center:', window.location.href);
} 