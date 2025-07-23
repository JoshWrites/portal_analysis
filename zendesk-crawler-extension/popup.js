document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM Content Loaded');
  
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const testDownloadBtn = document.getElementById('testDownloadBtn');
  const status = document.getElementById('status');
  const progress = document.getElementById('progress');
  const progressText = document.getElementById('progressText');
  const chunkProgress = document.getElementById('chunkProgress');
  const chunksWritten = document.getElementById('chunksWritten');
  const chunksDownloaded = document.getElementById('chunksDownloaded');
  const pagesCrawled = document.getElementById('pagesCrawled');

  
  console.log('DOM elements found:', {
    startBtn: !!startBtn,
    stopBtn: !!stopBtn,
    status: !!status,
    progress: !!progress,
    progressText: !!progressText,
    chunkProgress: !!chunkProgress,
    chunksWritten: !!chunksWritten,
    chunksDownloaded: !!chunksDownloaded,
    pagesCrawled: !!pagesCrawled
  });

  // Check if we're on a Zendesk Help Center
  checkZendeskHelpCenter();
  
  // Check current status on load
  updateStatus();

  function checkZendeskHelpCenter() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      // Add a small delay to ensure content script is ready
      setTimeout(function() {
        chrome.tabs.sendMessage(tabs[0].id, {action: 'checkZendesk'}, function(response) {
          if (chrome.runtime.lastError) {
            console.log('Communication error:', chrome.runtime.lastError);
            // Content script not loaded or not a Zendesk site
            status.textContent = 'Not on a Zendesk Help Center';
            status.className = 'status error';
            startBtn.disabled = true;
            startBtn.textContent = 'Navigate to a Help Center first';
          } else if (response && response.isZendesk) {
            console.log('Zendesk detected:', response);
            status.textContent = 'Ready to crawl Zendesk Help Center';
            status.className = 'status idle';
            startBtn.disabled = false;
          } else {
            console.log('Not a Zendesk site:', response);
            status.textContent = 'Not on a Zendesk Help Center';
            status.className = 'status error';
            startBtn.disabled = true;
            startBtn.textContent = 'Navigate to a Help Center first';
          }
        });
      }, 500); // 500ms delay
    });
  }

  startBtn.addEventListener('click', function() {
    // Check storage usage before starting
    chrome.storage.local.getBytesInUse(null, (bytesInUse) => {
      const maxBytes = 1024 * 1024 * 5; // 5MB limit
      const usedPercent = (bytesInUse / maxBytes) * 100;
      
      if (usedPercent > 80) {
        const shouldContinue = confirm(
          `Storage usage is high (${usedPercent.toFixed(1)}% of 5MB). ` +
          `This may cause the crawler to stop early due to storage limits. ` +
          `Would you like to clear previous data first?`
        );
        
        if (shouldContinue) {
          chrome.storage.local.clear(() => {
            console.log('Storage cleared');
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
              chrome.tabs.sendMessage(tabs[0].id, {action: 'startCrawling'});
              updateStatus('crawling');
            });
          });
        } else {
          // Continue without clearing
          chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: 'startCrawling'});
            updateStatus('crawling');
          });
        }
      } else {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
          chrome.tabs.sendMessage(tabs[0].id, {action: 'startCrawling'});
          updateStatus('crawling');
        });
      }
    });
  });

  stopBtn.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'stopCrawling'});
      updateStatus('idle');
    });
  });

  testDownloadBtn.addEventListener('click', function() {
    console.log('Test download button clicked');
    status.textContent = 'Testing download mechanism...';
    status.className = 'status idle';
    
    // Create a simple test ZIP file
    const zip = new JSZip();
    zip.file('test.txt', 'This is a test file for download mechanism');
    zip.file('test_info.json', JSON.stringify({
      test: true,
      timestamp: new Date().toISOString(),
      message: 'Testing download mechanism'
    }, null, 2));
    
    // Generate ZIP blob
    zip.generateAsync({type: 'blob'}).then(function(zipBlob) {
      console.log('Test ZIP created, size:', zipBlob.size);
      
      // Convert to base64
      const reader = new FileReader();
      reader.onload = function() {
        const base64Data = reader.result.split(',')[1];
        console.log('Test base64 data length:', base64Data.length);
        
        // Send to background script
        chrome.runtime.sendMessage({
          action: 'downloadChunk',
          data: {
            filename: 'test_download_mechanism.zip',
            base64Data: base64Data,
            chunkNumber: 999,
            runId: 'test-run'
          }
        }, function(response) {
          if (chrome.runtime.lastError) {
            console.error('Test download error:', chrome.runtime.lastError);
            status.textContent = `Test failed: ${chrome.runtime.lastError.message}`;
            status.className = 'status error';
          } else if (response && response.success) {
            console.log('Test download started:', response);
            status.textContent = `Test download started! ID: ${response.downloadId}`;
            status.className = 'status crawling';
          } else {
            console.error('Test download failed:', response);
            status.textContent = `Test failed: ${response?.error || 'Unknown error'}`;
            status.className = 'status error';
          }
        });
      };
      
      reader.onerror = function() {
        status.textContent = 'Test failed: Error reading blob data';
        status.className = 'status error';
      };
      
      reader.readAsDataURL(zipBlob);
    }).catch(function(error) {
      console.error('Test ZIP creation error:', error);
      status.textContent = `Test failed: ${error.message}`;
      status.className = 'status error';
    });
  });





















  function updateStatus(newStatus = null) {
    chrome.storage.local.get(['crawlingStatus', 'crawledData', 'dataBuffer', 'bufferSize', 'chunkCounter', 'chunksDownloaded'], function(result) {
      const status = result.crawlingStatus || 'idle';
      const data = result.crawledData || [];
      
      console.log('Popup updateStatus - data length:', data.length, 'status:', status);
      
      // Update status display
      const statusEl = document.getElementById('status');
      statusEl.className = `status ${status}`;
      
      if (status === 'idle') {
        statusEl.textContent = 'Ready to crawl';
        startBtn.style.display = 'block';
        stopBtn.style.display = 'none';
        progress.style.display = 'none';
      } else if (status === 'crawling') {
        statusEl.textContent = 'Crawling in progress...';
        startBtn.style.display = 'none';
        stopBtn.style.display = 'block';
        progress.style.display = 'block';
      } else if (status === 'error') {
        statusEl.textContent = 'Error occurred';
        startBtn.style.display = 'block';
        stopBtn.style.display = 'none';
        progress.style.display = 'none';
      } else if (status === 'quota_exceeded') {
        statusEl.textContent = 'Storage quota exceeded - crawling stopped';
        statusEl.className = 'status error';
        startBtn.style.display = 'block';
        stopBtn.style.display = 'none';
        progress.style.display = 'none';
      }


      
      // Update counters
      updateCounters(result);
      
      if (status === 'crawling') {
        progressText.textContent = `${data.length} pages`;
      }
    });
  }

  // Listen for updates from background script
  chrome.storage.onChanged.addListener(function(changes, namespace) {
    console.log('Storage changed:', changes, namespace);
    if (namespace === 'local' && (changes.crawlingStatus || changes.crawledData || changes.chunksDownloaded || changes.dataBuffer || changes.chunkCounter)) {
      console.log('Triggering updateStatus from storage change');
      updateStatus();
    }
  });

  // Update counters with current data
  function updateCounters(result) {
    const data = result.crawledData || [];
    const buffer = result.dataBuffer || [];
    const bufferSize = result.bufferSize || 0;
    const chunkCounter = result.chunkCounter || 0;
    
    // Calculate chunk progress percentage
    const maxBufferSize = 1024 * 1024; // 1MB
    const progressPercent = Math.min(Math.round((bufferSize / maxBufferSize) * 100), 100);
    chunkProgress.textContent = `${progressPercent}%`;
    
    // Update chunks written
    chunksWritten.textContent = chunkCounter;
    
    // Update pages crawled (stored + buffer)
    const totalPages = data.length + buffer.length;
    pagesCrawled.textContent = totalPages;
    
    // Update chunks downloaded from storage
    const downloaded = result.chunksDownloaded || 0;
    chunksDownloaded.textContent = downloaded;
    
    // Debug logging
    console.log('Counter update:', {
      dataLength: data.length,
      bufferLength: buffer.length,
      bufferSize: bufferSize,
      chunkCounter: chunkCounter,
      progressPercent: progressPercent,
      totalPages: totalPages
    });
  }

  // Download completion is now handled in background script
  // The popup will update via storage change events

  // Update status every second while crawling
  setInterval(updateStatus, 1000);
}); 