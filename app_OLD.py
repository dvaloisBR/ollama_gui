#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import requests
import json
import time
import os
import subprocess
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ollamagui-secret-key-2024'
CORS(app)

OLLAMA_URL = "http://localhost:11434"

# Sistema de Internacionalização
LANGUAGES = {
    'pt': {
        'app_name': 'OllamaGUI',
        'welcome': 'Bem-vindo ao OllamaGUI',
        'welcome_message': 'Converse com modelos de IA localmente',
        'type_message': 'Digite sua mensagem...',
        'send': 'Enviar',
        'typing': 'Digitando...',
        'select_model': 'Selecionar Modelo',
        'select_language': 'Selecionar Idioma',
        'new_chat': 'Nova Conversa',
        'clear_chat': 'Limpar Chat',
        'export_chat': 'Exportar',
        'settings': 'Configurações',
        'theme': 'Tema',
        'light': 'Claro',
        'dark': 'Escuro',
        'auto': 'Automático',
        'connection_status': 'Status da Conexão',
        'connected': 'Conectado',
        'disconnected': 'Desconectado',
        'loading_models': 'Carregando modelos...',
        'model_loaded': 'Modelo carregado',
        'error_loading': 'Erro ao carregar',
        'system_prompt': """Você é um assistente de IA útil e inteligente. 
Responda de forma clara e precisa no idioma do usuário."""
    },
    'en': {
        'app_name': 'OllamaGUI',
        'welcome': 'Welcome to OllamaGUI',
        'welcome_message': 'Chat with local AI models',
        'type_message': 'Type your message...',
        'send': 'Send',
        'typing': 'Typing...',
        'select_model': 'Select Model',
        'select_language': 'Select Language',
        'new_chat': 'New Chat',
        'clear_chat': 'Clear Chat',
        'export_chat': 'Export',
        'settings': 'Settings',
        'theme': 'Theme',
        'light': 'Light',
        'dark': 'Dark',
        'auto': 'Auto',
        'connection_status': 'Connection Status',
        'connected': 'Connected',
        'disconnected': 'Disconnected',
        'loading_models': 'Loading models...',
        'model_loaded': 'Model loaded',
        'error_loading': 'Error loading',
        'system_prompt': """You are a helpful and intelligent AI assistant.
Respond clearly and accurately in the user's language."""
    },
    'es': {
        'app_name': 'OllamaGUI',
        'welcome': 'Bienvenido a OllamaGUI',
        'welcome_message': 'Chatea con modelos de IA locales',
        'type_message': 'Escribe tu mensaje...',
        'send': 'Enviar',
        'typing': 'Escribiendo...',
        'select_model': 'Seleccionar Modelo',
        'select_language': 'Seleccionar Idioma',
        'new_chat': 'Nueva Conversación',
        'clear_chat': 'Limpiar Chat',
        'export_chat': 'Exportar',
        'settings': 'Configuración',
        'theme': 'Tema',
        'light': 'Claro',
        'dark': 'Oscuro',
        'auto': 'Automático',
        'connection_status': 'Estado de Conexión',
        'connected': 'Conectado',
        'disconnected': 'Desconectado',
        'loading_models': 'Cargando modelos...',
        'model_loaded': 'Modelo cargado',
        'error_loading': 'Error al cargar',
        'system_prompt': """Eres un asistente de IA útil e inteligente.
Responde de forma clara y precisa en el idioma del usuario."""
    }
}

# Modelos disponíveis (fallback se API não responder)
DEFAULT_MODELS = [
    'llama3:8b-instruct-q4_K_M',
    'llama3:8b-instruct-q4_0', 
    'deepseek-coder:latest',
    'mistral:7b-instruct-q4_K_M',
    'llama2:latest',
    'codellama:latest'
]

def get_translation(key, language='pt'):
    return LANGUAGES.get(language, LANGUAGES['pt']).get(key, key)

def get_ollama_models_direct():
    """Tenta obter modelos diretamente via comando ollama list"""
    try:
        print("🔍 Tentando obter modelos via comando ollama...")
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            models = []
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Pula o cabeçalho
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1:
                        model_name = parts[0]
                        if ':' in model_name:  # Garante que tem tag
                            models.append(model_name)
            print(f"✅ {len(models)} modelos encontrados via comando")
            return models
        else:
            print(f"❌ Comando falhou: {result.stderr}")
            return []
    except Exception as e:
        print(f"❌ Erro no comando ollama: {e}")
        return []

