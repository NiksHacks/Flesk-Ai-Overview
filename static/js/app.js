// ===== GLOBAL VARIABLES =====
let currentAiOverview = null;
let chatHistory = [];
let savedFiles = [];
let selectedFileId = null;
let sessionStats = {
    extractions: 0,
    analyses: 0,
    successRate: 0
};

// ===== DOM ELEMENTS =====
const elements = {
    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),
    
    // Navigation
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    
    // AI Overview
    queryInput: document.getElementById('queryInput'),
    extractBtn: document.getElementById('extractBtn'),
    clearOverviewBtn: document.getElementById('clearOverviewBtn'),
    aiOverviewResults: document.getElementById('aiOverviewResults'),
    
    // Content Gap
    fileUploadArea: document.getElementById('fileUploadArea'),
    jsonFileInput: document.getElementById('jsonFileInput'),
    chatHistory: document.getElementById('chatHistory'),
    chatInput: document.getElementById('chatInput'),
    sendChatBtn: document.getElementById('sendChatBtn'),
    exportChatBtn: document.getElementById('exportChatBtn'),
    clearChatBtn: document.getElementById('clearChatBtn'),
    
    // File Manager
    fileManagerUpload: document.getElementById('fileManagerUpload'),
    fileManagerInput: document.getElementById('fileManagerInput'),

    savedFilesList: document.getElementById('savedFilesList'),
    emptyFilesState: document.getElementById('emptyFilesState'),
    

    
    // Footer
    footerExtractions: document.getElementById('footerExtractions'),
    footerAnalyses: document.getElementById('footerAnalyses'),
    
    // Notifications
    notificationContainer: document.getElementById('notificationContainer')
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadSessionData();
    loadSavedFilesFromStorage(); // Load saved files library

});

function initializeApp() {
    // Add loading animation to page elements
    animatePageLoad();
    
    // Initialize tooltips and interactive elements
    initializeInteractiveElements();
    
    // Load saved data from localStorage
    loadSavedData();
    
    console.log('🚀 Ai Analyzer inizializzato con successo!');
}

function animatePageLoad() {
    // Animate cards on load
    const cards = document.querySelectorAll('.cyber-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initializeInteractiveElements() {
    // Add simple hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Add ripple effect to buttons
    buttons.forEach(btn => {
        btn.addEventListener('click', createRippleEffect);
    });
    
    // Removed heavy effects for better performance
}

// Removed heavy animation functions for better performance

function createRippleEffect(e) {
    const button = e.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Navigation tabs
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // AI Overview
    elements.extractBtn.addEventListener('click', extractAiOverview);
    elements.clearOverviewBtn.addEventListener('click', clearAiOverview);
    elements.queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') extractAiOverview();
    });
    
    // Content Gap
    elements.fileUploadArea.addEventListener('click', () => elements.jsonFileInput.click());
    elements.fileUploadArea.addEventListener('dragover', handleDragOver);
    elements.fileUploadArea.addEventListener('drop', handleFileDrop);
    elements.jsonFileInput.addEventListener('change', handleFileSelect);
    
    elements.sendChatBtn.addEventListener('click', sendChatMessage);
    elements.exportChatBtn.addEventListener('click', exportChatHistory);
    elements.clearChatBtn.addEventListener('click', clearChatHistory);
    elements.chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
    
    // File Manager
    elements.fileManagerUpload.addEventListener('click', () => elements.fileManagerInput.click());
    elements.fileManagerInput.addEventListener('change', handleFileManagerUpload);
    

}

// ===== TAB NAVIGATION =====
function switchTab(tabId) {
    // Update tab buttons
    elements.tabBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabId) {
            btn.classList.add('active');
        }
    });
    
    // Update tab panes
    elements.tabPanes.forEach(pane => {
        pane.classList.remove('active');
        if (pane.id === tabId) {
            pane.classList.add('active');
        }
    });
    
    // Trigger animations
    const activePane = document.getElementById(tabId);
    if (activePane) {
        activePane.style.animation = 'none';
        setTimeout(() => {
            activePane.style.animation = 'fadeInUp 0.5s ease';
        }, 10);
    }
    

}

