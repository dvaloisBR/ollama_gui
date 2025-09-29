// Configurações e estado da aplicação
class OllamaChatApp {
    constructor() {
        this.currentModel = 'deepseek-coder:latest';
        this.currentLanguage = 'pt';
        this.conversationHistory = [];
        this.isGenerating = false;
        this.isLoadingModel = false;
        this.baseUrl = window.location.origin;
        this.translations = {};
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
        this.checkConnection();
        this.loadModels();
        this.loadTranslations();
    }
    
    initializeElements() {
        // Elementos DOM
        this.elements = {
            chatContainer: document.getElementById('chatContainer'),
            textInput: document.getElementById('textInput'),
            sendBtn: document.getElementById('sendBtn'),
            newChatBtn: document.getElementById('newChatBtn'),
            clearChatBtn: document.getElementById('clearChatBtn'),
            themeToggle: document.getElementById('themeToggle'),
            themeIcon: document.getElementById('themeIcon'),
            typingIndicator: document.getElementById('typingIndicator'),
            mobileMenuBtn: document.getElementById('mobileMenuBtn'),
            modelSelect: document.getElementById('modelSelect'),
            languageSelect: document.getElementById('languageSelect'),
            currentModelBadge: document.getElementById('currentModelBadge'),
            connectionStatus: document.getElementById('connectionStatus'),
            connectionMessage: document.getElementById('connectionMessage'),
            settingsModal: document.getElementById('settingsModal'),
            settingsBtn: document.getElementById('settingsBtn'),
            closeSettings: document.getElementById('closeSettings'),
            progressBar: document.getElementById('progressBar'),
            progressText: document.getElementById('progressText'),
            progressModal: document.getElementById('progressModal')
        };
        
        console.log('Elementos inicializados:', this.elements);
    }
    
