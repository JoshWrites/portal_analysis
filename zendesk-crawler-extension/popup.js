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
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'startCrawling'});
      updateStatus('crawling');
    });
  });

  stopBtn.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'stopCrawling'});
      updateStatus('idle');
    });
  });

  exportBtn.addEventListener('click', function() {
    chrome.storage.local.get(['crawledData'], function(result) {
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
    // Create a zip file with markdown content
    const zip = new JSZip();
    
    data.forEach((page, index) => {
      const filename = `page_${index + 1}.md`;
      zip.file(filename, page.content);
    });
    
    zip.generateAsync({type: 'blob'}).then(function(content) {
      const url = URL.createObjectURL(content);
      chrome.downloads.download({
        url: url,
        filename: 'zendesk_content_markdown.zip',
        saveAs: true
      });
    });
  }

  testBtn.addEventListener('click', function() {
    console.log('Testing communication...');
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      console.log('Current tab:', tabs[0].url);
      console.log('Tab ID:', tabs[0].id);
      
      // Try direct script injection with a simple test
      chrome.scripting.executeScript({
        target: {tabId: tabs[0].id},
        func: function() {
          console.log('Direct script injection test');
          return {
            url: window.location.href,
            isZendesk: window.location.href.includes('/hc/'),
            readyState: document.readyState
          };
        }
      }, function(results) {
        console.log('Direct injection results:', results);
        if (results && results[0] && results[0].result) {
          const result = results[0].result;
          console.log('Page info:', result);
          if (result.isZendesk) {
            alert('✅ Zendesk detected via direct injection!');
          } else {
            alert('❌ Not a Zendesk site via direct injection.');
          }
        } else {
          alert('❌ Direct injection failed.');
        }
      });
    });
  });

  function updateStatus(newStatus = null) {
    chrome.storage.local.get(['crawlingStatus', 'crawledData'], function(result) {
      const status = result.crawlingStatus || 'idle';
      const data = result.crawledData || [];
      
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
      }

      // Update stats
      pagesCrawled.textContent = data.length;
      const totalLinks = data.reduce((sum, page) => sum + (page.links ? page.links.length : 0), 0);
      linksFound.textContent = totalLinks;
      
      const totalSize = data.reduce((sum, page) => sum + (page.content ? page.content.length : 0), 0);
      contentSize.textContent = `${Math.round(totalSize / 1024)} KB`;
      
      if (status === 'crawling') {
        progressText.textContent = `${data.length} pages`;
      }
    });
  }

  // Listen for updates from background script
  chrome.storage.onChanged.addListener(function(changes, namespace) {
    if (namespace === 'local' && (changes.crawlingStatus || changes.crawledData)) {
      updateStatus();
    }
  });

  // Update status every second while crawling
  setInterval(updateStatus, 1000);
}); 