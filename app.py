#!/usr/bin/env python3
# Copyright (C) 2024 Djalma Valois Filho
# 
# This file is part of ollama_gui.
# 
# Ollama_Gui is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Ollama_gui is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GitHub Deploy Assistant.  If not, see <https://www.gnu.org/licenses/>.

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import requests
import json
import time
import os
import subprocess
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ollamagui-secret-key-2024'
CORS(app)

OLLAMA_URL = "http://localhost:11434"
OLLAMA_LIBRARY_URL = "https://ollama.com/library"

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
        'download_model': 'Baixar Modelo',
        'available_models': 'Modelos Disponíveis',
        'download_started': 'Download iniciado',
        'download_complete': 'Download completo',
        'download_error': 'Erro no download',
        'search_models': 'Buscar Modelos',
        'popular_models': 'Modelos Populares',
        'new_models': 'Novos Modelos',
        'model_size': 'Tamanho',
        'model_pulls': 'Downloads',
        'install': 'Instalar',
        'installing': 'Instalando...',
        'installed': 'Instalado',
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
        'download_model': 'Download Model',
        'available_models': 'Available Models',
        'download_started': 'Download started',
        'download_complete': 'Download complete',
        'download_error': 'Download error',
        'search_models': 'Search Models',
        'popular_models': 'Popular Models',
        'new_models': 'New Models',
        'model_size': 'Size',
        'model_pulls': 'Pulls',
        'install': 'Install',
        'installing': 'Installing...',
        'installed': 'Installed',
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
        'download_model': 'Descargar Modelo',
        'available_models': 'Modelos Disponibles',
        'download_started': 'Descarga iniciada',
        'download_complete': 'Descarga completada',
        'download_error': 'Error en descarga',
        'search_models': 'Buscar Modelos',
        'popular_models': 'Modelos Populares',
        'new_models': 'Modelos Nuevos',
        'model_size': 'Tamaño',
        'model_pulls': 'Descargas',
        'install': 'Instalar',
        'installing': 'Instalando...',
        'installed': 'Instalado',
        'system_prompt': """Eres un asistente de IA útil e inteligente.
Responde de forma clara y precisa en el idioma del usuario."""
    }
}

# Cache para modelos da web
web_models_cache = {
    'data': [],
    'timestamp': 0,
    'cache_duration': 3600  # 1 hora em segundos
}

# Variável global para armazenar progresso dos downloads
download_progress = {}

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
    
    # Fallback final
    print("❌ Ollama não encontrado")
    return {
        'connected': False,
        'models': [],
        'method': 'fallback',
        'message': 'Ollama não está disponível'
    }

