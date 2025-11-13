/**
 * ABSolution Dialogue Panel - JavaScript Application
 * Handles all user interactions and API communications
 */

// Configuration
const CONFIG = {
    apiEndpoint: localStorage.getItem('api_endpoint') || 'http://localhost:8000',
    apiKey: localStorage.getItem('api_key') || '',
    sessionId: null,
    isConnected: false
};

// State
const state = {
    messages: [],
    activeAgents: [],
    isProcessing: false
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

/**
 * Initialize the application
 */
async function initializeApp() {
    console.log('Initializing ABSolution Dialogue Panel...');

    // Setup event listeners
    setupEventListeners();

    // Auto-resize textarea
    autoResizeTextarea();

    // Check if API endpoint is configured
    if (!CONFIG.apiEndpoint || CONFIG.apiEndpoint === 'http://localhost:8000') {
        showConfigModal();
    } else {
        // Create session
        await createSession();
    }

    // Add click handlers for example queries
    document.querySelectorAll('.example-query').forEach(element => {
        element.addEventListener('click', () => {
            sendQuickQuery(element.textContent);
        });
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    const input = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    // Send message on button click
    sendButton.addEventListener('click', sendMessage);

    // Send message on Ctrl+Enter
    input.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }

        // Update character count
        updateCharCount();
    });

    input.addEventListener('input', updateCharCount);
}

/**
 * Auto-resize textarea as user types
 */
function autoResizeTextarea() {
    const textarea = document.getElementById('message-input');

    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
}

/**
 * Update character count
 */
function updateCharCount() {
    const input = document.getElementById('message-input');
    const count = document.getElementById('char-count');
    count.textContent = input.value.length;
}

/**
 * Create a new session
 */
async function createSession() {
    try {
        showStatus('Connecting...', 'warning');

        const response = await fetch(`${CONFIG.apiEndpoint}/session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(CONFIG.apiKey && { 'Authorization': `Bearer ${CONFIG.apiKey}` })
            },
            body: JSON.stringify({
                user_id: 'web_user_' + Date.now()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        CONFIG.sessionId = data.session_id;
        CONFIG.isConnected = true;

        // Update UI
        document.getElementById('session-id').textContent = `Session: ${CONFIG.sessionId.substring(0, 8)}...`;
        showStatus('Connected', 'success');

        console.log('Session created:', CONFIG.sessionId);

    } catch (error) {
        console.error('Failed to create session:', error);
        showStatus('Connection Failed', 'error');
        addSystemMessage(`Failed to connect to API: ${error.message}. Please check your configuration.`);
        showConfigModal();
    }
}

/**
 * Send a message
 */
async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message || state.isProcessing) return;

    if (!CONFIG.sessionId) {
        addSystemMessage('No active session. Please configure API endpoint.');
        showConfigModal();
        return;
    }

    // Clear input and suggestions
    input.value = '';
    input.style.height = 'auto';
    updateCharCount();
    hideSuggestions();

    // Add user message to chat
    addMessage('user', message);

    // Show typing indicator
    showTypingIndicator();

    // Set processing state
    state.isProcessing = true;
    document.getElementById('send-button').disabled = true;

    try {
        const response = await fetch(`${CONFIG.apiEndpoint}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(CONFIG.apiKey && { 'Authorization': `Bearer ${CONFIG.apiKey}` })
            },
            body: JSON.stringify({
                session_id: CONFIG.sessionId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Hide typing indicator
        hideTypingIndicator();

        // Add assistant response
        addMessage('assistant', data.message || data.response, {
            agents: data.metadata?.agents_consulted || data.agents_used || [],
            timestamp: data.metadata?.timestamp || data.timestamp
        });

        // Update active agents
        updateActiveAgents(data.metadata?.agents_consulted || data.agents_used || []);

        // Show suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            showSuggestions(data.suggestions);
        }

    } catch (error) {
        console.error('Failed to send message:', error);
        hideTypingIndicator();
        addSystemMessage(`Error: ${error.message}`);
    } finally {
        state.isProcessing = false;
        document.getElementById('send-button').disabled = false;
        input.focus();
    }
}

/**
 * Send a quick query
 */
function sendQuickQuery(query) {
    const input = document.getElementById('message-input');
    input.value = query;
    input.focus();
    updateCharCount();
    sendMessage();
}

/**
 * Add a message to the chat
 */
function addMessage(type, content, metadata = {}) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Parse markdown-like formatting
    const formattedContent = formatMessage(content);
    contentDiv.innerHTML = formattedContent;

    messageDiv.appendChild(contentDiv);

    // Add metadata for assistant messages
    if (type === 'assistant' && (metadata.agents || metadata.timestamp)) {
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'message-metadata';

        if (metadata.agents && metadata.agents.length > 0) {
            metadata.agents.forEach(agent => {
                const badge = document.createElement('span');
                badge.className = 'agent-badge';
                badge.textContent = formatAgentName(agent);
                metadataDiv.appendChild(badge);
            });
        }

        if (metadata.timestamp) {
            const time = document.createElement('span');
            time.textContent = formatTimestamp(metadata.timestamp);
            metadataDiv.appendChild(time);
        }

        messageDiv.appendChild(metadataDiv);
    }

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    // Store in state
    state.messages.push({ type, content, metadata });
}

