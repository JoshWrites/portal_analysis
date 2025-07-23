// Zendesk Help Center Crawler - Content Script
class ZendeskCrawler {
  constructor() {
    this.isCrawling = false;
    this.visitedUrls = new Set();
    this.crawledData = [];
    this.baseUrl = window.location.origin;
    this.currentUrl = window.location.href;
    this.isZendeskHelpCenter = this.detectZendeskHelpCenter();
    this.storageStrategy = 'auto-download'; // 'auto-download', 'streaming', or 'memory'
    this.runId = this.generateRunId();
    this.chunkCounter = 0;
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
    
    // If we couldn't extract from URL, try to get from page content
    if (!hierarchy.category || !hierarchy.section) {
      this.extractHierarchyFromPage(hierarchy);
    }
    
    return hierarchy;
  }

  // Extract hierarchy information from page content
  extractHierarchyFromPage(hierarchy) {
    // Try to find category and section from breadcrumbs
    const breadcrumbSelectors = [
      '.breadcrumb a',
      '.breadcrumbs a',
      '[class*="breadcrumb"] a',
      'nav[aria-label="breadcrumb"] a',
      '.breadcrumb li a',
      '.breadcrumbs li a',
      'ol.breadcrumb li a',
      'ul.breadcrumb li a',
      '.breadcrumb span',
      '.breadcrumbs span',
      '[class*="breadcrumb"] span',
      'nav[aria-label="breadcrumb"] span'
    ];
    
    for (const selector of breadcrumbSelectors) {
      const breadcrumbLinks = document.querySelectorAll(selector);
      if (breadcrumbLinks.length > 0) {
        const links = Array.from(breadcrumbLinks);
        console.log('Found breadcrumb links:', links.length);
        
        // Extract full breadcrumb path
        const breadcrumbPath = links.map(link => link.textContent.trim()).filter(text => text.length > 0);
        console.log('Breadcrumb path:', breadcrumbPath);
        
        // Also try to get breadcrumb text from the container
        let breadcrumbText = '';
        const breadcrumbContainer = document.querySelector('.breadcrumb, .breadcrumbs, [class*="breadcrumb"]');
        if (breadcrumbContainer) {
          breadcrumbText = breadcrumbContainer.textContent.trim();
          console.log('Breadcrumb container text:', breadcrumbText);
        }
        
        // Look for category and section in breadcrumbs
        for (let i = 0; i < links.length - 1; i++) {
          const link = links[i];
          const text = link.textContent.trim();
          const href = link.getAttribute('href');
          
          // Try multiple patterns for category detection
          if (!hierarchy.category) {
            // Pattern 1: Direct category match in href
            if (href && href.includes('/categories/')) {
              const match = href.match(/\/categories\/(\d+)-([\w-]+)/);
              if (match) {
                hierarchy.category = {
                  id: match[1],
                  name: text || match[2].replace(/-/g, ' ')
                };
                console.log('Found category from href:', hierarchy.category);
              }
            }
            // Pattern 2: Look for category in breadcrumb path (usually second item)
            else if (breadcrumbPath.length >= 2 && i === 1) {
              hierarchy.category = {
                id: `cat_${i}`,
                name: text
              };
              console.log('Found category from breadcrumb position:', hierarchy.category);
            }
            // Pattern 3: Look for common category names
            else if (text && this.isLikelyCategory(text)) {
              hierarchy.category = {
                id: `cat_${i}`,
                name: text
              };
              console.log('Found category from text analysis:', hierarchy.category);
            }
          }
          
          // Try multiple patterns for section detection
          if (!hierarchy.section) {
            // Pattern 1: Direct section match in href
            if (href && href.includes('/sections/')) {
              const match = href.match(/\/sections\/(\d+)-([\w-]+)/);
              if (match) {
                hierarchy.section = {
                  id: match[1],
                  name: text || match[2].replace(/-/g, ' ')
                };
                console.log('Found section from href:', hierarchy.section);
              }
            }
            // Pattern 2: Look for section in breadcrumb path (usually third item)
            else if (breadcrumbPath.length >= 3 && i === 2) {
              hierarchy.section = {
                id: `sec_${i}`,
                name: text
              };
              console.log('Found section from breadcrumb position:', hierarchy.section);
            }
            // Pattern 3: Look for common section names
            else if (text && this.isLikelySection(text)) {
              hierarchy.section = {
                id: `sec_${i}`,
                name: text
              };
              console.log('Found section from text analysis:', hierarchy.section);
            }
          }
        }
        
        // If we still don't have category/section, try to infer from breadcrumb structure
        if (!hierarchy.category && breadcrumbPath.length >= 2) {
          hierarchy.category = {
            id: 'cat_inferred',
            name: breadcrumbPath[1] || 'General'
          };
          console.log('Inferred category from breadcrumb:', hierarchy.category);
        }
        
        if (!hierarchy.section && breadcrumbPath.length >= 3) {
          hierarchy.section = {
            id: 'sec_inferred',
            name: breadcrumbPath[2] || 'General'
          };
          console.log('Inferred section from breadcrumb:', hierarchy.section);
        }
        
        // Additional parsing from breadcrumb text
        if (breadcrumbText && (!hierarchy.category || !hierarchy.section)) {
          // Parse breadcrumb text like "IRONSCALES > API > IRONSCALES Application API"
          const breadcrumbParts = breadcrumbText.split('>').map(part => part.trim()).filter(part => part.length > 0);
          console.log('Parsed breadcrumb parts:', breadcrumbParts);
          
          if (!hierarchy.category && breadcrumbParts.length >= 2) {
            hierarchy.category = {
              id: 'cat_text',
              name: breadcrumbParts[1]
            };
            console.log('Found category from breadcrumb text:', hierarchy.category);
          }
          
          if (!hierarchy.section && breadcrumbParts.length >= 3) {
            hierarchy.section = {
              id: 'sec_text',
              name: breadcrumbParts[2]
            };
            console.log('Found section from breadcrumb text:', hierarchy.section);
          }
        }
        
        break;
      }
    }
    
    // Fallback: If no breadcrumbs found, try to extract from URL path
    if (!hierarchy.category || !hierarchy.section) {
      this.extractHierarchyFromURL(window.location.href, hierarchy);
    }
    
    // Final fallback: Use defaults
    if (!hierarchy.category) {
      hierarchy.category = {
        id: 'uncategorized',
        name: 'Uncategorized'
      };
    }
    
    if (!hierarchy.section) {
      hierarchy.section = {
        id: 'general',
        name: 'General'
      };
    }
    
    console.log('Final hierarchy:', hierarchy);
  }

