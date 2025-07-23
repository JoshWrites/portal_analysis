// Simple test content script
console.log('Test content script loaded');

// Mock crawler for testing
class TestCrawler {
  constructor() {
    this.isCrawling = false;
    this.crawledData = [];
  }

  async startCrawling() {
    console.log('Test: Starting crawling...');
    this.isCrawling = true;
    
    // Update status
    chrome.storage.local.set({crawlingStatus: 'crawling'});
    
    // Simulate crawling some pages
    const testPages = [
      {
        url: 'https://test.com/page1',
        title: 'Test Page 1',
        content: 'This is test content for page 1',
        links: ['https://test.com/link1', 'https://test.com/link2'],
        images: []
      },
      {
        url: 'https://test.com/page2',
        title: 'Test Page 2',
        content: 'This is test content for page 2 with more text to make it longer',
        links: ['https://test.com/link3'],
        images: []
      },
      {
        url: 'https://test.com/page3',
        title: 'Test Page 3',
        content: 'This is test content for page 3 with even more text to test the counter updates',
        links: ['https://test.com/link4', 'https://test.com/link5'],
        images: []
      }
    ];
    
    for (let i = 0; i < testPages.length; i++) {
      if (!this.isCrawling) break;
      
      console.log(`Test: Crawling page ${i + 1}`);
      this.crawledData.push(testPages[i]);
      
      // Save to storage
      chrome.storage.local.set({crawledData: this.crawledData});
      
      // Update progress
      const progress = {
        pagesCrawled: this.crawledData.length,
        totalIdentified: testPages.length,
        currentUrl: testPages[i].url
      };
      chrome.storage.local.set({crawlingProgress: progress});
      
      // Wait a bit to simulate crawling
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log('Test: Crawling completed!');
    this.isCrawling = false;
    chrome.storage.local.set({crawlingStatus: 'idle'});
  }

  stopCrawling() {
    console.log('Test: Stopping crawling...');
    this.isCrawling = false;
    chrome.storage.local.set({crawlingStatus: 'idle'});
  }
}

// Initialize test crawler
const testCrawler = new TestCrawler();

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Test: Content script received message:', request);
  
  if (request.action === 'checkZendesk') {
    console.log('Test: Checking Zendesk');
    sendResponse({isZendesk: true});
  } else if (request.action === 'startCrawling') {
    console.log('Test: Starting crawling...');
    testCrawler.startCrawling();
    sendResponse({success: true});
  } else if (request.action === 'stopCrawling') {
    console.log('Test: Stopping crawling...');
    testCrawler.stopCrawling();
    sendResponse({success: true});
  }
  
  return true; // Keep message channel open for async response
});

console.log('Test content script ready'); 