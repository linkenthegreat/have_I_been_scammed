let currentCheckId = null;
let sessionId = null; // ← Store session ID persistently

// Initialize session ID when page loads
function initializeSession() {
    // Generate session ID once (format: user_abc123xyz)
    sessionId = 'user_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    console.log('🆔 Session initialized:', sessionId);
}

// Call on page load
initializeSession();

// New Chat button handler
document.addEventListener('DOMContentLoaded', () => {
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            const confirmed = confirm('Start a new conversation? Current chat will be cleared.');
            if (confirmed) {
                // Generate new session ID
                sessionId = 'user_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
                console.log('🆔 New session started:', sessionId);
                
                // Clear current check_id
                currentCheckId = null;
                
                // Clear chat messages (keep welcome message)
                const chatMessages = document.getElementById('chatMessages');
                const welcomeMessage = chatMessages.querySelector('.message.assistant-message');
                chatMessages.innerHTML = '';
                if (welcomeMessage) {
                    chatMessages.appendChild(welcomeMessage);
                }
                
                // Clear input (with null check)
                const userMessageInput = document.getElementById('userMessage');
                if (userMessageInput) {
                    userMessageInput.value = '';
                }
                
                // Clear file attachments
                const imageUpload = document.getElementById('image-upload');
                const audioUpload = document.getElementById('audio-upload');
                if (imageUpload) imageUpload.value = '';
                if (audioUpload) audioUpload.value = '';
                
                const fileAttachments = document.getElementById('fileAttachments');
                const imageTag = document.getElementById('imageTag');
                const audioTag = document.getElementById('audioTag');
                if (fileAttachments) fileAttachments.style.display = 'none';
                if (imageTag) imageTag.style.display = 'none';
                if (audioTag) audioTag.style.display = 'none';
                
                // Show confirmation message
                addMessage('assistant', '✨ New conversation started. How can I help you today?');
            }
        });
    }
});

// Show file attachments
if (document.getElementById('image-upload')) {
    document.getElementById('image-upload').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('image-filename-tag').textContent = file.name;
            document.getElementById('imageTag').style.display = 'inline-block';
            document.getElementById('fileAttachments').style.display = 'block';
        }
    });
}

if (document.getElementById('audio-upload')) {
    document.getElementById('audio-upload').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('audio-filename-tag').textContent = file.name;
            document.getElementById('audioTag').style.display = 'inline-block';
            document.getElementById('fileAttachments').style.display = 'block';
        }
    });
}

function clearFile(type) {
    if (type === 'image') {
        document.getElementById('image-upload').value = '';
        document.getElementById('imageTag').style.display = 'none';
    } else if (type === 'audio') {
        document.getElementById('audio-upload').value = '';
        document.getElementById('audioTag').style.display = 'none';
    }
    
    // Hide container if no files
    const hasImage = document.getElementById('imageTag').style.display !== 'none';
    const hasAudio = document.getElementById('audioTag').style.display !== 'none';
    if (!hasImage && !hasAudio) {
        document.getElementById('fileAttachments').style.display = 'none';
    }
}

async function analyzeScam() {
    const content = document.getElementById('userInput').value.trim();
    
    // Check for multimodal files
    const imageFile = document.getElementById('image-upload')?.files[0];
    const audioFile = document.getElementById('audio-upload')?.files[0];
    const hasFiles = imageFile || audioFile;

    if (!content && !hasFiles) {
        return alert("Please enter a message or attach a file to analyze.");
    }

    // Get optional context
    const userLocation = document.getElementById('userLocation').value;
    const userRole = document.getElementById('userRole').value;

    // Add user message to chat
    addMessage('user', content || '[Attached files]');
    
    // Clear input
    document.getElementById('userInput').value = '';
    
    // Add thinking indicator
    addThinkingIndicator();

    try {
        let response;
        
        if (hasFiles) {
            // Use FormData for multimodal file upload
            const formData = new FormData();
            formData.append('session_id', sessionId); // ← Use persistent session ID
            formData.append('content', content || '');
            
            if (userLocation) formData.append('user_location', userLocation);
            if (userRole) formData.append('user_role', userRole);
            
            if (imageFile) formData.append('image_file', imageFile);
            if (audioFile) formData.append('audio_file', audioFile);
            
            response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData  // No Content-Type header - browser sets it automatically
            });
        } else {
            // Use JSON for text-only requests
            response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId, // ← Use persistent session ID
                    content: content,
                    user_location: userLocation || null,
                    user_role: userRole || null
                })
            });
        }

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        displayResult(data);

    } catch (error) {
        removeThinkingIndicator();
        addMessage('assistant', `❌ Error: ${error.message}`);
    }
}

function addMessage(role, text) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = text.replace(/\n/g, '<br>');
    
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addThinkingIndicator() {
    const messagesDiv = document.getElementById('chatMessages');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message assistant-message';
    thinkingDiv.id = 'thinkingIndicator';
    thinkingDiv.innerHTML = '<div class="message-content">🤔 Analyzing...</div>';
    messagesDiv.appendChild(thinkingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function removeThinkingIndicator() {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) indicator.remove();
}

function displayResult(data) {
    removeThinkingIndicator();
    
    // Build response message
    let responseHTML = '';
    
    // Handle both "analysis" and "chat" response types
    if (data.type === 'analysis' && data.raw_analysis && data.raw_analysis.risk_score) {
        const risk = data.raw_analysis.risk_score.toLowerCase();
        const riskEmoji = risk === 'high' || risk === 'danger' ? '🚨' : (risk === 'caution' ? '⚠️' : '✅');
        responseHTML = `<h3>${riskEmoji} Risk Assessment: ${risk.toUpperCase()}</h3>`;
    }
    
    // Add report/message content
    const reportText = data.report || data.message || 'No response received';
    responseHTML += reportText.replace(/\n/g, '<br>');
    
    // Add export links if available
    if (data.check_id) {
        responseHTML += `<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);">`;
        responseHTML += `<p><strong>Export Options:</strong></p>`;
        responseHTML += `<a href="/api/export/email?check_id=${data.check_id}" style="margin-right: 1rem;">📧 Email Draft</a>`;
        responseHTML += `<a href="/api/export/pdf?check_id=${data.check_id}">📄 Download PDF</a>`;
        responseHTML += `</div>`;
        currentCheckId = data.check_id;
    }
    
    // Display in chat
    addMessage('assistant', responseHTML);
    
    // Clear file attachments
    clearFile('image');
    clearFile('audio');

    // Store check ID for feedback
    currentCheckId = data.check_id;
}

async function sendFeedback(helpful) {
    if (!currentCheckId) return;

    try {
        await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                check_id: currentCheckId,
                helpful: helpful
            })
        });
        alert("Thanks for your feedback! This helps our agents learn.");
    } catch (e) {
        console.error("Feedback error:", e);
    }
}