  // Helper method to check if text is likely a category
  isLikelyCategory(text) {
    if (!text) return false;
    const categoryKeywords = [
      'api', 'home', 'faq', 'settings', 'getting started', 'incidents', 
      'investigation', 'mailboxes', 'simulation', 'training', 'product updates',
      'internal kb', 'protected mailboxes', 'incident management'
    ];
    return categoryKeywords.some(keyword => 
      text.toLowerCase().includes(keyword)
    );
  }

  // Helper method to check if text is likely a section
  isLikelySection(text) {
    if (!text) return false;
    const sectionKeywords = [
      'general', 'overview', 'setup', 'configuration', 'troubleshooting',
      'integration', 'authentication', 'permissions', 'alerts'
    ];
    return sectionKeywords.some(keyword => 
      text.toLowerCase().includes(keyword)
    );
  }

  // Extract hierarchy from URL as fallback
  extractHierarchyFromURL(url, hierarchy) {
    const urlObj = new URL(url);
    const path = urlObj.pathname;
    
    // Try to extract from URL path patterns
    const pathParts = path.split('/').filter(part => part.length > 0);
    
    // Look for category and section in URL path
    for (let i = 0; i < pathParts.length; i++) {
      const part = pathParts[i];
      
      // Category pattern: /categories/123-category-name
      if (part === 'categories' && i + 1 < pathParts.length) {
        const categoryPart = pathParts[i + 1];
        const categoryMatch = categoryPart.match(/^(\d+)-(.+)$/);
        if (categoryMatch && !hierarchy.category) {
          hierarchy.category = {
            id: categoryMatch[1],
            name: categoryMatch[2].replace(/-/g, ' ')
          };
        }
      }
      
      // Section pattern: /sections/456-section-name
      if (part === 'sections' && i + 1 < pathParts.length) {
        const sectionPart = pathParts[i + 1];
        const sectionMatch = sectionPart.match(/^(\d+)-(.+)$/);
        if (sectionMatch && !hierarchy.section) {
          hierarchy.section = {
            id: sectionMatch[1],
            name: sectionMatch[2].replace(/-/g, ' ')
          };
        }
      }
    }
  }