// ===== AI OVERVIEW EXTRACTION =====
async function extractAiOverview() {
    const query = elements.queryInput.value.trim();
    
    if (!query) {
        showNotification('Inserisci una query di ricerca', 'warning');
        return;
    }
    
    showLoading(true);
    elements.extractBtn.disabled = true;
    elements.extractBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Estrazione in corso...';
    
    try {
        const response = await fetch('/extract_ai_overview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentAiOverview = data.data;
            
            // Save to library automatically
            const fileId = saveFileToLibrary(data.data);
            
            displayAiOverviewResults(data.data);
            sessionStats.extractions++;
            updateSessionStats();
            showNotification('AI Overview estratto e salvato nella libreria!', 'success');
        } else {
            showNotification(data.error || 'Errore durante l\'estrazione', 'error');
        }
    } catch (error) {
        console.error('Errore:', error);
        showNotification('Errore di connessione', 'error');
    } finally {
        showLoading(false);
        elements.extractBtn.disabled = false;
        elements.extractBtn.innerHTML = '<i class="fas fa-rocket"></i> ESTRAI AI OVERVIEW';
    }
}

function displayAiOverviewResults(data) {
    const resultsHtml = `
        <div class="cyber-card result-card bounce-in">
            <h3 class="result-title">
                <i class="fas fa-check-circle"></i>
                AI Overview Estratto
            </h3>
            <div class="result-content">
                <p><strong>Query:</strong> ${data.query}</p>
                <p><strong>Contenuto:</strong></p>
                <div class="ai-overview-content">
                    ${data.ai_overview || data.content || 'Nessun contenuto AI Overview trovato per questa query.'}
                </div>
                <p><strong>Timestamp:</strong> ${new Date(data.extraction_time || data.timestamp).toLocaleString('it-IT')}</p>
            </div>
            
            <div class="button-group mt-20">
                <button class="btn btn-primary" onclick="sendToContentGap()">
                    <i class="fas fa-arrow-right"></i>
                    Invia a Content Gap
                </button>

            </div>
        </div>
    `;
    
    elements.aiOverviewResults.innerHTML = resultsHtml;
    elements.aiOverviewResults.style.display = 'block';
    elements.clearOverviewBtn.style.display = 'inline-flex';
    
    // Animate the results
    setTimeout(() => {
        elements.aiOverviewResults.scrollIntoView({ behavior: 'smooth' });
    }, 300);
}

function clearAiOverview() {
    currentAiOverview = null;
    elements.aiOverviewResults.style.display = 'none';
    elements.clearOverviewBtn.style.display = 'none';
    elements.queryInput.value = '';
    showNotification('AI Overview cancellato', 'success');
}

// ===== SEND TO CONTENT GAP =====
function sendToContentGap() {
    if (!currentAiOverview) {
        showNotification('Nessun AI Overview da inviare', 'warning');
        return;
    }
    
    // Enable chat interface
    elements.chatInput.disabled = false;
    elements.sendChatBtn.disabled = false;
    
    // Switch to content gap tab
    switchTab('content-gap');
    
    // Add welcome message with AI Overview info
    const wordCount = (currentAiOverview.ai_overview || currentAiOverview.content || '').split(' ').length;
    const welcomeMessage = `AI Overview caricato automaticamente! Contiene ${wordCount} parole estratte dalla query "${currentAiOverview.query}". Ora puoi farmi domande per analizzare il content gap.`;
    
    // Clear existing chat and add welcome message
    elements.chatHistory.innerHTML = '';
    chatHistory = [];
    addChatMessage('assistant', welcomeMessage);
    
    showNotification('AI Overview inviato al Content Gap!', 'success');
}

