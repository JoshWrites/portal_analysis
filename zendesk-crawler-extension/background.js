// Zendesk Help Center Crawler - Background Service Worker

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Zendesk Crawler extension installed');
  
  // Initialize storage
  chrome.storage.local.set({
    crawlingStatus: 'idle',
    crawledData: []
  });
});

// Handle messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getStatus') {
    chrome.storage.local.get(['crawlingStatus', 'crawledData'], (result) => {
      sendResponse({
        status: result.crawlingStatus || 'idle',
        dataCount: result.crawledData ? result.crawledData.length : 0
      });
    });
    return true; // Keep message channel open for async response
  }
  
  if (request.action === 'clearData') {
    chrome.storage.local.set({
      crawledData: []
    });
    sendResponse({success: true});
  }
  
  if (request.action === 'exportData') {
    chrome.storage.local.get(['crawledData'], (result) => {
      if (result.crawledData && result.crawledData.length > 0) {
        const dataStr = JSON.stringify(result.crawledData, null, 2);
        const blob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        chrome.downloads.download({
          url: url,
          filename: `zendesk_crawled_data_${new Date().toISOString().split('T')[0]}.json`,
          saveAs: true
        });
        
        sendResponse({success: true});
      } else {
        sendResponse({success: false, error: 'No data to export'});
      }
    });
    return true; // Keep message channel open for async response
  }
});

// Handle tab updates to inject content script if needed
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('zendesk.com/hc/')) {
    // Content script should auto-inject, but we can add additional logic here if needed
    console.log('Zendesk Help Center page loaded:', tab.url);
  }
});

console.log('Zendesk Crawler background script loaded'); 