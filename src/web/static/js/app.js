// DOCU-GEN Web Application JavaScript - Mobile First
const form = document.getElementById('generateForm');
const statusDiv = document.getElementById('status');
const progressDiv = document.getElementById('progress');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const resultsDiv = document.getElementById('results');
const resultsContainer = document.getElementById('resultsContainer');
const generateBtn = document.getElementById('generateBtn');
const previewModal = document.getElementById('previewModal');
const previewContent = document.getElementById('previewContent');
const closePreviewBtn = document.getElementById('closePreview');
const wsStatus = document.getElementById('wsStatus');
const wsIndicator = document.getElementById('wsIndicator');
const wsStatusText = document.getElementById('wsStatusText');
const errorDetails = document.getElementById('errorDetails');
const errorDetailsContent = document.getElementById('errorDetailsContent');
const errorDetailsText = document.getElementById('errorDetailsText');
const errorDetailsToggle = document.getElementById('errorDetailsToggle');
const downloadAllBtn = document.getElementById('downloadAllBtn');

let projectId = null;
let websocket = null;
let reconnectAttempts = 0;
let pollInterval = null;
let wsConnected = false;
let isPolling = false;
const maxReconnectAttempts = 5;
let allDocuments = []; // Store all documents for download all

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userIdea = document.getElementById('userIdea').value.trim();
    const profile = document.querySelector('input[name="profile"]:checked').value;
    
    if (!userIdea) {
        showStatus('Please enter a project idea', 'error');
        return;
    }
    
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    generateBtn.classList.add('loading');
    showStatus('Starting documentation generation...', 'info');
    hideErrorDetails();
    progressDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
    downloadAllBtn.classList.add('hidden');
    progressBar.style.width = '0%';
    progressText.textContent = '0%';
    allDocuments = []; // Clear previous documents
    
    // Scroll to progress
    progressDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_idea: userIdea, profile: profile, phase1_only: true})
            // body: JSON.stringify({user_idea: userIdea, profile: profile})

        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        projectId = data.project_id;
        connectWebSocket(projectId);
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
        showErrorDetails('Generation start failed', error.message);
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Documentation';
        generateBtn.classList.remove('loading');
        progressDiv.classList.add('hidden');
        updateWebSocketStatus(false, false);
    }
});

// Update WebSocket status indicator
function updateWebSocketStatus(connected, polling = false) {
    wsConnected = connected;
    isPolling = polling;
    wsStatus.classList.remove('hidden');
    
    if (connected && !polling) {
        wsIndicator.className = 'w-2 h-2 rounded-full bg-green-500 animate-pulse';
        wsStatusText.textContent = 'Connected (WebSocket)';
        wsStatusText.className = 'text-xs text-green-600';
    } else if (polling) {
        wsIndicator.className = 'w-2 h-2 rounded-full bg-yellow-500';
        wsStatusText.textContent = 'Polling (Fallback)';
        wsStatusText.className = 'text-xs text-yellow-600';
    } else {
        wsIndicator.className = 'w-2 h-2 rounded-full bg-gray-400';
        wsStatusText.textContent = 'Disconnected';
        wsStatusText.className = 'text-xs text-gray-500';
    }
}

// WebSocket connection
function connectWebSocket(projectId) {
    if (websocket) websocket.close();
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    websocket = new WebSocket(`${protocol}//${window.location.host}/ws/${projectId}`);
    reconnectAttempts = 0;
    updateWebSocketStatus(false, false);
    
    websocket.onopen = () => {
        updateWebSocketStatus(true, false);
        showStatus('Connected. Generating documentation...', 'info');
    };
    websocket.onmessage = (event) => {
        try {
            handleWebSocketMessage(JSON.parse(event.data));
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    };
    websocket.onerror = () => {
        updateWebSocketStatus(false, false);
        showStatus('Connection error. Using fallback...', 'error');
        fallbackToPolling(projectId);
    };
    websocket.onclose = () => {
        updateWebSocketStatus(false, false);
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            setTimeout(() => connectWebSocket(projectId), 1000 * reconnectAttempts);
        } else {
            fallbackToPolling(projectId);
        }
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'start':
            updateProgress(5);
            showStatus('Generation started...', 'info');
            break;
        case 'phase':
            if (message.phase === 'phase_1') {
                updateProgress(25);
                showStatus('Phase 1: Foundational documents...', 'info');
            } else if (message.phase === 'phase_2') {
                updateProgress(60);
                showStatus('Phase 2: Parallel generation...', 'info');
            } else if (message.phase === 'phase_3') {
                updateProgress(85);
                showStatus('Phase 3: Finalization...', 'info');
            }
            break;
        case 'progress':
            updateProgress(message.progress || 0);
            if (message.message) {
                showStatus(message.message, 'info');
            }
            break;
        case 'complete':
            updateProgress(100);
            showStatus('Documentation generated successfully!', 'success');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Documentation';
            generateBtn.classList.remove('loading');
            progressDiv.classList.add('hidden');
            if (websocket) {
                websocket.close();
                websocket = null;
            }
            fetchResults();
            // Scroll to results
            setTimeout(() => {
                resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 300);
            break;
        case 'error':
            const errorMsg = message.message || 'Unknown error';
            showStatus('Error: ' + errorMsg, 'error');
            showErrorDetails(errorMsg, message.error || message.details || null);
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Documentation';
            generateBtn.classList.remove('loading');
            progressDiv.classList.add('hidden');
            if (websocket) {
                websocket.close();
                websocket = null;
            }
            updateWebSocketStatus(false, false);
            break;
    }
}

// Update progress bar
function updateProgress(percent) {
    progressBar.style.width = percent + '%';
    progressText.textContent = Math.round(percent) + '%';
}

// Show status message
function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = `mb-4 px-4 py-3 rounded-lg text-sm ${
        type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
        type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' :
        'bg-blue-50 text-blue-700 border border-blue-200'
    }`;
    statusDiv.classList.remove('hidden');
}