    setupEventListeners() {
        // Eventos de input
        this.elements.textInput.addEventListener('input', this.handleInput.bind(this));
        this.elements.textInput.addEventListener('keydown', this.handleKeydown.bind(this));
        
        // Eventos de botões
        this.elements.sendBtn.addEventListener('click', this.sendMessage.bind(this));
        this.elements.newChatBtn.addEventListener('click', this.newConversation.bind(this));
        this.elements.clearChatBtn.addEventListener('click', this.clearConversation.bind(this));
        this.elements.themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        this.elements.mobileMenuBtn.addEventListener('click', this.toggleMobileMenu.bind(this));
        
        // Eventos do modal
        this.elements.settingsBtn.addEventListener('click', () => this.toggleModal(true));
        this.elements.closeSettings.addEventListener('click', () => this.toggleModal(false));
        
        // Evento de seleção de modelo
        this.elements.modelSelect.addEventListener('change', this.changeModel.bind(this));
        this.elements.languageSelect.addEventListener('change', this.changeLanguage.bind(this));
        
        // Fechar modal ao clicar fora
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) {
                this.toggleModal(false);
            }
        });
        
        this.elements.progressModal.addEventListener('click', (e) => {
            if (e.target === this.elements.progressModal) {
                this.toggleProgressModal(false);
            }
        });
    }
    
    async loadTranslations() {
        try {
            console.log('Carregando traduções para:', this.currentLanguage);
            const response = await fetch(`${this.baseUrl}/api/translations/${this.currentLanguage}`);
            
            if (response.ok) {
                const data = await response.json();
                this.translations = data.translations;
                console.log('Traduções carregadas:', this.translations);
                this.updateUITexts();
            } else {
                console.error('Erro ao carregar traduções:', response.status);
            }
        } catch (error) {
            console.error('Erro ao carregar traduções:', error);
        }
    }
    
    updateUITexts() {
        console.log('Atualizando textos da interface...');
        
        // Atualiza textos da interface
        if (this.elements.newChatBtn) {
            this.elements.newChatBtn.innerHTML = `<span>+</span> ${this.translations.new_chat || 'Nova conversa'}`;
        }
        
        if (this.elements.textInput) {
            this.elements.textInput.placeholder = this.translations.placeholder || 'Digite sua mensagem...';
        }
        
        if (this.elements.clearChatBtn) {
            this.elements.clearChatBtn.textContent = this.translations.clear_chat || '🗑️ Limpar Chat';
        }
        
        if (this.elements.typingIndicator) {
            const span = this.elements.typingIndicator.querySelector('span');
            if (span) {
                span.textContent = this.translations.typing || 'DeepSeek está digitando';
            }
        }
        
        // Atualiza mensagem de boas-vindas
        const welcomeMessage = this.elements.chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            const title = welcomeMessage.querySelector('h2');
            const message = welcomeMessage.querySelector('p:first-of-type');
            
            if (title) title.textContent = this.translations.welcome_title || 'Bem-vindo ao DeepSeek Ollama';
            if (message) message.textContent = this.translations.welcome_message || 'Comece uma conversa digitando uma mensagem abaixo.';
        }
        
        // Atualiza select de modelos
        if (this.elements.modelSelect.querySelector('option[value=""]')) {
            this.elements.modelSelect.querySelector('option[value=""]').textContent = 
                this.translations.select_model || 'Selecionar modelo';
        }
    }
    
    async changeLanguage() {
        const newLanguage = this.elements.languageSelect.value;
        
        if (newLanguage && newLanguage !== this.currentLanguage) {
            console.log('Alterando idioma para:', newLanguage);
            
            try {
                const response = await fetch(`${this.baseUrl}/api/language`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ language: newLanguage })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    this.currentLanguage = newLanguage;
                    this.translations = data.translations;
                    localStorage.setItem('language', newLanguage);
                    this.updateUITexts();
                    this.addSystemMessage(`🌐 Idioma alterado para: ${this.getLanguageName(newLanguage)}`);
                    console.log('Idioma alterado com sucesso');
                } else {
                    throw new Error(data.error || 'Erro desconhecido');
                }
            } catch (error) {
                console.error('Erro ao alterar idioma:', error);
                this.addSystemMessage(`❌ Erro ao alterar idioma: ${error.message}`);
                this.elements.languageSelect.value = this.currentLanguage;
            }
        }
    }
    
    getLanguageName(code) {
        const names = {
            'pt': 'Português',
            'en': 'English',
            'es': 'Español', 
            'fr': 'Français',
            'de': 'Deutsch'
        };
        return names[code] || code;
    }
    
    async checkConnection() {
        try {
            console.log('Verificando conexão...');
            const response = await fetch(`${this.baseUrl}/api/health`);
            const data = await response.json();
            
            if (data.ollama === 'connected') {
                this.updateConnectionStatus(true, this.translations.connected || 'Conectado');
                if (this.elements.connectionMessage) {
                    this.elements.connectionMessage.textContent = '✅ ' + (this.translations.connected || 'Conectado');
                    this.elements.connectionMessage.style.color = '#10b981';
                }
                console.log('✅ Conectado ao Ollama');
            } else {
                this.updateConnectionStatus(false, this.translations.disconnected || 'Desconectado');
                if (this.elements.connectionMessage) {
                    this.elements.connectionMessage.textContent = '❌ ' + (this.translations.disconnected || 'Desconectado');
                    this.elements.connectionMessage.style.color = '#ef4444';
                }
                console.log('❌ Ollama desconectado');
            }
        } catch (error) {
            this.updateConnectionStatus(false, 'Erro de conexão');
            if (this.elements.connectionMessage) {
                this.elements.connectionMessage.textContent = '❌ Erro ao conectar com o servidor.';
                this.elements.connectionMessage.style.color = '#ef4444';
            }
            console.error('Erro de conexão:', error);
        }
    }
    
    updateConnectionStatus(connected, message) {
        const statusDot = this.elements.connectionStatus.querySelector('.status-dot');
        const statusText = this.elements.connectionStatus.querySelector('span:last-child');
        
        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = message;
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = message;
        }
    }
    
    async loadModels() {
        try {
            console.log('Carregando modelos...');
            this.elements.modelSelect.innerHTML = `<option value="">${this.translations.models_loading || 'Carregando modelos...'}</option>`;
            
            const response = await fetch(`${this.baseUrl}/api/models`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Modelos recebidos:', data);
            
            if (data.models && data.models.length > 0) {
                this.populateModelSelect(data.models);
                this.currentModel = data.models[0];
                this.updateModelBadge();
                
                if (this.elements.connectionMessage) {
                    this.elements.connectionMessage.innerHTML = 
                        `✅ ${this.translations.connected || 'Conectado'}! <strong>${data.models.length}</strong> modelo(s) disponível(is)`;
                }
                
                console.log(`✅ ${data.models.length} modelos carregados`);
            } else {
                console.warn('Nenhum modelo encontrado no Ollama');
                if (this.elements.connectionMessage) {
                    this.elements.connectionMessage.textContent = '⚠️ Nenhum modelo encontrado. Execute: ollama pull deepseek-coder';
                }
            }
        } catch (error) {
            console.error('Erro ao carregar modelos:', error);
            if (this.elements.connectionMessage) {
                this.elements.connectionMessage.textContent = '❌ Erro ao carregar modelos do Ollama';
            }
        }
    }
    
    populateModelSelect(models) {
        const modelSelect = this.elements.modelSelect;
        modelSelect.innerHTML = '';
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = this.translations.select_model || 'Selecionar modelo';
        modelSelect.appendChild(defaultOption);
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });
        
        if (models.length > 0) {
            modelSelect.value = this.currentModel;
        }
        
        console.log('Select de modelos populado com', models.length, 'modelos');
    }
    
    async changeModel() {
        const newModel = this.elements.modelSelect.value;
        
        if (newModel && newModel !== this.currentModel && !this.isLoadingModel) {
            this.isLoadingModel = true;
            console.log('Alterando modelo para:', newModel);
            
            // Mostra modal de progresso
            this.showProgressModal(true);
            this.updateProgress(10, this.translations.loading_model || 'Carregando modelo...');
            
            try {
                // Simula progresso
                for (let i = 20; i <= 80; i += 20) {
                    this.updateProgress(i, `${this.translations.loading_model || 'Carregando modelo'}... ${i}%`);
                    await new Promise(resolve => setTimeout(resolve, 300));
                }
                
                const response = await fetch(`${this.baseUrl}/api/model`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        model: newModel,
                        language: this.currentLanguage
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    this.currentModel = newModel;
                    this.updateModelBadge();
                    this.updateProgress(100, data.message);
                    
                    // Espera um pouco para mostrar 100% e depois fecha
                    setTimeout(() => {
                        this.showProgressModal(false);
                        this.addSystemMessage(`✅ ${data.message}: ${newModel}`);
                    }, 800);
                    
                } else {
                    throw new Error(data.error || 'Erro desconhecido');
                }
            } catch (error) {
                console.error('Erro ao alterar modelo:', error);
                this.updateProgress(0, this.translations.error_loading_model || 'Erro ao carregar modelo');
                
                setTimeout(() => {
                    this.showProgressModal(false);
                    this.addSystemMessage(`❌ ${error.message}`);
                    this.elements.modelSelect.value = this.currentModel;
                }, 1500);
            } finally {
                this.isLoadingModel = false;
            }
        }
    }
    
    showProgressModal(show) {
        if (this.elements.progressModal) {
            this.elements.progressModal.style.display = show ? 'flex' : 'none';
        }
    }
    
    updateProgress(percent, text) {
        if (this.elements.progressBar) {
            this.elements.progressBar.style.width = percent + '%';
        }
        if (this.elements.progressText) {
            this.elements.progressText.textContent = text;
        }
    }
    
    updateModelBadge() {
        const badge = this.elements.currentModelBadge;
        badge.innerHTML = `<span>🤖</span><span>${this.currentModel}</span>`;
    }
    
    handleInput() {
        this.elements.textInput.style.height = 'auto';
        this.elements.textInput.style.height = Math.min(this.elements.textInput.scrollHeight, 200) + 'px';
        this.elements.sendBtn.disabled = this.elements.textInput.value.trim() === '' || this.isGenerating;
    }
    
    handleKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!this.elements.sendBtn.disabled) {
                this.sendMessage();
            }
        }
    }
    
    async sendMessage() {
        const message = this.elements.textInput.value.trim();
        if (message === '' || this.isGenerating) return;

        this.isGenerating = true;
        this.elements.sendBtn.disabled = true;
        
        this.addMessage('user', message);
        
        this.elements.textInput.value = '';
        this.elements.textInput.style.height = 'auto';
        
        this.showTypingIndicator(true);
        
        try {
            const response = await fetch(`${this.baseUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    model: this.currentModel,
                    history: this.conversationHistory,
                    language: this.currentLanguage
                })
            });
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = '';
            
            const messageElement = this.createMessageElement('assistant', '');
            this.elements.chatContainer.appendChild(messageElement);
            this.scrollToBottom();
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data && data !== '[DONE]') {
                            try {
                                const parsed = JSON.parse(data);
                                if (parsed.content) {
                                    assistantMessage += parsed.content;
                                    messageElement.querySelector('.bubble').textContent = assistantMessage;
                                    this.scrollToBottom();
                                }
                                if (parsed.done) {
                                    this.conversationHistory.push({
                                        role: 'assistant',
                                        content: assistantMessage
                                    });
                                    break;
                                }
                            } catch (e) {
                                console.warn('Erro ao parsear chunk:', e);
                            }
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('Erro ao enviar mensagem:', error);
            this.addSystemMessage(`❌ Erro: ${error.message}`);
        } finally {
            this.showTypingIndicator(false);
            this.isGenerating = false;
            this.elements.sendBtn.disabled = this.elements.textInput.value.trim() === '';
        }
    }
    
    createMessageElement(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-msg`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'avatar';
        avatarDiv.textContent = sender === 'user' ? 'U' : 'AI';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'bubble';
        bubbleDiv.textContent = content;
        
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        actionsDiv.innerHTML = `
            <button class="action-btn" onclick="app.copyMessage(this)">Copiar</button>
            <button class="action-btn" onclick="app.rateMessage(this, 'up')">👍</button>
            <button class="action-btn" onclick="app.rateMessage(this, 'down')">👎</button>
        `;
        
        contentDiv.appendChild(bubbleDiv);
        contentDiv.appendChild(actionsDiv);
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        return messageDiv;
    }
    
    addMessage(sender, content) {
        const messageElement = this.createMessageElement(sender, content);
        this.elements.chatContainer.appendChild(messageElement);
        
        const welcomeMessage = this.elements.chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        if (sender === 'user') {
            this.conversationHistory.push({ role: 'user', content: content });
        }
        
        this.scrollToBottom();
        return messageElement;
    }
    
    addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-msg';
        messageDiv.innerHTML = `
            <div class="avatar">!</div>
            <div class="message-content">
                <div class="bubble">${content}</div>
            </div>
        `;
        this.elements.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    