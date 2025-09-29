#!/usr/bin/env python3
import requests
import subprocess
import time
import os

def run_command(cmd, timeout=10):
    """Executa um comando e retorna o resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def diagnosticar_ollama():
    print("🩺 DIAGNÓSTICO COMPLETO DO OLLAMA")
    print("=" * 50)
    
    # 1. Verifica se o Ollama está instalado
    print("1. 📦 Verificando instalação do Ollama...")
    result = run_command("which ollama")
    if result['success']:
        print("   ✅ Ollama encontrado:", result['stdout'])
    else:
        print("   ❌ Ollama não encontrado no PATH")
        print("   💡 Instale com: curl -fsSL https://ollama.ai/install.sh | sh")
        return False
    
    # 2. Verifica versão
    print("2. 🔍 Verificando versão...")
    result = run_command("ollama --version")
    if result['success']:
        print("   ✅ Versão:", result['stdout'])
    else:
        print("   ❌ Não foi possível obter versão")
    
    # 3. Verifica processo
    print("3. 🔄 Verificando processos...")
    result = run_command("pgrep -f ollama")
    if result['success'] and result['stdout']:
        print("   ✅ Processos Ollama encontrados:", result['stdout'])
    else:
        print("   ❌ Nenhum processo Ollama encontrado")
        print("   💡 Execute: ollama serve")
    
    # 4. Verifica porta
    print("4. 🔌 Verificando porta 11434...")
    result = run_command("netstat -tuln | grep 11434 || ss -tuln | grep 11434")
    if result['success'] and '11434' in result['stdout']:
        print("   ✅ Porta 11434 está escutando")
    else:
        print("   ❌ Porta 11434 não está escutando")
    
    # 5. Testa API
    print("5. 🌐 Testando API...")
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"   ✅ API respondendo - {len(models)} modelos")
            for model in models:
                print(f"      - {model['name']}")
        else:
            print(f"   ❌ API retornou status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na API: {e}")
    
    # 6. Lista modelos via comando
    print("6. 📋 Listando modelos via comando...")
    result = run_command("ollama list", timeout=15)
    if result['success']:
        print("   ✅ Comando 'ollama list' executado:")
        print(result['stdout'])
    else:
        print("   ❌ Erro no comando 'ollama list':", result.get('stderr', result.get('error', 'Unknown')))
    
    # 7. Verifica permissões
    print("7. 🔒 Verificando permissões...")
    ollama_dir = os.path.expanduser("~/.ollama")
    if os.path.exists(ollama_dir):
        print(f"   ✅ Diretório Ollama existe: {ollama_dir}")
        stat = os.stat(ollama_dir)
        print(f"   👤 Dono: {stat.st_uid}, Permissões: {oct(stat.st_mode)[-3:]}")
    else:
        print(f"   ❌ Diretório Ollama não existe: {ollama_dir}")
    
    print("=" * 50)
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Se Ollama não está rodando: ollama serve")
    print("2. Se não há modelos: ollama pull llama3:8b-instruct-q4_K_M") 
    print("3. Se há erro de permissão: sudo chown -R $USER ~/.ollama")
    print("4. Reinicie o servidor Flask após corrigir problemas")

if __name__ == '__main__':
    diagnosticar_ollama()