// Show error details
function showErrorDetails(message, details) {
    if (message || details) {
        errorDetails.classList.remove('hidden');
        let errorText = message || 'Unknown error';
        if (details) {
            if (typeof details === 'string') {
                errorText += '\n\nDetails: ' + details;
            } else {
                errorText += '\n\nDetails: ' + JSON.stringify(details, null, 2);
            }
        }
        errorDetailsText.textContent = errorText;
    } else {
        errorDetails.classList.add('hidden');
    }
}

// Toggle error details
function toggleErrorDetails() {
    const isHidden = errorDetailsContent.classList.contains('hidden');
    if (isHidden) {
        errorDetailsContent.classList.remove('hidden');
        errorDetailsToggle.textContent = '▲';
    } else {
        errorDetailsContent.classList.add('hidden');
        errorDetailsToggle.textContent = '▼';
    }
}
window.toggleErrorDetails = toggleErrorDetails; // Make it global

// Hide error details
function hideErrorDetails() {
    errorDetails.classList.add('hidden');
    errorDetailsContent.classList.add('hidden');
    errorDetailsToggle.textContent = '▼';
}

// Fallback to polling
function fallbackToPolling(projectId) {
    updateWebSocketStatus(false, true);
    showStatus('WebSocket unavailable. Using automatic refresh...', 'info');
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(() => checkStatus(projectId), 2000);
    checkStatus(projectId);
}

