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
  
  if (request.action === 'downloadChunk') {
    console.log('Download chunk request received:', request.data);
    try {
      const { filename, base64Data, chunkNumber, runId } = request.data;
      
      console.log('Converting base64 to blob...');
      console.log('Base64 data length:', base64Data.length);
      
      // Convert base64 back to blob
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/zip' });
      
      console.log('Blob created, size:', blob.size);
      console.log('Creating data URL...');
      
      // Convert blob to data URL
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result;
        console.log('Starting download with data URL');
        console.log('Filename:', filename);
        
        // Start download using data URL
        chrome.downloads.download({
          url: dataUrl,
          filename: filename,
          saveAs: false
        }, (downloadId) => {
          if (chrome.runtime.lastError) {
            console.error('Download error:', chrome.runtime.lastError);
            sendResponse({success: false, error: chrome.runtime.lastError.message});
          } else {
            console.log(`Download started: ${filename} (ID: ${downloadId})`);
            
            // Track this download
            chrome.storage.local.get(['pendingDownloads'], (result) => {
              const pendingDownloads = result.pendingDownloads || {};
              pendingDownloads[downloadId] = {
                filename: filename,
                timestamp: new Date().toISOString(),
                chunkNumber: chunkNumber,
                runId: runId
              };
              
              chrome.storage.local.set({pendingDownloads: pendingDownloads}, () => {
                console.log(`Tracking download ${downloadId} for ${filename}`);
              });
            });
            
            sendResponse({success: true, downloadId: downloadId});
          }
        });
      };
      
      reader.onerror = () => {
        console.error('Error reading blob data');
        sendResponse({success: false, error: 'Failed to read blob data'});
      };
      
      reader.readAsDataURL(blob);
      
    } catch (error) {
      console.error('Error handling download request:', error);
      sendResponse({success: false, error: error.message});
    }
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

// Handle download completion events
chrome.downloads.onChanged.addListener((downloadDelta) => {
  if (downloadDelta.state && downloadDelta.state.current === 'complete') {
    const downloadId = downloadDelta.id;
    
    // Check if this is one of our tracked downloads
    chrome.storage.local.get(['pendingDownloads', 'chunksDownloaded'], (result) => {
      const pendingDownloads = result.pendingDownloads || {};
      const chunksDownloaded = result.chunksDownloaded || 0;
      
      if (pendingDownloads[downloadId]) {
        const downloadInfo = pendingDownloads[downloadId];
        console.log(`Download completed: ${downloadInfo.filename}`);
        
        // Remove from pending downloads
        delete pendingDownloads[downloadId];
        
        // Increment downloaded counter
        const newDownloaded = chunksDownloaded + 1;
        
        chrome.storage.local.set({
          pendingDownloads: pendingDownloads,
          chunksDownloaded: newDownloaded
        }, () => {
          console.log(`Updated chunks downloaded: ${newDownloaded}`);
        });
      }
    });
  }
});

console.log('Zendesk Crawler background script loaded'); 