// ===== FILE HANDLING =====
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#00d4ff';
    e.currentTarget.style.background = 'rgba(0, 212, 255, 0.1)';
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'rgba(0, 212, 255, 0.3)';
    e.currentTarget.style.background = 'rgba(0, 212, 255, 0.05)';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file, fromFileManager = false) {
    if (file.type !== 'application/json') {
        showNotification('Seleziona un file JSON valido', 'warning');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = JSON.parse(e.target.result);
            currentAiOverview = data;
            
            // Salva il file nella libreria se viene dal file manager
            if (fromFileManager) {
                const fileId = saveFileToLibrary(data, file.name);
                showNotification(`File "${file.name}" salvato nella libreria!`, 'success');
            } else {
                // Enable chat interface per content gap e salva anche nella libreria
                const fileId = saveFileToLibrary(data, file.name);
                elements.chatInput.disabled = false;
                elements.sendChatBtn.disabled = false;
                
                // Add welcome message
                const welcomeMessage = `File "${file.name}" caricato con successo! Contiene ${(data.ai_overview || data.content || '').split(' ').length} parole. Ora puoi farmi domande per analizzare il gap di contenuto.`;
                addChatMessage('assistant', welcomeMessage);
                
                showNotification('File JSON caricato e salvato nella libreria!', 'success');
            }
            
        } catch (error) {
            showNotification('Errore nel parsing del file JSON', 'error');
        }
    };
    reader.readAsText(file);
}

function handleFileManagerUpload(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/json') {
        handleFile(file, true); // true indica che viene dal file manager
        // Non switchare automaticamente al content-gap
    }
}

