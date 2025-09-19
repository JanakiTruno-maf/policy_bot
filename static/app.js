const form = document.getElementById('chat-form');
const msgEl = document.getElementById('message');
const conversation = document.getElementById('conversation');
const clearBtn = document.getElementById('clear-btn');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = (msgEl.value || '').trim();
  const top_k = 5;

  if (!message) {
    msgEl.focus();
    return;
  }

  // Clear welcome message if it exists
  const welcomeMsg = conversation.querySelector('.welcome-message');
  if (welcomeMsg) {
    welcomeMsg.remove();
  }
  
  // Add user message to conversation
  addMessage('user', message);
  
  // Clear input and show loading
  msgEl.value = '';
  msgEl.disabled = true;
  addMessage('assistant', 'Analyzing legal documents...', true);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message, top_k })
    });
    const data = await res.json();

    // Remove loading message
    removeLastMessage();

    if (!res.ok) {
      throw new Error(data.error || 'Server error');
    }

    // Add assistant response
    addMessage('assistant', data.annotated_text || data.response || '', false, data.sources || []);

  } catch (err) {
    removeLastMessage();
    addMessage('assistant', 'Error: ' + err.message);
  } finally {
    msgEl.disabled = false;
    msgEl.focus();
  }
});

function addMessage(sender, text, isLoading = false, sources = []) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  if (isLoading) {
    messageDiv.classList.add('loading');
  }

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  
  // Simple markdown rendering for bold text and sources
  let htmlText = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
  
  contentDiv.innerHTML = htmlText;

  messageDiv.appendChild(contentDiv);

  // Add sources if provided
  if (sources.length > 0) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'sources';
    sourcesDiv.innerHTML = '<h4>Legal Sources:</h4>';
    
    const sourcesList = document.createElement('ol');
    sources.forEach((s, i) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      let href = s.uri || '#';
      
      // Add page number as fragment for PDF viewers
      if (s.page_number) {
        href += `#page=${s.page_number}`;
      }
      
      a.href = href;
      a.textContent = s.title || s.uri || `Source ${i+1}`;
      a.target = '_blank';
      a.className = 'source-link';
      
      const score = (typeof s.score === 'number') ? ` (Relevance: ${s.score.toFixed(2)})` : '';
      
      // Build location info string
      const locationInfo = s.page_range ? ` - Page ${s.page_range}` : '';
      
      li.appendChild(a);
      li.appendChild(document.createTextNode(score + locationInfo));
      
      // Add text preview if available
      if (s.text) {
        const preview = document.createElement('div');
        preview.className = 'source-preview';
        const truncatedText = s.text.length > 200 ? s.text.substring(0, 200) + '...' : s.text;
        preview.innerHTML = `<em>"${truncatedText}"</em>`;
        li.appendChild(preview);
      }
      
      sourcesList.appendChild(li);
    });
    
    sourcesDiv.appendChild(sourcesList);
    messageDiv.appendChild(sourcesDiv);
  }

  conversation.appendChild(messageDiv);
  conversation.scrollTop = conversation.scrollHeight;
}

function removeLastMessage() {
  const lastMessage = conversation.lastElementChild;
  if (lastMessage) {
    conversation.removeChild(lastMessage);
  }
}

// Focus on input when page loads
msgEl.focus();

// Clear conversation
if (clearBtn) {
  clearBtn.addEventListener('click', async () => {
    try {
      await fetch('/clear', { method: 'POST' });
      conversation.innerHTML = `
        <div class="welcome-message">
          <h3>Welcome to MAF Policy Bot</h3>
          <p>I provide factual information about tobacco laws, regulations, and legal requirements from our document database. Ask me about tobacco legislation, compliance requirements, or market regulations.</p>
        </div>
      `;
    } catch (err) {
      console.error('Failed to clear conversation:', err);
    }
  });
}