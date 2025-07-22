document.addEventListener('DOMContentLoaded', function() {
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const exportBtn = document.getElementById('exportBtn');
  const status = document.getElementById('status');
  const progress = document.getElementById('progress');
  const progressText = document.getElementById('progressText');
  const pagesCrawled = document.getElementById('pagesCrawled');
  const linksFound = document.getElementById('linksFound');
  const contentSize = document.getElementById('contentSize');

  // Check current status on load
  updateStatus();

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
        const dataStr = JSON.stringify(result.crawledData, null, 2);
        const blob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        chrome.downloads.download({
          url: url,
          filename: 'zendesk_crawled_data.json',
          saveAs: true
        });
      } else {
        alert('No data to export. Start crawling first.');
      }
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