// Check status (polling fallback)
async function checkStatus(projectId) {
    if (!projectId) return;
    try {
        const response = await fetch(`/api/status/${projectId}`);
        const data = await response.json();
        const completed = data.completed_agents?.length || 0;
        const total = 15;
        const percent = Math.round((completed / total) * 100);
        updateProgress(percent);
        if (data.status === 'complete') {
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
            showStatus('Documentation generated successfully!', 'success');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Documentation';
            generateBtn.classList.remove('loading');
            progressDiv.classList.add('hidden');
            await fetchResults();
            setTimeout(() => {
                resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 300);
        } else if (data.status === 'failed') {
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
            const errorMsg = data.error || 'Generation failed. Please try again.';
            showStatus('Generation failed: ' + errorMsg, 'error');
            showErrorDetails(errorMsg, data.error_details || null);
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Documentation';
            generateBtn.classList.remove('loading');
            progressDiv.classList.add('hidden');
            updateWebSocketStatus(false, false);
        }
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

// Fetch and display results
async function fetchResults() {
    try {
        const response = await fetch(`/api/results/${projectId}`);
        const data = await response.json();
        
        resultsContainer.innerHTML = '';
        const documentsByLevel = data.documents_by_level || {};
        
        // Collect all documents for download all
        allDocuments = [];
        
        const levels = [
            { key: 'level_1_strategic', title: 'Strategic Documents', icon: '🎯', color: 'red' },
            { key: 'level_2_product', title: 'Product Documents', icon: '📊', color: 'blue' },
            { key: 'level_3_technical', title: 'Technical Documents', icon: '💻', color: 'green' },
            { key: 'cross_level', title: 'Cross-Level Documents', icon: '🌐', color: 'gray' }
        ];
        
        levels.forEach(level => {
            const levelData = documentsByLevel[level.key];
            if (levelData && levelData.documents && levelData.documents.length > 0) {
                const section = createLevelSection(level, levelData);
                resultsContainer.appendChild(section);
                // Collect documents for download all
                levelData.documents.forEach(doc => {
                    allDocuments.push({
                        type: doc.type,
                        display_name: doc.display_name,
                        file_path: doc.file_path
                    });
                });
            }
        });
        
        if (resultsContainer.children.length === 0) {
            resultsContainer.innerHTML = '<p class="text-gray-500 text-center py-8">No documents found</p>';
            downloadAllBtn.classList.add('hidden');
        } else {
            // Show download all button if documents are available
            downloadAllBtn.classList.remove('hidden');
        }
        
        // Hide error details on success
        hideErrorDetails();
        
        resultsDiv.classList.remove('hidden');
    } catch (error) {
        console.error('Error fetching results:', error);
        showStatus('Error loading results: ' + error.message, 'error');
        showErrorDetails('Error loading results', error.message);
    }
}

// Create level section
function createLevelSection(level, levelData) {
    const section = document.createElement('div');
    section.className = 'border border-gray-200 rounded-lg p-4';
    
    const title = document.createElement('h3');
    title.className = 'text-base font-semibold text-gray-900 mb-3 flex items-center gap-2';
    title.innerHTML = `<span>${level.icon}</span> <span>${level.title}</span>`;
    section.appendChild(title);
    
    const list = document.createElement('div');
    list.className = 'space-y-2';
    
    levelData.documents.forEach((doc, index) => {
        const item = document.createElement('div');
        item.className = 'doc-item flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 border border-gray-200 rounded-lg bg-gray-50 hover:bg-white hover:shadow-sm transition-all';
        
        const name = document.createElement('div');
        name.className = 'flex-1 min-w-0';
        const nameText = document.createElement('span');
        nameText.className = 'text-sm font-medium text-gray-900 block truncate';
        nameText.textContent = doc.display_name;
        name.appendChild(nameText);
        if (doc.file_size_human) {
            const size = document.createElement('span');
            size.className = 'text-xs text-gray-500 mt-1 block';
            size.textContent = doc.file_size_human;
            name.appendChild(size);
        }
        item.appendChild(name);
        
        const actions = document.createElement('div');
        actions.className = 'flex gap-2 shrink-0';
        
        const previewBtn = document.createElement('button');
        previewBtn.className = 'px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 hover:border-blue-300 transition-colors';
        previewBtn.textContent = 'Preview';
        previewBtn.onclick = () => previewDocument(doc);
        actions.appendChild(previewBtn);
        
        const downloadBtn = document.createElement('a');
        downloadBtn.href = `/api/download/${projectId}/${doc.type}`;
        downloadBtn.className = 'px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center justify-center';
        downloadBtn.textContent = 'Download';
        downloadBtn.download = doc.display_name;
        actions.appendChild(downloadBtn);
        
        item.appendChild(actions);
        list.appendChild(item);
    });
    
    section.appendChild(list);
    return section;
}

// Preview document
async function previewDocument(doc) {
    try {
        previewModal.classList.remove('hidden');
        previewContent.innerHTML = '<div class="text-center py-8"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div><p class="mt-4 text-gray-500">Loading preview...</p></div>';
        
        const response = await fetch(`/api/preview/${projectId}/${doc.type}`);
        if (!response.ok) throw new Error('Failed to fetch');
        const text = await response.text();
        
        if (typeof marked !== 'undefined') {
            previewContent.innerHTML = marked.parse(text);
        } else {
            previewContent.textContent = text;
        }
    } catch (error) {
        console.error('Error previewing:', error);
        previewContent.innerHTML = `<div class="text-center py-8 text-red-600"><p>Error loading preview: ${error.message}</p></div>`;
    }
}

// Close preview modal
closePreviewBtn.addEventListener('click', () => {
    previewModal.classList.add('hidden');
});

// Close modal on background click
previewModal.addEventListener('click', (e) => {
    if (e.target === previewModal) {
        previewModal.classList.add('hidden');
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !previewModal.classList.contains('hidden')) {
        previewModal.classList.add('hidden');
    }
});

// Download all documents as ZIP
async function downloadAllDocuments() {
    if (!projectId || allDocuments.length === 0) {
        showStatus('No documents available for download', 'error');
        return;
    }
    
    try {
        downloadAllBtn.disabled = true;
        downloadAllBtn.textContent = '📦 Downloading...';
        
        // Call API to generate ZIP
        const response = await fetch(`/api/download-all/${projectId}`, {
            method: 'GET'
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate ZIP file');
        }
        
        // Get blob and create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `docu-gen-${projectId}-${new Date().toISOString().split('T')[0]}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showStatus('All documents downloaded successfully!', 'success');
    } catch (error) {
        console.error('Error downloading all documents:', error);
        showStatus('Error downloading all documents: ' + error.message, 'error');
        showErrorDetails('Download error', error.message);
    } finally {
        downloadAllBtn.disabled = false;
        downloadAllBtn.textContent = '📦 Download All';
    }
}
window.downloadAllDocuments = downloadAllDocuments; // Make it global

