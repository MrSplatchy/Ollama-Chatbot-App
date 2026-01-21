const promptForm = document.getElementById('promptForm');
const promptInput = document.getElementById('prompt');
const sendButton = document.getElementById('sendButton');
const chatMessages = document.getElementById('chatMessages');
let currentController = null;
let isGenerating = false;
let buffer = [];
let userResizing = false;

// Permettre le redimensionnement manuel du textarea
promptInput.style.resize = "vertical";

// Détecter le début et la fin du redimensionnement manuel
promptInput.addEventListener('mousedown', () => {
    userResizing = true;
});

window.addEventListener('mouseup', () => {
    userResizing = false;
});

// Fonction pour redimensionner automatiquement le textarea
function autoResizeTextarea() {
    if (!userResizing) {
        promptInput.style.height = 'auto';
        const newHeight = Math.min(promptInput.scrollHeight, 400); // 400px = seuil max
        promptInput.style.height = newHeight + 'px';
    }
}

// Vérifier si l'on peut envoyer un message
function canSendMessage() {
    return promptInput.value.trim().length > 0 && !isGenerating;
}

// Mettre à jour l'état du bouton d'envoi
function updateSendButtonState() {
    if (canSendMessage()) {
        sendButton.style.opacity = '1';
        sendButton.style.cursor = 'pointer';
    } else {
        sendButton.style.opacity = '0.5';
        sendButton.style.cursor = 'not-allowed';
    }
}

// Gérer l'envoi ou l'arrêt du message
async function handleSendOrStop() {
    if (isGenerating) {
        currentController?.abort();
        isGenerating = false;
        sendButton.textContent = '➤';
        sendButton.style.backgroundColor = '';
        document.getElementById('loadingIndicator').style.display = 'none';
        updateSendButtonState();
    } else if (canSendMessage()) {
        await generateResponse();
    }
}

// Ajouter un message dans la zone de chat
function addMessage(content, className) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${className}`;
    messageElement.innerHTML = content;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageElement;
}

// Générer la réponse de l'IA
async function generateResponse() {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    isGenerating = true;
    sendButton.textContent = '■';
    sendButton.style.backgroundColor = 'red';
    document.getElementById('loadingIndicator').style.display = 'inline-block';

    addMessage(prompt, 'user-message');
    promptInput.value = '';
    autoResizeTextarea(); // Réinitialiser la hauteur du textarea après l'envoi

    const botMessage = addMessage('', 'bot-message');

    try {
        currentController = new AbortController();
        const response = await fetch('/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ prompt: prompt }),
            signal: currentController.signal
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer.push(decoder.decode(value));
            if (buffer.length >= 1) {
                botMessage.innerHTML += buffer.join('').replace(/\n/g, '<br>');
                buffer = [];
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
        
        if (buffer.length > 0) {
            botMessage.innerHTML += buffer.join('').replace(/\n/g, '<br>');
            chatMessages.scrollTop = chatMessages.scrollHeight;
            buffer = [];
        }

    } catch (error) {
        if (error.name !== 'AbortError') {
            botMessage.innerHTML = '<span style="color: red;">Error: Unable to get response</span>';
        }
    } finally {
        isGenerating = false;
        sendButton.textContent = '➤';
        sendButton.style.backgroundColor = '';
        currentController = null;
        document.getElementById('loadingIndicator').style.display = 'none';
        updateSendButtonState();
    }
}

// Événements
promptInput.addEventListener('input', () => {
    updateSendButtonState();
    autoResizeTextarea(); // Redimensionner automatiquement lors de la saisie
});

promptInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendOrStop();
    }
});

sendButton.addEventListener('click', handleSendOrStop);

window.addEventListener('load', updateSendButtonState);

// Rendre le redimensionnement plus fluide
promptInput.style.transition = 'height 0.2s ease';