// ===== CHAT FUNCTIONALITY =====
async function sendChatMessage() {
    const message = elements.chatInput.value.trim();
    
    if (!message) {
        showNotification('Inserisci un messaggio', 'warning');
        return;
    }
    
    if (!currentAiOverview) {
        showNotification('Carica prima un file AI Overview JSON', 'warning');
        return;
    }
    
    // Add user message
    addChatMessage('user', message);
    elements.chatInput.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        const response = await fetch('/chat_analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: message,
                ai_overview_data: currentAiOverview
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (data.success) {
            // Gestisci risposta che può contenere testo + dati visivi
            if (typeof data.response === 'object') {
                addChatMessage('assistant', data.response);
            } else {
                addChatMessage('assistant', data.response);
            }
            sessionStats.analyses++;
            updateSessionStats();
        } else {
            addChatMessage('assistant', 'Errore nell\'analisi: ' + (data.error || 'Errore sconosciuto'));
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addChatMessage('assistant', 'Errore di connessione. Riprova più tardi.');
        console.error('Errore chat:', error);
    }
}

function addChatMessage(sender, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender === 'user' ? 'user-message' : 'ai-message'}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Gestisci messaggi con contenuto visuale (grafici/tabelle)
    if (typeof content === 'object' && sender === 'assistant') {
        if (content.text) {
            messageContent.innerHTML = formatMessageContent(content.text);
        }
        
        // Aggiungi grafico se presente
        if (content.chart) {
            const chartContainer = document.createElement('div');
            chartContainer.innerHTML = renderVisualContent(content);
            messageContent.appendChild(chartContainer);
        }
        
        // Aggiungi tabella se presente
        if (content.table) {
            const tableContainer = document.createElement('div');
            tableContainer.innerHTML = renderVisualContent(content);
            messageContent.appendChild(tableContainer);
        }
    } else {
        // Messaggio normale
        messageContent.innerHTML = formatMessageContent(content);
    }
    
    messageDiv.appendChild(messageContent);
    elements.chatHistory.appendChild(messageDiv);
    
    // Add to chat history array
    chatHistory.push({ sender, content, timestamp: new Date().toISOString() });
    
    // Scroll to bottom
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    
    // Animate message
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    setTimeout(() => {
        messageDiv.style.transition = 'all 0.3s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 10);
}

function formatMessageContent(content) {
    // Check if content contains chart or table data
    if (typeof content === 'object' && content.type) {
        return renderVisualContent(content);
    }
    
    // Check if content is a string that contains JSON for charts/tables
    if (typeof content === 'string') {
        try {
            const parsed = JSON.parse(content);
            if (parsed.type && (parsed.type === 'chart' || parsed.type === 'table')) {
                return renderVisualContent(parsed);
            }
        } catch (e) {
            // Not JSON, continue with normal formatting
        }
    }
    
    // Enhanced markdown formatting
    let formatted = content;
    
    // Headers (### -> h3, ## -> h2, # -> h1)
    formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    formatted = formatted.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Code blocks (```code```)
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code (`code`)
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold and italic
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Lists - handle them more carefully
    // First, handle unordered lists
    const unorderedListRegex = /((?:^[\s]*[-\*] .*$\n?)+)/gm;
    formatted = formatted.replace(unorderedListRegex, (match) => {
        const items = match.replace(/^[\s]*[-\*] (.*)$/gm, '<li>$1</li>');
        return `<ul>${items}</ul>`;
    });
    
    // Then handle ordered lists
    const orderedListRegex = /((?:^[\s]*\d+\. .*$\n?)+)/gm;
    formatted = formatted.replace(orderedListRegex, (match) => {
        const items = match.replace(/^[\s]*\d+\. (.*)$/gm, '<li>$1</li>');
        return `<ol>${items}</ol>`;
    });
    
    // Links [text](url)
    formatted = formatted.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Tables (basic support)
    const tableRegex = /\|(.+)\|\n\|[-\s\|]+\|\n((\|.+\|\n?)+)/g;
    formatted = formatted.replace(tableRegex, (match, header, rows) => {
        const headerCells = header.split('|').map(cell => cell.trim()).filter(cell => cell);
        const rowsArray = rows.trim().split('\n').map(row => 
            row.split('|').map(cell => cell.trim()).filter(cell => cell)
        );
        
        let tableHtml = '<table class="markdown-table"><thead><tr>';
        headerCells.forEach(cell => {
            tableHtml += `<th>${cell}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';
        
        rowsArray.forEach(row => {
            tableHtml += '<tr>';
            row.forEach(cell => {
                tableHtml += `<td>${cell}</td>`;
            });
            tableHtml += '</tr>';
        });
        
        tableHtml += '</tbody></table>';
        return tableHtml;
    });
    
    // Line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not already wrapped
    if (!formatted.startsWith('<')) {
        formatted = `<p>${formatted}</p>`;
    }
    
    return formatted;
}

function renderVisualContent(data) {
    const containerId = 'chart-' + Date.now();
    
    // Gestisci dati chart
    if (data.chart) {
        const chartData = data.chart;
        let plotlyData = [];
        
        if (chartData.type === 'bar') {
            plotlyData = [{
                x: chartData.data.x,
                y: chartData.data.y,
                type: 'bar',
                marker: {
                    color: 'rgba(0, 255, 255, 0.7)',
                    line: {
                        color: 'rgba(0, 255, 255, 1)',
                        width: 1
                    }
                }
            }];
        } else if (chartData.type === 'line') {
            plotlyData = [{
                x: chartData.data.x,
                y: chartData.data.y,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: 'rgba(0, 255, 255, 1)' },
                marker: { color: 'rgba(0, 255, 255, 0.8)' }
            }];
        } else if (chartData.type === 'pie') {
            plotlyData = [{
                labels: chartData.data.labels,
                values: chartData.data.values,
                type: 'pie',
                marker: {
                    colors: ['rgba(0, 255, 255, 0.8)', 'rgba(0, 150, 255, 0.8)', 'rgba(0, 100, 200, 0.8)']
                }
            }];
        }
        
        const layout = {
            title: {
                text: chartData.title || 'Grafico',
                font: { color: '#00ffff' }
            },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0.3)',
            font: { color: '#ffffff' },
            xaxis: { color: '#ffffff' },
            yaxis: { color: '#ffffff' }
        };
        
        return `
            <div class="chart-container">
                <h4 class="chart-title">${chartData.title || 'Grafico'}</h4>
                <div id="${containerId}" class="plotly-chart"></div>
                <script>
                    setTimeout(() => {
                        const plotlyData = ${JSON.stringify(plotlyData)};
                        const layout = ${JSON.stringify(layout)};
                        const config = {responsive: true, displayModeBar: true};
                        Plotly.newPlot('${containerId}', plotlyData, layout, config);
                    }, 100);
                </script>
            </div>
        `;
    }
    
    // Gestisci dati table
    if (data.table) {
        const tableData = data.table;
        const tableHtml = generateTableHTML(tableData);
        return `
            <div class="table-container">
                <h4 class="table-title">${tableData.title || 'Tabella'}</h4>
                ${tableHtml}
            </div>
        `;
    }
    
    // Fallback per compatibilità
    if (data.type === 'chart' || data.type === 'table') {
        return renderVisualContent({[data.type]: data});
    }
    
    return data.content || JSON.stringify(data);
}

function generateTableHTML(data) {
    if (!data.headers || !data.rows) {
        return '<p>Dati tabella non validi</p>';
    }
    
    let html = '<table class="analysis-table">';
    
    // Headers
    html += '<thead><tr>';
    data.headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead>';
    
    // Rows
    html += '<tbody>';
    data.rows.forEach(row => {
        html += '<tr>';
        row.forEach(cell => {
            html += `<td>${cell}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    
    return html;
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    const typingId = 'typing-' + Date.now();
    typingDiv.id = typingId;
    typingDiv.className = 'chat-message assistant';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sto analizzando...';
    
    typingDiv.appendChild(messageContent);
    elements.chatHistory.appendChild(typingDiv);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    
    return typingId;
}

function removeTypingIndicator(typingId) {
    const typingElement = document.getElementById(typingId);
    if (typingElement) {
        typingElement.remove();
    }
}

function exportChatHistory() {
    if (chatHistory.length === 0) {
        showNotification('Nessuna conversazione da esportare', 'warning');
        return;
    }
    
    const exportData = {
        timestamp: new Date().toISOString(),
        chat_history: chatHistory,
        ai_overview_data: currentAiOverview
    };
    
    downloadFile(JSON.stringify(exportData, null, 2), 'chat_history.json', 'application/json');
    showNotification('Chat esportata con successo!', 'success');
}

function clearChatHistory() {
    if (chatHistory.length === 0) {
        showNotification('Nessuna conversazione da cancellare', 'warning');
        return;
    }
    
    chatHistory = [];
    elements.chatHistory.innerHTML = '';
    showNotification('Chat cancellata', 'success');
}

// ===== SAVED FILES LIBRARY =====
function saveFileToLibrary(data, originalFileName = null) {
    const fileId = Date.now().toString();
    const fileName = originalFileName || `ai_overview_${new Date().toISOString().split('T')[0]}.json`;
    
    const fileEntry = {
        id: fileId,
        name: fileName,
        query: data.query,
        data: data,
        timestamp: new Date().toISOString(),
        wordCount: (data.ai_overview || data.content || '').split(' ').length
    };
    
    savedFiles.push(fileEntry);
    saveSavedFilesToStorage();
    renderSavedFilesList();
    
    return fileId;
}

function loadSavedFilesFromStorage() {
    const saved = localStorage.getItem('aiAnalyzerSavedFiles');
    if (saved) {
        try {
            savedFiles = JSON.parse(saved);
        } catch (error) {
            console.error('Errore nel caricamento dei file salvati:', error);
            savedFiles = [];
        }
    }
    renderSavedFilesList();
}

function saveSavedFilesToStorage() {
    localStorage.setItem('aiAnalyzerSavedFiles', JSON.stringify(savedFiles));
}

function renderSavedFilesList() {
    if (savedFiles.length === 0) {
        elements.savedFilesList.innerHTML = `
            <div class="empty-state" id="emptyFilesState">
                <i class="fas fa-folder-open"></i>
                <p>Nessun file salvato</p>
                <small>Carica o estrai AI Overview per popolare la libreria</small>
            </div>
        `;
        return;
    }
    
    const filesHtml = savedFiles.map(file => `
        <div class="file-item ${selectedFileId === file.id ? 'selected' : ''}" data-file-id="${file.id}">
            <div class="file-info">
                <div class="file-name">
                    <i class="fas fa-file-code"></i>
                    ${file.name}
                </div>
                <div class="file-details">
                    <span class="file-query">Query: ${file.query}</span>
                    <span class="file-date">${new Date(file.timestamp).toLocaleDateString('it-IT')}</span>
                    <span>${file.wordCount} parole</span>
                </div>
            </div>
            <div class="file-actions">
                <button class="file-action-btn" onclick="selectFile('${file.id}')">
                    <i class="fas fa-eye"></i>
                    Seleziona
                </button>
                <button class="file-action-btn" onclick="loadFileToContentGap('${file.id}')">
                    <i class="fas fa-comments"></i>
                    Analizza
                </button>
                <button class="file-action-btn danger" onclick="deleteFile('${file.id}')">
                    <i class="fas fa-trash"></i>
                    Elimina
                </button>
            </div>
        </div>
    `).join('');
    
    elements.savedFilesList.innerHTML = filesHtml;
}

function selectFile(fileId) {
    selectedFileId = fileId;
    const file = savedFiles.find(f => f.id === fileId);
    if (file) {
        currentAiOverview = file.data;
        renderSavedFilesList();
        showNotification(`File "${file.name}" selezionato`, 'success');
    }
}

function loadFileToContentGap(fileId) {
    const file = savedFiles.find(f => f.id === fileId);
    if (file) {
        currentAiOverview = file.data;
        selectedFileId = fileId;
        
        // Enable chat interface
        elements.chatInput.disabled = false;
        elements.sendChatBtn.disabled = false;
        
        // Switch to content gap tab
        switchTab('content-gap');
        
        // Add welcome message
        const welcomeMessage = `File "${file.name}" caricato per l'analisi! Contiene ${file.wordCount} parole estratte dalla query "${file.query}". Ora puoi farmi domande per analizzare il content gap.`;
        
        // Clear existing chat and add welcome message
        elements.chatHistory.innerHTML = '';
        chatHistory = [];
        addChatMessage('assistant', welcomeMessage);
        
        renderSavedFilesList();
        showNotification('File caricato nel Content Gap Analyzer!', 'success');
    }
}

function deleteFile(fileId) {
    if (confirm('Sei sicuro di voler eliminare questo file?')) {
        savedFiles = savedFiles.filter(f => f.id !== fileId);
        if (selectedFileId === fileId) {
            selectedFileId = null;
            currentAiOverview = null;
        }
        saveSavedFilesToStorage();
        renderSavedFilesList();
        showNotification('File eliminato', 'success');
    }
}



function downloadFile(data, filename, mimeType = null) {
    const blob = data instanceof Blob ? data : new Blob([data], { type: mimeType || 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function updateSessionStats() {
    // Update footer stats
    if (elements.footerExtractions) {
        elements.footerExtractions.textContent = sessionStats.extractions;
    }
    if (elements.footerAnalyses) {
        elements.footerAnalyses.textContent = sessionStats.analyses;
    }
    
    // Save to localStorage
    localStorage.setItem('aiAnalyzerStats', JSON.stringify(sessionStats));
}

// ===== UTILITY FUNCTIONS =====
function showLoading(show) {
    if (show) {
        elements.loadingOverlay.classList.add('active');
    } else {
        elements.loadingOverlay.classList.remove('active');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    elements.notificationContainer.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
    
    // Click to dismiss
    notification.addEventListener('click', () => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    });
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

function loadSessionData() {
    const savedStats = localStorage.getItem('aiAnalyzerStats');
    if (savedStats) {
        sessionStats = { ...sessionStats, ...JSON.parse(savedStats) };
    }
}

function loadSavedData() {
    // Load any saved data from localStorage
    const savedOverview = localStorage.getItem('currentAiOverview');
    if (savedOverview) {
        try {
            currentAiOverview = JSON.parse(savedOverview);
        } catch (error) {
            console.error('Errore nel caricamento dei dati salvati:', error);
        }
    }
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to extract AI Overview
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (document.activeElement === elements.queryInput) {
            extractAiOverview();
        }
    }
    
    // Escape to close notifications
    if (e.key === 'Escape') {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => {
            notification.click();
        });
    }
});

// ===== AUTO-SAVE =====
setInterval(() => {
    if (currentAiOverview) {
        localStorage.setItem('currentAiOverview', JSON.stringify(currentAiOverview));
    }
}, 30000); // Save every 30 seconds

// ===== PERFORMANCE MONITORING =====
window.addEventListener('load', function() {
    const loadTime = performance.now();
    console.log(`🚀 Ai Analyzer caricato in ${Math.round(loadTime)}ms`);
    
    // Show welcome notification
    setTimeout(() => {
        showNotification('Benvenuto in Stratego Ai Analyzer! Sistema pronto per l\'uso.', 'success');
    }, 1000);
});

// ===== ERROR HANDLING =====
window.addEventListener('error', function(e) {
    console.error('Errore JavaScript:', e.error);
    showNotification('Si è verificato un errore. Ricarica la pagina se il problema persiste.', 'error');
});

// ===== EXPORT GLOBAL FUNCTIONS =====
window.switchTab = switchTab;
window.showNotification = showNotification;

console.log('🎯 Ai Analyzer JavaScript caricato e pronto!');