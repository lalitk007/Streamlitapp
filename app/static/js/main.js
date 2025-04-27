// app/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Handle crawl form submission
    const crawlForm = document.getElementById('crawl-form');
    const crawlStatus = document.getElementById('crawl-status');

    if (crawlForm) {
        crawlForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const url = document.getElementById('crawl-url').value;
            const maxPages = document.getElementById('max-pages').value;
            const maxDepth = document.getElementById('max-depth').value;

            if (!url) {
                showCrawlStatus('Please enter a valid URL', 'error');
                return;
            }

            // Show loading status
            showCrawlStatus('Crawling and indexing website... This may take a while.', 'loading');

            try {
                const response = await fetch('/api/crawl', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        url: url,
                        max_pages: parseInt(maxPages),
                        max_depth: parseInt(maxDepth)
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showCrawlStatus(`Success! Crawled and indexed ${data.pages.length} pages.`, 'success');

                    // Refresh stats after a short delay
                    setTimeout(refreshStats, 1000);
                } else {
                    showCrawlStatus(`Error: ${data.detail
                    // app/static/js/main.js (continued)
                } else {
                    showCrawlStatus(`Error: ${data.detail || 'Failed to crawl website'}`, 'error');
                }
            } catch (error) {
                showCrawlStatus(`Error: ${error.message || 'Failed to crawl website'}`, 'error');
            }
        });
    }

    function showCrawlStatus(message, type) {
        if (crawlStatus) {
            crawlStatus.textContent = message;
            crawlStatus.className = 'crawl-status ' + type;
        }
    }

    async function refreshStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            // Update stats on the page
            const documentCountElement = document.querySelector('.stat-value');
            if (documentCountElement) {
                documentCountElement.textContent = data.document_count;
            }
        } catch (error) {
            console.error('Failed to refresh stats:', error);
        }
    }

    // Add clear index functionality
    const clearIndexButton = document.getElementById('clear-index');
    if (clearIndexButton) {
        clearIndexButton.addEventListener('click', async function() {
            if (confirm('Are you sure you want to clear the search index? This action cannot be undone.')) {
                try {
                    const response = await fetch('/api/clear', {
                        method: 'DELETE'
                    });

                    const data = await response.json();

                    if (response.ok) {
                        alert('Search index cleared successfully');
                        refreshStats();
                    } else {
                        alert(`Error: ${data.detail || 'Failed to clear index'}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message || 'Failed to clear index'}`);
                }
            }
        });
    }
});