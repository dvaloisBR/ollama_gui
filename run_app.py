#!/usr/bin/env python3
import os
import sys
import subprocess
import time

def check_ollama():
    """Verifica se o Ollama está rodando"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✅ Ollama está rodando")
            return True
        else:
            print("❌ Ollama não está respondendo")
            return False
    except:
        print("❌ Ollama não está rodando")
        return False

def start_flask():
    """Inicia o Flask"""
    print("🚀 Iniciando Flask...")
    
    # Define o ambiente
    env = os.environ.copy()
    env['FLASK_APP'] = 'app.py'
    env['FLASK_ENV'] = 'development'
    
    # Inicia o Flask
    process = subprocess.Popen([
        sys.executable, 'app.py'
    ], env=env)
    
    # Aguarda um pouco para o Flask iniciar
    time.sleep(3)
    
    # Verifica se está rodando
    try:
        import requests
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            print("✅ Flask está rodando em http://localhost:5000")
            return process
        else:
            print("❌ Flask não está respondendo")
            return None
    except:
        print("❌ Flask não iniciou corretamente")
        return None

def main():
    print("=" * 50)
    print("🤖 Ollama Web Chat - Inicializador")
    print("=" * 50)
    
    # Verifica Ollama
    if not check_ollama():
        print("💡 Execute: ollama serve")
        return
    
    # Inicia Flask
    flask_process = start_flask()
    if not flask_process:
        return
    
    print("🎉 Tudo pronto! Acesse: http://localhost:5000")
    print("⏹️  Pressione Ctrl+C para parar")
    
    try:
        # Mantém o script rodando
        flask_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Parando Flask...")
        flask_process.terminate()

if __name__ == '__main__':
    main()