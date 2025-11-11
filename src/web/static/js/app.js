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

let projectId = null;
let websocket = null;
let reconnectAttempts = 0;
let pollInterval = null;
const maxReconnectAttempts = 5;

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
    progressDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
    progressBar.style.width = '0%';
    progressText.textContent = '0%';
    
    // Scroll to progress
    progressDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_idea: userIdea, profile: profile})
        });
        const data = await response.json();
        projectId = data.project_id;
        connectWebSocket(projectId);
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Documentation';
        generateBtn.classList.remove('loading');
        progressDiv.classList.add('hidden');
    }
});

// WebSocket connection
function connectWebSocket(projectId) {
    if (websocket) websocket.close();
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    websocket = new WebSocket(`${protocol}//${window.location.host}/ws/${projectId}`);
    reconnectAttempts = 0;
    
    websocket.onopen = () => {
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
        showStatus('Connection error. Using fallback...', 'error');
        fallbackToPolling(projectId);
    };
    websocket.onclose = () => {
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
            showStatus('Error: ' + (message.message || 'Unknown error'), 'error');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Documentation';
            generateBtn.classList.remove('loading');
            progressDiv.classList.add('hidden');
            if (websocket) {
                websocket.close();
                websocket = null;
            }
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

// Fallback to polling
function fallbackToPolling(projectId) {
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
            showStatus('Generation failed. Please try again.', 'error');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Documentation';
            generateBtn.classList.remove('loading');
            progressDiv.classList.add('hidden');
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
            }
        });
        
        if (resultsContainer.children.length === 0) {
            resultsContainer.innerHTML = '<p class="text-gray-500 text-center py-8">No documents found</p>';
        }
        
        resultsDiv.classList.remove('hidden');
    } catch (error) {
        console.error('Error fetching results:', error);
        showStatus('Error loading results: ' + error.message, 'error');
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