/**
 * Add a system message
 */
function addSystemMessage(content) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `<p>${content}</p>`;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Format message content (basic markdown support)
 */
function formatMessage(content) {
    if (!content) return '';

    // Escape HTML
    let formatted = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');

    // Lists
    formatted = formatted.replace(/^- (.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Code blocks
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

    return formatted;
}

/**
 * Format agent name
 */
function formatAgentName(agent) {
    const names = {
        'data_analyst': '📊 Data Analyst',
        'risk_assessor': '⚠️ Risk Assessor',
        'report_generator': '📝 Report Generator',
        'benchmark_analyst': '📈 Benchmark Analyst',
        'alert_monitor': '🔔 Alert Monitor'
    };
    return names[agent] || agent;
}

/**
 * Format timestamp
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    indicator.style.display = 'flex';
    scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    indicator.style.display = 'none';
}

/**
 * Show suggestions
 */
function showSuggestions(suggestions) {
    const container = document.getElementById('suggestions');
    const chipsContainer = document.getElementById('suggestion-chips');

    // Clear existing suggestions
    chipsContainer.innerHTML = '';

    // Add new suggestions
    suggestions.forEach(suggestion => {
        const chip = document.createElement('div');
        chip.className = 'suggestion-chip';
        chip.textContent = suggestion;
        chip.addEventListener('click', () => {
            sendQuickQuery(suggestion);
        });
        chipsContainer.appendChild(chip);
    });

    container.style.display = 'block';
}

/**
 * Hide suggestions
 */
function hideSuggestions() {
    const container = document.getElementById('suggestions');
    container.style.display = 'none';
}

/**
 * Update active agents in sidebar
 */
function updateActiveAgents(agents) {
    // Reset all agents
    document.querySelectorAll('.agent-card').forEach(card => {
        card.classList.remove('active');
    });

    // Activate used agents
    agents.forEach(agent => {
        const card = document.querySelector(`.agent-card[data-agent="${agent}"]`);
        if (card) {
            card.classList.add('active');

            // Remove active class after 3 seconds
            setTimeout(() => {
                card.classList.remove('active');
            }, 3000);
        }
    });

    state.activeAgents = agents;
}

/**
 * Show status
 */
function showStatus(text, type = 'success') {
    const badge = document.getElementById('connection-status');
    const dot = badge.querySelector('.status-dot');

    badge.innerHTML = `<span class="status-dot"></span>${text}`;

    const colors = {
        success: 'var(--success-color)',
        warning: 'var(--warning-color)',
        error: 'var(--danger-color)'
    };

    dot.style.background = colors[type] || colors.success;
}

/**
 * Scroll to bottom of chat
 */
function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
    }, 100);
}

/**
 * Clear chat
 */
function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }

    const messagesContainer = document.getElementById('chat-messages');

    // Remove all messages except welcome message
    const messages = messagesContainer.querySelectorAll('.message');
    messages.forEach((message, index) => {
        if (index > 0) { // Keep first message (welcome)
            message.remove();
        }
    });

    state.messages = [];
    hideSuggestions();
}

/**
 * Export chat
 */
async function exportChat() {
    if (!CONFIG.sessionId) {
        alert('No active session to export');
        return;
    }

    try {
        const response = await fetch(`${CONFIG.apiEndpoint}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(CONFIG.apiKey && { 'Authorization': `Bearer ${CONFIG.apiKey}` })
            },
            body: JSON.stringify({
                session_id: CONFIG.sessionId,
                format: 'markdown'
            })
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        const content = await response.text();

        // Download as file
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `abs-conversation-${Date.now()}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        addSystemMessage('Conversation exported successfully!');

    } catch (error) {
        console.error('Export failed:', error);
        alert('Failed to export conversation: ' + error.message);
    }
}

/**
 * Show configuration modal
 */
function showConfigModal() {
    const modal = document.getElementById('config-modal');
    const endpointInput = document.getElementById('api-endpoint');
    const keyInput = document.getElementById('api-key');

    endpointInput.value = CONFIG.apiEndpoint;
    keyInput.value = CONFIG.apiKey;

    modal.style.display = 'flex';
    endpointInput.focus();
}

/**
 * Close configuration modal
 */
function closeConfigModal() {
    const modal = document.getElementById('config-modal');
    modal.style.display = 'none';
}

/**
 * Save configuration
 */
async function saveConfig() {
    const endpoint = document.getElementById('api-endpoint').value.trim();
    const apiKey = document.getElementById('api-key').value.trim();

    if (!endpoint) {
        alert('Please enter an API endpoint');
        return;
    }

    // Save to localStorage
    localStorage.setItem('api_endpoint', endpoint);
    localStorage.setItem('api_key', apiKey);

    // Update config
    CONFIG.apiEndpoint = endpoint;
    CONFIG.apiKey = apiKey;

    // Close modal
    closeConfigModal();

    // Create new session
    await createSession();
}

// Export functions for HTML onclick handlers
window.sendMessage = sendMessage;
window.sendQuickQuery = sendQuickQuery;
window.clearChat = clearChat;
window.exportChat = exportChat;
window.showConfigModal = showConfigModal;
window.closeConfigModal = closeConfigModal;
window.saveConfig = saveConfig;