def fetch_models_from_web():
    """Busca modelos da web usando a API pública do Ollama"""
    try:
        # Verifica se temos cache válido
        current_time = time.time()
        if (web_models_cache['data'] and 
            current_time - web_models_cache['timestamp'] < web_models_cache['cache_duration']):
            print("📦 Retornando modelos do cache")
            return web_models_cache['data']
        
        print("🌐 Buscando modelos da web...")
        
        # Usa a API pública do Ollama para obter modelos
        response = requests.get('https://ollama.com/api/tags', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            for model_data in data.get('models', []):
                model = model_data.get('model', '')
                if model:
                    # Extrai informações do modelo
                    parts = model.split(':')
                    name = parts[0] if len(parts) > 0 else model
                    tag = parts[1] if len(parts) > 1 else 'latest'
                    
                    models.append({
                        'name': model,
                        'short_name': name,
                        'tag': tag,
                        'pulls': model_data.get('pulls', 0),
                        'size': model_data.get('size', 0),
                        'modified': model_data.get('modified_at', '')
                    })
            
            # Ordena por popularidade (pulls)
            models.sort(key=lambda x: x['pulls'], reverse=True)
            
            # Atualiza cache
            web_models_cache['data'] = models
            web_models_cache['timestamp'] = current_time
            
            print(f"✅ {len(models)} modelos encontrados na web")
            return models
        else:
            print(f"❌ Erro na API web: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao buscar modelos da web: {e}")
        return []

def get_popular_models_from_web():
    """Retorna os modelos mais populares da web"""
    all_models = fetch_models_from_web()
    
    # Filtra e categoriza modelos
    popular_models = []
    new_models = []
    code_models = []
    chat_models = []
    
    for model in all_models[:100]:  # Limita a 100 modelos
        model_name = model['name'].lower()
        
        # Categorização
        if any(keyword in model_name for keyword in ['coder', 'code', 'python']):
            code_models.append(model)
        elif any(keyword in model_name for keyword in ['chat', 'instruct']):
            chat_models.append(model)
        else:
            # Modelos mais recentes (baseado na data de modificação)
            if model['modified']:
                new_models.append(model)
            else:
                popular_models.append(model)
    
    # Limita cada categoria
    return {
        'popular': popular_models[:20],
        'new': new_models[:10],
        'code': code_models[:15],
        'chat': chat_models[:15]
    }

def download_model_thread(model_name, language='pt'):
    """Função para baixar modelo em thread separada"""
    try:
        print(f"📥 Iniciando download do modelo: {model_name}")
        download_progress[model_name] = {
            'status': 'downloading',
            'progress': 0,
            'message': get_translation('download_started', language)
        }
        
        # Executa o comando ollama pull
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Monitora o progresso
        for line in process.stdout:
            print(f"📦 {model_name}: {line.strip()}")
            # Parseia progresso se disponível
            if 'downloading' in line.lower() or 'pulling' in line.lower():
                download_progress[model_name]['progress'] = min(
                    download_progress[model_name]['progress'] + 5, 90
                )
            elif 'verifying' in line.lower():
                download_progress[model_name]['progress'] = 95
            elif 'success' in line.lower():
                download_progress[model_name]['progress'] = 100
        
        process.wait()
        
        if process.returncode == 0:
            download_progress[model_name] = {
                'status': 'completed',
                'progress': 100,
                'message': get_translation('download_complete', language)
            }
            print(f"✅ Download completo: {model_name}")
            
            # Limpa cache de modelos locais
            global web_models_cache
            web_models_cache['data'] = []
            
        else:
            download_progress[model_name] = {
                'status': 'error',
                'progress': 0,
                'message': get_translation('download_error', language)
            }
            print(f"❌ Erro no download: {model_name}")
            
    except Exception as e:
        download_progress[model_name] = {
            'status': 'error',
            'progress': 0,
            'message': f"{get_translation('download_error', language)}: {str(e)}"
        }
        print(f"❌ Erro no download thread: {e}")

def format_file_size(size_bytes):
    """Formata tamanho de arquivo para legibilidade"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/models')
def get_models():
    connection_info = test_ollama_connection()
    
    # Sempre retorna modelos, mesmo que seja fallback
    all_models = connection_info['models']
    
    print(f"📦 Retornando {len(all_models)} modelos (método: {connection_info['method']})")
    
    return jsonify({
        'models': all_models,
        'connected': connection_info['connected'],
        'message': connection_info['message'],
        'method': connection_info['method']
    })

@app.route('/api/web-models')
def get_web_models():
    """Retorna modelos disponíveis na web, categorizados"""
    try:
        categorized_models = get_popular_models_from_web()
        
        # Obtém modelos instalados localmente
        connection_info = test_ollama_connection()
        installed_models = connection_info['models'] if connection_info['connected'] else []
        
        return jsonify({
            'categories': categorized_models,
            'installed_models': installed_models,
            'total_models': sum(len(cat) for cat in categorized_models.values())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-models')
def search_models():
    """Busca modelos por termo"""
    try:
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify({'error': 'Termo de busca não fornecido'}), 400
        
        all_models = fetch_models_from_web()
        filtered_models = [
            model for model in all_models 
            if query in model['name'].lower() or query in model['short_name'].lower()
        ]
        
        # Obtém modelos instalados localmente
        connection_info = test_ollama_connection()
        installed_models = connection_info['models'] if connection_info['connected'] else []
        
        return jsonify({
            'results': filtered_models[:50],  # Limita resultados
            'installed_models': installed_models,
            'count': len(filtered_models)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-model', methods=['POST'])
def download_model():
    """Inicia o download de um modelo"""
    try:
        data = request.json
        model_name = data.get('model')
        language = data.get('language', 'pt')
        
        if not model_name:
            return jsonify({'error': 'Nome do modelo não fornecido'}), 400
        
        # Verifica se o modelo já está instalado
        connection_info = test_ollama_connection()
        if model_name in connection_info['models']:
            return jsonify({'error': 'Modelo já está instalado'}), 400
        
        # Verifica se já está baixando
        if model_name in download_progress and download_progress[model_name]['status'] == 'downloading':
            return jsonify({'error': 'Download já em andamento'}), 400
        
        # Inicia download em thread separada
        thread = threading.Thread(
            target=download_model_thread,
            args=(model_name, language)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': get_translation('download_started', language),
            'model': model_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-progress/<model_name>')
def get_download_progress(model_name):
    """Retorna o progresso do download de um modelo"""
    progress = download_progress.get(model_name, {
        'status': 'unknown',
        'progress': 0,
        'message': 'Download não encontrado'
    })
    
    return jsonify(progress)

# ... (mantenha as outras rotas como chat, health, translations, etc.)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', 'Hello')
        model = data.get('model', 'llama3:8b-instruct')
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

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 OllamaGUI - Interface Completa com Loja de Modelos")
    print("=" * 60)
    
    # Testa conexão na inicialização
    connection_info = test_ollama_connection()
    
    if connection_info['connected']:
        print("✅ Ollama conectado com sucesso!")
        print(f"📦 Modelos disponíveis: {len(connection_info['models'])}")
        for model in connection_info['models'][:5]:
            print(f"   - {model}")
        if len(connection_info['models']) > 5:
            print(f"   ... e mais {len(connection_info['models']) - 5} modelos")
    else:
        print("⚠️  Ollama não está disponível")
        print("💡 Para conectar ao Ollama, execute em outro terminal:")
        print("   ollama serve")
    
    print("📡 Servidor: http://localhost:5000")
    print("🔗 Ollama: http://localhost:11434")
    print("🌐 Idiomas: pt, en, es")
    print("🛒 Loja de modelos online: ✅ Ativa")
    print("🔍 Busca por modelos: ✅ Ativa")
    print("📊 Categorização: Popular, Novos, Code, Chat")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
