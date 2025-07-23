document.addEventListener('DOMContentLoaded', function() {
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const exportBtn = document.getElementById('exportBtn');
  const testBtn = document.getElementById('testBtn');
  const status = document.getElementById('status');
  const progress = document.getElementById('progress');
  const progressText = document.getElementById('progressText');
  const pagesCrawled = document.getElementById('pagesCrawled');
  const linksFound = document.getElementById('linksFound');
  const contentSize = document.getElementById('contentSize');

  console.log('Debug: DOM elements found:', {
    startBtn: !!startBtn,
    stopBtn: !!stopBtn,
    exportBtn: !!exportBtn,
    status: !!status,
    progress: !!progress,
    progressText: !!progressText,
    pagesCrawled: !!pagesCrawled,
    linksFound: !!linksFound,
    contentSize: !!contentSize
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
    console.log('Debug: Start button clicked');
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'startCrawling'});
      updateStatus('crawling');
    });
  });

  stopBtn.addEventListener('click', function() {
    console.log('Debug: Stop button clicked');
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'stopCrawling'});
      updateStatus('idle');
    });
  });

  exportBtn.addEventListener('click', function() {
    console.log('Debug: Export button clicked');
    chrome.storage.local.get(['crawledData'], function(result) {
      console.log('Debug: Export data:', result);
      if (result.crawledData && result.crawledData.length > 0) {
        // Export as JSON
        const dataStr = JSON.stringify(result.crawledData, null, 2);
        const blob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        chrome.downloads.download({
          url: url,
          filename: 'zendesk_crawled_data.json',
          saveAs: true
        });
        
        // Also export as markdown files
        exportAsMarkdown(result.crawledData);
      } else {
        alert('No data to export. Start crawling first.');
      }
    });
  });

  function exportAsMarkdown(data) {
    // Export each page as a separate markdown file
    data.forEach((page, index) => {
      const filename = `zendesk_page_${index + 1}.md`;
      const blob = new Blob([page.content], {type: 'text/markdown'});
      const url = URL.createObjectURL(blob);
      
      chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: false
      });
    });
  }

  testBtn.addEventListener('click', function() {
    console.log('Debug: Test button clicked');
    // Test counter updates manually
    chrome.storage.local.get(['crawledData'], function(result) {
      console.log('Debug: Current storage data:', result);
      
      // Simulate some test data
      const testData = [
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
        }
      ];
      
      chrome.storage.local.set({crawledData: testData}, function() {
        console.log('Debug: Test data saved to storage');
        updateStatus();
      });
    });
  });

  function updateStatus(newStatus = null) {
    console.log('Debug: updateStatus called with newStatus:', newStatus);
    chrome.storage.local.get(['crawlingStatus', 'crawledData', 'crawlingProgress'], function(result) {
      console.log('Debug: Storage data retrieved:', result);
      
      const status = result.crawlingStatus || 'idle';
      const data = result.crawledData || [];
      const progress = result.crawlingProgress;
      
      console.log('Debug: Parsed data:', {
        status: status,
        dataLength: data.length,
        progress: progress
      });
      
      // Update status display
      const statusEl = document.getElementById('status');
      statusEl.className = `status ${status}`;
      
      if (status === 'idle') {
        statusEl.textContent = 'Ready to crawl';
        startBtn.style.display = 'block';
        stopBtn.style.display = 'none';
        progress.style.display = 'none';
      } else if (status === 'crawling') {
        // Show current URL if available
        const currentUrl = progress && progress.currentUrl ? 
          progress.currentUrl.split('/').pop() || progress.currentUrl.split('/').slice(-2).join('/') : 
          'in progress...';
        statusEl.textContent = `Crawling ${currentUrl}`;
        startBtn.style.display = 'none';
        stopBtn.style.display = 'block';
        progress.style.display = 'block';
      } else if (status === 'error') {
        statusEl.textContent = 'Error occurred';
        startBtn.style.display = 'block';
        stopBtn.style.display = 'none';
        progress.style.display = 'none';
      }

      // Update stats with debug logging
      console.log('Debug: Updating counters...');
      console.log('Debug: pagesCrawled element:', pagesCrawled);
      console.log('Debug: data.length:', data.length);
      
      pagesCrawled.textContent = data.length;
      
      const totalLinks = data.reduce((sum, page) => sum + (page.links ? page.links.length : 0), 0);
      console.log('Debug: totalLinks:', totalLinks);
      linksFound.textContent = totalLinks;
      
      const totalSize = data.reduce((sum, page) => sum + (page.content ? page.content.length : 0), 0);
      console.log('Debug: totalSize:', totalSize);
      contentSize.textContent = `${Math.round(totalSize / 1024)} KB (${totalSize} bytes)`;
      
      if (status === 'crawling') {
        progressText.textContent = `${data.length} pages`;
      }
      
      console.log('Debug: Counters updated:', {
        pagesCrawled: pagesCrawled.textContent,
        linksFound: linksFound.textContent,
        contentSize: contentSize.textContent
      });
    });
  }

  // Listen for updates from background script
  chrome.storage.onChanged.addListener(function(changes, namespace) {
    console.log('Debug: Storage changed:', changes, namespace);
    if (namespace === 'local' && (changes.crawlingStatus || changes.crawledData || changes.crawlingProgress)) {
      console.log('Debug: Relevant storage change detected, updating status');
      updateStatus();
    }
  });

  // Update status every second while crawling
  setInterval(updateStatus, 1000);
}); 