  // Generate unique run ID for this crawl session
  generateRunId() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day}_${hours}-${minutes}-${seconds}`;
  }

  // Auto-download storage management for large datasets
  async saveAutoDownloadData(pageData) {
    try {
      // Get current buffer
      const result = await chrome.storage.local.get(['dataBuffer', 'bufferSize']);
      let dataBuffer = result.dataBuffer || [];
      let bufferSize = result.bufferSize || 0;
      
      // Add new page to buffer
      dataBuffer.push(pageData);
      bufferSize += JSON.stringify(pageData).length;
      
      // If buffer is getting large, download and purge
      if (bufferSize > 1024 * 1024) { // 1MB buffer limit
        console.log(`Buffer size ${bufferSize} exceeds limit, triggering download...`);
        
        // Download current buffer as ZIP
        try {
          const downloadSuccess = await this.downloadChunk(dataBuffer);
          
          if (downloadSuccess) {
            // Clear buffer after successful download
            await chrome.storage.local.set({
              dataBuffer: [],
              bufferSize: 0,
              chunkCounter: this.chunkCounter
            });
            
            console.log(`Downloaded chunk ${this.chunkCounter}, cleared buffer`);
          } else {
            console.error('Failed to download chunk, keeping in buffer');
          }
        } catch (downloadError) {
          console.error('Error during download:', downloadError);
          // Keep data in buffer if download fails
        }
      } else {
        // Just update buffer
        await chrome.storage.local.set({
          dataBuffer: dataBuffer,
          bufferSize: bufferSize,
          chunkCounter: this.chunkCounter
        });
      }
      
      return true;
    } catch (error) {
      console.error('Error saving auto-download data:', error);
      return false;
    }
  }

  // Download chunk as ZIP file
  async downloadChunk(dataBuffer) {
    return new Promise(async (resolve, reject) => {
      try {
        this.chunkCounter++;
        const chunkNumber = String(this.chunkCounter).padStart(3, '0');
        
        // Create dedicated subdirectory structure
        const subdir = `zendesk_chunks/${this.runId}`;
        const filename = `${subdir}/chunk_${chunkNumber}.zip`;
        
        // Create ZIP content
        const zip = new JSZip();
        
        // Add README with chunk info
        let readme = `# Zendesk Help Center Chunk ${this.chunkCounter}\n\n`;
        readme += `Generated on: ${new Date().toISOString()}\n`;
        readme += `Run ID: ${this.runId}\n`;
        readme += `Chunk Number: ${this.chunkCounter}\n`;
        readme += `Total Articles: ${dataBuffer.length}\n\n`;
        
        zip.file('README.md', readme);
        
        // Add session info for tracking
        const sessionInfo = {
          runId: this.runId,
          chunkNumber: this.chunkCounter,
          totalChunks: this.chunkCounter,
          articlesInChunk: dataBuffer.length,
          timestamp: new Date().toISOString(),
          baseUrl: this.baseUrl
        };
        zip.file('session_info.json', JSON.stringify(sessionInfo, null, 2));
        
        // Add each page as markdown file
        for (const page of dataBuffer) {
          const hierarchy = page.metadata?.hierarchy || {};
          const category = hierarchy.category?.name || 'Uncategorized';
          const section = hierarchy.section?.name || 'General';
          
          // Create directory structure
          const dirPath = `${category}/${section}/`;
          const fileName = `${page.title.replace(/[^a-zA-Z0-9]/g, '_')}.md`;
          const filePath = dirPath + fileName;
          
          // Create markdown content
          let markdown = `# ${page.title}\n\n`;
          markdown += `**URL:** ${page.url}\n`;
          markdown += `**Category:** ${category}\n`;
          markdown += `**Section:** ${section}\n\n`;
          markdown += page.content;
          
          zip.file(filePath, markdown);
        }
        
        // Generate ZIP blob
        const zipBlob = await zip.generateAsync({type: 'blob'});
        
        // Convert blob to base64 for message passing
        const reader = new FileReader();
        reader.onload = () => {
          const base64Data = reader.result.split(',')[1]; // Remove data URL prefix
          
          // Send download request to background script
          chrome.runtime.sendMessage({
            action: 'downloadChunk',
            data: {
              filename: filename,
              base64Data: base64Data,
              chunkNumber: this.chunkCounter,
              runId: this.runId
            }
          }, (response) => {
            if (chrome.runtime.lastError) {
              console.error('Download error:', chrome.runtime.lastError);
              reject(new Error(chrome.runtime.lastError.message));
            } else if (response && response.success) {
              console.log(`Download started: ${filename} (ID: ${response.downloadId})`);
              resolve(true);
            } else {
              console.error('Download failed:', response);
              reject(new Error(response?.error || 'Download failed'));
            }
          });
        };
        
        reader.onerror = () => {
          reject(new Error('Failed to read blob data'));
        };
        
        reader.readAsDataURL(zipBlob);
        
      } catch (error) {
        console.error('Error creating/downloading chunk:', error);
        reject(error);
      }
    });
  }



  // Get all streaming data
  async getAllStreamingData() {
    try {
      const result = await chrome.storage.local.get(['crawledData', 'dataBuffer']);
      const storedData = result.crawledData || [];
      const bufferData = result.dataBuffer || [];
      
      // Combine stored data with current buffer
      return [...storedData, ...bufferData];
    } catch (error) {
      console.error('Error getting streaming data:', error);
      return [];
    }
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
    this.chunkCounter = 0; // Reset chunk counter
    
    console.log('Starting Zendesk crawler...');
    
    // Update status and initialize counters
    chrome.storage.local.set({
      crawlingStatus: 'crawling',
      chunkCounter: 0,
      chunksDownloaded: 0,
      pendingDownloads: {},
      dataBuffer: [],
      bufferSize: 0
    });
    
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
        // Use auto-download storage for better memory management
        const saveSuccess = await this.saveAutoDownloadData(pageData);
        
        if (!saveSuccess) {
          console.error('Failed to save page data, stopping crawl to prevent data loss');
          this.isCrawling = false;
          break;
        }
        
        // Keep a small in-memory array for progress tracking
        this.crawledData.push(pageData);
        
        // Update storage for progress tracking
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