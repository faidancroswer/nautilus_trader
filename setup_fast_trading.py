#!/usr/bin/env python3
"""
Script de configuração para o sistema de trading rápido com Ollama
"""

import os
import sys
import subprocess
import logging
import time
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Verifica se a versão do Python é adequada"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 ou superior é necessário")
        return False
    logger.info(f"Python {sys.version} - OK")
    return True


def check_required_packages():
    """Verifica e instala pacotes necessários"""
    required_packages = [
        'MetaTrader5',
        'pandas',
        'numpy',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"Pacote {package} - OK")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Pacote {package} - FALTANDO")
    
    if missing_packages:
        logger.info("Instalando pacotes faltantes...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"Pacote {package} instalado com sucesso")
            except subprocess.CalledProcessError:
                logger.error(f"Falha ao instalar {package}")
                return False
    
    return True


def check_ollama_installation():
    """Verifica se o Ollama está instalado e rodando"""
    try:
        # Verificar se o comando ollama existe
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Ollama instalado - {result.stdout.strip()}")
        else:
            logger.error("Ollama não está instalado")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.error("Ollama não encontrado no sistema")
        return False
    
    # Verificar se o serviço está rodando
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("Serviço Ollama está rodando - OK")
            return True
        else:
            logger.warning("Serviço Ollama não está respondendo")
            return False
    except requests.exceptions.RequestException:
        logger.warning("Serviço Ollama não está rodando")
        return False


def start_ollama_service():
    """Inicia o serviço Ollama se não estiver rodando"""
    logger.info("Tentando iniciar o serviço Ollama...")
    try:
        # No Windows, o Ollama geralmente roda como serviço
        if os.name == 'nt':
            subprocess.Popen(['ollama', 'serve'], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(['ollama', 'serve'])
        
        # Aguardar o serviço iniciar
        for i in range(10):
            time.sleep(2)
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    logger.info("Serviço Ollama iniciado com sucesso")
                    return True
            except requests.exceptions.RequestException:
                continue
        
        logger.error("Falha ao iniciar o serviço Ollama")
        return False
        
    except Exception as e:
        logger.error(f"Erro ao iniciar Ollama: {e}")
        return False


def check_ollama_model():
    """Verifica se o modelo necessário está disponível"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            
            # Procurar por modelos phi3
            available_models = [model['name'] for model in models]
            logger.info(f"Modelos disponíveis: {available_models}")

            # Verificar se temos phi3:latest ou similar
            for model in available_models:
                if 'phi3' in model.lower():
                    logger.info(f"Modelo Phi3 encontrado: {model}")
                    return True

            logger.warning("Modelo Phi3 não encontrado")
            return False
        else:
            logger.error("Falha ao verificar modelos")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao verificar modelos: {e}")
        return False


def download_phi3_model():
    """Baixa o modelo Phi3 se necessário"""
    logger.info("Baixando modelo phi3:latest...")
    try:
        process = subprocess.Popen(
            ['ollama', 'pull', 'phi3:latest'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Mostrar progresso
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"Download: {output.strip()}")
        
        if process.returncode == 0:
            logger.info("Modelo phi3:latest baixado com sucesso")
            return True
        else:
            logger.error("Falha ao baixar modelo")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao baixar modelo: {e}")
        return False


def check_mt5_installation():
    """Verifica se o MetaTrader 5 está instalado"""
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            logger.info("MetaTrader 5 - OK")
            mt5.shutdown()
            return True
        else:
            logger.error("MetaTrader 5 não pode ser inicializado")
            return False
    except ImportError:
        logger.error("MetaTrader 5 não está instalado")
        return False


def create_config_files():
    """Cria arquivos de configuração necessários"""
    logger.info("Criando arquivos de configuração...")
    
    # Criar diretório de logs se não existir
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Criar configuração do Ollama
    try:
        from ollama_config import setup_ollama_for_trading
        config = setup_ollama_for_trading("speed")
        config.save_config("ollama_trading_config.json")
        logger.info("Configuração do Ollama criada")
    except Exception as e:
        logger.error(f"Erro ao criar configuração do Ollama: {e}")
        return False
    
    return True


def test_system():
    """Testa o sistema completo"""
    logger.info("Testando sistema completo...")
    
    try:
        # Testar conexão com Ollama
        from ollama_config import setup_ollama_for_trading
        config = setup_ollama_for_trading("speed")
        
        if not config.validate_model_availability():
            logger.error("Modelo não disponível")
            return False
        
        if not config.warm_up_model():
            logger.error("Falha no aquecimento do modelo")
            return False
        
        logger.info("Sistema testado com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro no teste do sistema: {e}")
        return False


def main():
    """Função principal de configuração"""
    logger.info("=== CONFIGURAÇÃO DO SISTEMA DE TRADING RÁPIDO ===")
    
    # Verificações básicas
    if not check_python_version():
        return False
    
    if not check_required_packages():
        return False
    
    if not check_mt5_installation():
        logger.error("Por favor, instale o MetaTrader 5 primeiro")
        return False
    
    # Configurar Ollama
    if not check_ollama_installation():
        logger.error("Por favor, instale o Ollama primeiro")
        logger.info("Baixe em: https://ollama.ai/download")
        return False
    
    # Iniciar serviço se necessário
    if not check_ollama_installation():
        if not start_ollama_service():
            return False
    
    # Verificar/baixar modelo
    if not check_ollama_model():
        logger.info("Modelo Phi3 não encontrado, iniciando download...")
        if not download_phi3_model():
            return False
    
    # Criar arquivos de configuração
    if not create_config_files():
        return False
    
    # Testar sistema
    if not test_system():
        return False
    
    logger.info("=== CONFIGURAÇÃO CONCLUÍDA COM SUCESSO ===")
    logger.info("Para iniciar o trading, execute: python fast_ai_trading.py")
    logger.info("Ou execute: python advanced_ai_alligator.py")
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Configuração falhou. Verifique os erros acima.")
        sys.exit(1)
    else:
        logger.info("Sistema pronto para uso!")
