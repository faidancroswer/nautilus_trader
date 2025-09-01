#!/usr/bin/env python3
"""
Configuração otimizada do Ollama para negociações rápidas
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OllamaConfig:
    """
    Configuração otimizada do Ollama para trading de alta frequência
    """
    
    def __init__(self):
        # Configurações básicas do Ollama
        self.host = "localhost"
        self.port = 11434
        self.model = "phi3:latest"
        
        # Configurações de performance otimizadas
        self.timeout = 10  # Timeout reduzido para respostas rápidas
        self.max_retries = 2  # Menos tentativas para velocidade
        self.temperature = 0.2  # Temperatura baixa para consistência
        self.top_p = 0.8
        self.max_tokens = 50  # Tokens reduzidos para respostas rápidas
        
        # Configurações de cache
        self.enable_cache = True
        self.cache_duration = 30  # segundos
        self.max_cache_size = 20
        
        # Configurações de prompt otimizado
        self.use_simplified_prompts = True
        self.prompt_compression = True
        
        # Configurações de conexão
        self.connection_pool_size = 5
        self.keep_alive = True
        
    def get_api_url(self) -> str:
        """Retorna a URL da API do Ollama"""
        return f"http://{self.host}:{self.port}/api/generate"
    
    def get_optimized_payload(self, prompt: str) -> Dict[str, Any]:
        """
        Retorna payload otimizado para requisições rápidas
        """
        return {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repeat_penalty": 1.1,
                "stop": ["DECISION:", "\n\n"]
            }
        }
    
    def optimize_for_speed(self):
        """
        Aplica configurações para máxima velocidade
        """
        self.timeout = 8
        self.max_retries = 1
        self.temperature = 0.1
        self.max_tokens = 30
        self.cache_duration = 60
        logger.info("Ollama configurado para máxima velocidade")
    
    def optimize_for_accuracy(self):
        """
        Aplica configurações para máxima precisão
        """
        self.timeout = 20
        self.max_retries = 3
        self.temperature = 0.3
        self.max_tokens = 100
        self.cache_duration = 15
        logger.info("Ollama configurado para máxima precisão")
    
    def get_system_prompt(self) -> str:
        """
        Retorna prompt de sistema otimizado
        """
        return """You are a high-frequency forex trading AI. Respond ONLY with trading decisions.
Rules:
- OPEN_BUY: Strong bullish signals
- OPEN_SELL: Strong bearish signals  
- CLOSE_POSITION: Exit signals
- HOLD: No clear opportunity
Respond with ONLY the decision word."""

    def validate_model_availability(self) -> bool:
        """
        Verifica se o modelo está disponível
        """
        try:
            import requests
            response = requests.get(f"http://{self.host}:{self.port}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for model in models:
                    if model.get('name', '').startswith(self.model.split(':')[0]):
                        logger.info(f"Modelo {self.model} disponível")
                        return True
                logger.warning(f"Modelo {self.model} não encontrado")
                return False
            else:
                logger.error(f"Erro ao verificar modelos: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erro na validação do modelo: {e}")
            return False
    
    def warm_up_model(self) -> bool:
        """
        Aquece o modelo para respostas mais rápidas
        """
        try:
            import requests
            payload = self.get_optimized_payload("Ready for trading")
            response = requests.post(
                self.get_api_url(), 
                json=payload, 
                timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info("Modelo aquecido com sucesso")
                return True
            else:
                logger.warning(f"Falha no aquecimento: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erro no aquecimento do modelo: {e}")
            return False
    
    def get_config_dict(self) -> Dict[str, Any]:
        """
        Retorna configuração como dicionário
        """
        return {
            "host": self.host,
            "port": self.port,
            "model": self.model,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "enable_cache": self.enable_cache,
            "cache_duration": self.cache_duration,
            "max_cache_size": self.max_cache_size
        }
    
    def save_config(self, filepath: str = "ollama_trading_config.json"):
        """
        Salva configuração em arquivo JSON
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.get_config_dict(), f, indent=2)
            logger.info(f"Configuração salva em {filepath}")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    def load_config(self, filepath: str = "ollama_trading_config.json"):
        """
        Carrega configuração de arquivo JSON
        """
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    config = json.load(f)
                
                for key, value in config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                logger.info(f"Configuração carregada de {filepath}")
            else:
                logger.info(f"Arquivo {filepath} não encontrado, usando configuração padrão")
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")


# Instância global de configuração
ollama_config = OllamaConfig()

# Configurações pré-definidas
SPEED_CONFIG = {
    "timeout": 8,
    "max_retries": 1,
    "temperature": 0.1,
    "max_tokens": 30,
    "cache_duration": 60
}

ACCURACY_CONFIG = {
    "timeout": 20,
    "max_retries": 3,
    "temperature": 0.3,
    "max_tokens": 100,
    "cache_duration": 15
}

BALANCED_CONFIG = {
    "timeout": 12,
    "max_retries": 2,
    "temperature": 0.2,
    "max_tokens": 50,
    "cache_duration": 30
}


def setup_ollama_for_trading(mode: str = "balanced") -> OllamaConfig:
    """
    Configura Ollama para trading com modo específico
    
    Args:
        mode: "speed", "accuracy", ou "balanced"
    
    Returns:
        OllamaConfig configurado
    """
    config = OllamaConfig()
    
    if mode == "speed":
        config.optimize_for_speed()
    elif mode == "accuracy":
        config.optimize_for_accuracy()
    else:  # balanced
        pass  # usa configuração padrão
    
    # Valida e aquece o modelo
    if config.validate_model_availability():
        config.warm_up_model()
    else:
        logger.error("Modelo não disponível - verifique se o Ollama está rodando")
    
    return config


if __name__ == "__main__":
    # Teste da configuração
    config = setup_ollama_for_trading("speed")
    config.save_config()
    print("Configuração do Ollama criada com sucesso!")
