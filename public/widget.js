/**
 * Miriel Chat Widget - Drawer Style
 * Embeddable chat widget that works on any website
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    API_BASE_URL: window.MIRIEL_API_URL || 'http://localhost:8000/api/v1',
    API_KEY: document.currentScript?.getAttribute('data-api-key') || '',
  };

  // State
  let state = {
    isOpen: false,
    sessionId: null,
    messages: [],
    isLoading: false,
    tenantId: null,
    chatbotName: null,
    colors: null,
    companyName: null,
  };

  // Initialize widget
  async function init() {
    // Load configuration first
    await loadConfig();
    
    // Load session from localStorage
    const savedSession = localStorage.getItem('miriel_session_id');
    if (savedSession) {
      state.sessionId = parseInt(savedSession);
    }

    // Inject CSS
    injectCSS();
    
    // Create widget HTML
    createWidget();
    
    // Apply customization
    applyCustomization();
    
    // Load existing messages if session exists
    if (state.sessionId) {
      loadMessages();
    }
  }
  
  // Load widget configuration
  async function loadConfig() {
    if (!CONFIG.API_KEY) {
      console.error('Miriel Widget: API key is required');
      return;
    }
    
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/widgets/config?api_key=${CONFIG.API_KEY}`);
      
      if (!response.ok) {
        console.error('Miriel Widget: Failed to load configuration');
        return;
      }
      
      const data = await response.json();
      state.tenantId = data.tenant_id;
      state.chatbotName = data.chatbot_name;
      state.colors = data.colors;
      state.companyName = data.company_name;
      
    } catch (error) {
      console.error('Miriel Widget: Error loading configuration', error);
    }
  }

  // Inject CSS
  function injectCSS() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = CONFIG.API_BASE_URL.replace('/api/v1', '') + '/widget.css';
    document.head.appendChild(link);
  }

  // Create widget HTML
  function createWidget() {
    // Create tab button
    const tab = document.createElement('button');
    tab.className = 'miriel-chat-tab';
    tab.innerHTML = '💬 Chat with us';
    tab.onclick = toggleDrawer;
    document.body.appendChild(tab);

    // Create drawer
    const drawer = document.createElement('div');
    drawer.className = 'miriel-chat-drawer';
    drawer.id = 'miriel-chat-drawer';
    drawer.innerHTML = `
      <div class="miriel-chat-header" id="miriel-header">
        <h3 class="miriel-chat-title" id="miriel-title">Chat Support</h3>
        <button class="miriel-chat-close" id="miriel-close" onclick="window.MirielChat.close()">×</button>
      </div>
      
      <div class="miriel-chat-messages" id="miriel-messages">
        <div class="miriel-welcome">
          <h4 class="miriel-welcome-title">👋 Welcome!</h4>
          <p class="miriel-welcome-text">How can we help you today?</p>
        </div>
      </div>
      
      <div class="miriel-chat-input-container">
        <div class="miriel-chat-input-wrapper">
          <textarea 
            id="miriel-input" 
            class="miriel-chat-input" 
            placeholder="Type your message..."
            rows="1"
          ></textarea>
          <button class="miriel-chat-send" id="miriel-send">Send</button>
        </div>
      </div>
    `;
    document.body.appendChild(drawer);

    // Setup event listeners
    setupEventListeners();
  }

  // Setup event listeners
  function setupEventListeners() {
    const input = document.getElementById('miriel-input');
    const sendBtn = document.getElementById('miriel-send');

    // Send on button click
    sendBtn.onclick = sendMessage;

    // Send on Enter (but Shift+Enter for new line)
    input.onkeydown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    };

    // Auto-resize textarea
    input.oninput = () => {
      input.style.height = 'auto';
      input.style.height = input.scrollHeight + 'px';
    };
  }

  // Apply customization colors
  function applyCustomization() {
    if (!state.colors) return;

    // Update title with chatbot name
    if (state.chatbotName) {
      const title = document.getElementById('miriel-title');
      if (title) {
        title.textContent = state.chatbotName;
      }
    }

    // Create style element for custom colors
    const style = document.createElement('style');
    style.id = 'miriel-custom-styles';
    
    const colors = state.colors;
    style.textContent = `
      /* Custom Widget Colors */
      .miriel-chat-tab {
        background: ${colors.send_button_color} !important;
      }
      
      .miriel-chat-header {
        background: linear-gradient(135deg, ${colors.chat_header_color} 0%, ${colors.chat_header_color}dd 100%) !important;
      }
      
      .miriel-chat-close {
        color: ${colors.close_icon_color} !important;
      }
      
      .miriel-chat-messages {
        background: ${colors.chat_bg_color} !important;
      }
      
      .miriel-message.ai .miriel-message-content {
        background: ${colors.ai_bubble_color} !important;
      }
      
      .miriel-message.human .miriel-message-content {
        background: ${colors.human_bubble_color} !important;
      }
      
      .miriel-message.human .miriel-message-avatar {
        background: ${colors.human_bubble_color} !important;
      }
      
      .miriel-chat-input {
        background: ${colors.text_box_color} !important;
      }
      
      .miriel-chat-send {
        background: ${colors.send_button_color} !important;
      }
      
      .miriel-chat-send:hover:not(:disabled) {
        background: ${colors.send_button_color}dd !important;
      }
      
      .miriel-chat-input:focus {
        border-color: ${colors.send_button_color} !important;
      }
    `;
    
    document.head.appendChild(style);
  }

  // Toggle drawer open/close
  function toggleDrawer() {
    state.isOpen = !state.isOpen;
    const drawer = document.getElementById('miriel-chat-drawer');
    
    if (state.isOpen) {
      drawer.classList.add('open');
      document.getElementById('miriel-input').focus();
    } else {
      drawer.classList.remove('open');
    }
  }

  // Close drawer
  function closeDrawer() {
    state.isOpen = false;
    document.getElementById('miriel-chat-drawer').classList.remove('open');
  }

  // Send message
  async function sendMessage() {
    const input = document.getElementById('miriel-input');
    const message = input.value.trim();
    
    if (!message || state.isLoading) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Add user message to UI
    addMessage('human', message);

    // Show typing indicator
    showTyping();

    // Disable input while loading
    state.isLoading = true;
    updateInputState();

    try {
      // Call API
      const response = await fetch(`${CONFIG.API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tenant_id: state.tenantId,
          session_id: state.sessionId || null,
          message: message,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();

      // Save session ID
      if (data.session_id && !state.sessionId) {
        state.sessionId = data.session_id;
        localStorage.setItem('miriel_session_id', data.session_id);
      }

      // Hide typing indicator
      hideTyping();

      // Add AI response
      addMessage('ai', data.content, data.sources);

    } catch (error) {
      console.error('Error sending message:', error);
      hideTyping();
      showError('Failed to send message. Please try again.');
    } finally {
      state.isLoading = false;
      updateInputState();
    }
  }

  // Add message to UI
  function addMessage(role, content, sources = []) {
    const messagesContainer = document.getElementById('miriel-messages');
    
    // Remove welcome message if exists
    const welcome = messagesContainer.querySelector('.miriel-welcome');
    if (welcome) {
      welcome.remove();
    }

    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `miriel-message ${role}`;
    
    const avatar = role === 'human' ? '👤' : '🤖';
    let sourcesHTML = '';
    
    if (sources && sources.length > 0) {
      sourcesHTML = `
        <div class="miriel-message-sources">
          <strong>Sources:</strong>
          ${sources.map(s => `<a href="${s.url}" target="_blank">📄 ${s.url}</a>`).join('')}
        </div>
      `;
    }
    
    messageEl.innerHTML = `
      <div class="miriel-message-avatar">${avatar}</div>
      <div class="miriel-message-content">
        <p class="miriel-message-text">${escapeHtml(content)}</p>
        ${sourcesHTML}
      </div>
    `;
    
    messagesContainer.appendChild(messageEl);
    scrollToBottom();
  }

  // Show typing indicator
  function showTyping() {
    const messagesContainer = document.getElementById('miriel-messages');
    const typing = document.createElement('div');
    typing.id = 'miriel-typing';
    typing.className = 'miriel-message ai';
    typing.innerHTML = `
      <div class="miriel-message-avatar">🤖</div>
      <div class="miriel-message-content">
        <div class="miriel-typing">
          <div class="miriel-typing-dot"></div>
          <div class="miriel-typing-dot"></div>
          <div class="miriel-typing-dot"></div>
        </div>
      </div>
    `;
    messagesContainer.appendChild(typing);
    scrollToBottom();
  }

  // Hide typing indicator
  function hideTyping() {
    const typing = document.getElementById('miriel-typing');
    if (typing) {
      typing.remove();
    }
  }

  // Show error message
  function showError(message) {
    const messagesContainer = document.getElementById('miriel-messages');
    const error = document.createElement('div');
    error.className = 'miriel-error';
    error.textContent = message;
    messagesContainer.appendChild(error);
    scrollToBottom();
    
    // Remove error after 5 seconds
    setTimeout(() => error.remove(), 5000);
  }

  // Load existing messages
  async function loadMessages() {
    if (!state.sessionId) return;

    try {
      const response = await fetch(
        `${CONFIG.API_BASE_URL}/chat/sessions/${state.sessionId}/messages`
      );
      
      if (!response.ok) return;

      const data = await response.json();
      
      // Add messages to UI
      data.messages.forEach(msg => {
        addMessage(msg.role, msg.content, msg.meta?.sources);
      });

    } catch (error) {
      console.error('Error loading messages:', error);
    }
  }

  // Update input state (enabled/disabled)
  function updateInputState() {
    const input = document.getElementById('miriel-input');
    const sendBtn = document.getElementById('miriel-send');
    
    input.disabled = state.isLoading;
    sendBtn.disabled = state.isLoading;
  }

  // Scroll to bottom
  function scrollToBottom() {
    const messagesContainer = document.getElementById('miriel-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Public API
  window.MirielChat = {
    open: () => {
      if (!state.isOpen) toggleDrawer();
    },
    close: closeDrawer,
    send: (message) => {
      document.getElementById('miriel-input').value = message;
      sendMessage();
    },
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();