def test_ollama_connection():
    """Testa a conexão com o Ollama de múltiplas formas"""
    print("🔍 Testando conexão com Ollama...")
    
    # Método 1: API REST
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            print(f"✅ API REST - {len(models)} modelos")
            return {
                'connected': True,
                'models': models,
                'method': 'api',
                'message': f'Ollama conectado - {len(models)} modelos disponíveis'
            }
    except requests.exceptions.ConnectionError:
        print("❌ API REST: ConnectionError")
    except requests.exceptions.Timeout:
        print("❌ API REST: Timeout")
    except Exception as e:
        print(f"❌ API REST: {e}")
    
    # Método 2: Comando direto
    direct_models = get_ollama_models_direct()
    if direct_models:
        print(f"✅ Comando direto - {len(direct_models)} modelos")
        return {
            'connected': True,
            'models': direct_models,
            'method': 'command',
            'message': f'Ollama conectado - {len(direct_models)} modelos disponíveis'
        }
    
    # Método 3: Verifica se processo está rodando
    try:
        result = subprocess.run(['pgrep', '-f', 'ollama'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Processo Ollama está rodando, mas API não responde")
            return {
                'connected': False,
                'models': DEFAULT_MODELS,  # Fallback para permitir uso
                'method': 'process',
                'message': 'Ollama está rodando mas API não responde. Use modelos padrão.'
            }
    except:
        pass
    
    # Fallback final
    print("❌ Ollama não encontrado, usando modelos padrão")
    return {
        'connected': False,
        'models': DEFAULT_MODELS,
        'method': 'fallback',
        'message': 'Ollama não está disponível. Usando modelos padrão para demonstração.'
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/models')
def get_models():
    connection_info = test_ollama_connection()
    
    # Sempre retorna modelos, mesmo que seja fallback
    all_models = connection_info['models']
    
    # Ordena modelos: primeiro os que existem em DEFAULT_MODELS
    models = []
    for default_model in DEFAULT_MODELS:
        if default_model in all_models:
            models.append(default_model)
    
    # Adiciona outros modelos
    for model in all_models:
        if model not in models:
            models.append(model)
    
    print(f"📦 Retornando {len(models)} modelos (método: {connection_info['method']})")
    
    return jsonify({
        'models': models,
        'connected': connection_info['connected'],
        'message': connection_info['message'],
        'method': connection_info['method']
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', 'Hello')
        model = data.get('model', DEFAULT_MODELS[0])
        language = data.get('language', 'pt')
        
        print(f"💬 [{language}] Tentando enviar para {model}: {message}")
        
        # Verifica se podemos usar o Ollama
        connection_info = test_ollama_connection()
        
        if not connection_info['connected']:
            return jsonify({
                'response': f"⚠️ Ollama não está disponível. \n\nMensagem que seria enviada para {model}: {message}\n\nPara usar modelos reais, execute: ollama serve"
            })
        
        # System prompt com idioma
        system_prompt = get_translation('system_prompt', language)
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "stream": False
        }
        
        start_time = time.time()
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        end_time = time.time()
        
        print(f"⏱️  Tempo de resposta: {end_time - start_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            response_text = data['message']['content']
            print(f"✅ Resposta recebida de {model}")
            return jsonify({'response': response_text})
        else:
            error_msg = f'Erro do Ollama: {response.status_code}'
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                pass
            return jsonify({'error': error_msg}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout - Modelo muito lento'}), 408
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Ollama não está rodando'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    connection_info = test_ollama_connection()
    
    return jsonify({
        'status': 'healthy' if connection_info['connected'] else 'error',
        'ollama': 'connected' if connection_info['connected'] else 'disconnected',
        'message': connection_info['message'],
        'method': connection_info['method'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/translations/<lang>')
def get_translations(lang):
    translations = LANGUAGES.get(lang, LANGUAGES['pt'])
    return jsonify({
        'language': lang,
        'translations': translations
    })

@app.route('/api/debug/connection')
def debug_connection():
    """Endpoint para debug da conexão"""
    return jsonify(test_ollama_connection())

@app.route('/api/install-model', methods=['POST'])
def install_model():
    """Endpoint para instalar um modelo"""
    try:
        data = request.json
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({'error': 'Nome do modelo não fornecido'}), 400
        
        print(f"📥 Instalando modelo: {model_name}")
        
        # Executa o comando ollama pull
        result = subprocess.run(
            ['ollama', 'pull', model_name], 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Modelo {model_name} instalado com sucesso!'
            })
        else:
            return jsonify({
                'error': f'Erro ao instalar modelo: {result.stderr}'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout na instalação do modelo'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 OllamaGUI - Interface Completa")
    print("=" * 60)
    
    # Testa conexão na inicialização
    connection_info = test_ollama_connection()
    
    if connection_info['connected']:
        print("✅ Ollama conectado com sucesso!")
        print(f"📦 Modelos disponíveis: {len(connection_info['models'])}")
        for model in connection_info['models'][:5]:  # Mostra apenas os 5 primeiros
            print(f"   - {model}")
        if len(connection_info['models']) > 5:
            print(f"   ... e mais {len(connection_info['models']) - 5} modelos")
    else:
        print("⚠️  Ollama não está disponível, usando modo fallback")
        print("💡 Para conectar ao Ollama, execute em outro terminal:")
        print("   ollama serve")
        print("💡 Para instalar um modelo:")
        print("   ollama pull llama3:8b-instruct-q4_K_M")
    
    print("📡 Servidor: http://localhost:5000")
    print("🔗 Ollama: http://localhost:11434")
    print("🌐 Idiomas: pt, en, es")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)