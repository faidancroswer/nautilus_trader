#!/usr/bin/env python3
"""
Seletor de modelo Ollama para trading
Escolhe automaticamente o melhor modelo disponível
"""

import requests
import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Seletor inteligente de modelo Ollama para trading
    """
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        
        # Modelos em ordem de preferência (velocidade vs qualidade)
        self.preferred_models = [
            {
                "name": "llama3:8b",
                "speed": "fast",
                "quality": "high",
                "timeout": 10,
                "description": "Melhor equilíbrio velocidade/qualidade"
            },
            {
                "name": "llama3.2:1b", 
                "speed": "very_fast",
                "quality": "good",
                "timeout": 5,
                "description": "Muito rápido, boa qualidade"
            },
            {
                "name": "phi3:latest",
                "speed": "slow",
                "quality": "very_high",
                "timeout": 30,
                "description": "Alta qualidade, mais lento"
            },
            {
                "name": "llama3:latest",
                "speed": "medium",
                "quality": "very_high", 
                "timeout": 15,
                "description": "Boa qualidade, velocidade média"
            }
        ]
    
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos disponíveis no Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            else:
                logger.error(f"Erro ao obter modelos: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erro na conexão com Ollama: {e}")
            return []
    
    def test_model_speed(self, model_name: str, timeout: int = 15) -> Optional[float]:
        """Testa velocidade de resposta de um modelo"""
        try:
            test_prompt = "XAUUSD BUY"
            payload = {
                "model": model_name,
                "prompt": test_prompt,
                "stream": False,
                "temperature": 0.1,
                "max_tokens": 5
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=timeout
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"Modelo {model_name}: {response_time:.1f}s")
                return response_time
            else:
                logger.warning(f"Modelo {model_name}: Erro {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Modelo {model_name}: Timeout ({timeout}s)")
            return None
        except Exception as e:
            logger.error(f"Modelo {model_name}: Erro {e}")
            return None
    
    def select_best_model(self, priority: str = "speed") -> Optional[Dict]:
        """
        Seleciona o melhor modelo disponível
        
        Args:
            priority: "speed" para velocidade, "quality" para qualidade
        """
        available_models = self.get_available_models()
        if not available_models:
            logger.error("Nenhum modelo disponível no Ollama")
            return None
        
        logger.info(f"Modelos disponíveis: {available_models}")
        
        # Filtrar modelos preferidos que estão disponíveis
        available_preferred = []
        for model_info in self.preferred_models:
            if model_info["name"] in available_models:
                available_preferred.append(model_info)
        
        if not available_preferred:
            logger.error("Nenhum modelo preferido disponível")
            return None
        
        # Ordenar por prioridade
        if priority == "speed":
            # Ordenar por velocidade (timeout menor = mais rápido)
            available_preferred.sort(key=lambda x: x["timeout"])
        else:  # quality
            # Manter ordem original (qualidade)
            pass
        
        # Testar modelos em ordem de preferência
        for model_info in available_preferred:
            model_name = model_info["name"]
            timeout = model_info["timeout"]
            
            logger.info(f"Testando {model_name}...")
            response_time = self.test_model_speed(model_name, timeout)
            
            if response_time is not None:
                logger.info(f"✓ Modelo selecionado: {model_name}")
                logger.info(f"  Velocidade: {response_time:.1f}s")
                logger.info(f"  Descrição: {model_info['description']}")
                return model_info
        
        logger.error("Nenhum modelo funcionou corretamente")
        return None
    
    def get_fast_model(self) -> str:
        """Retorna o modelo mais rápido disponível"""
        model_info = self.select_best_model("speed")
        return model_info["name"] if model_info else "llama3:8b"
    
    def get_quality_model(self) -> str:
        """Retorna o modelo de melhor qualidade disponível"""
        model_info = self.select_best_model("quality")
        return model_info["name"] if model_info else "llama3:8b"
    
    def create_optimized_config(self, model_name: str) -> Dict:
        """Cria configuração otimizada para o modelo"""
        model_info = next((m for m in self.preferred_models if m["name"] == model_name), None)
        
        if not model_info:
            # Configuração padrão
            return {
                "model": model_name,
                "timeout": 15,
                "temperature": 0.2,
                "max_tokens": 50
            }
        
        # Configuração específica do modelo
        if "1b" in model_name:  # Modelo pequeno
            return {
                "model": model_name,
                "timeout": model_info["timeout"],
                "temperature": 0.1,  # Mais determinístico
                "max_tokens": 30     # Menos tokens
            }
        elif "8b" in model_name:  # Modelo médio
            return {
                "model": model_name,
                "timeout": model_info["timeout"],
                "temperature": 0.2,
                "max_tokens": 50
            }
        else:  # Modelo grande
            return {
                "model": model_name,
                "timeout": model_info["timeout"],
                "temperature": 0.3,
                "max_tokens": 100
            }


def auto_select_trading_model(priority: str = "speed") -> Dict:
    """
    Função utilitária para seleção automática de modelo
    
    Args:
        priority: "speed" ou "quality"
    
    Returns:
        Configuração do modelo selecionado
    """
    selector = ModelSelector()
    model_info = selector.select_best_model(priority)
    
    if model_info:
        config = selector.create_optimized_config(model_info["name"])
        logger.info(f"Modelo selecionado automaticamente: {model_info['name']}")
        return config
    else:
        # Fallback para configuração padrão
        logger.warning("Usando configuração padrão")
        return {
            "model": "llama3:8b",
            "timeout": 15,
            "temperature": 0.2,
            "max_tokens": 50
        }


def main():
    """Teste do seletor de modelo"""
    logging.basicConfig(level=logging.INFO)
    
    print("=== SELETOR DE MODELO OLLAMA ===")
    
    selector = ModelSelector()
    
    # Testar seleção por velocidade
    print("\n1. Seleção por VELOCIDADE:")
    speed_model = selector.select_best_model("speed")
    if speed_model:
        print(f"   Modelo: {speed_model['name']}")
        print(f"   Velocidade: {speed_model['speed']}")
        print(f"   Timeout: {speed_model['timeout']}s")
    
    # Testar seleção por qualidade
    print("\n2. Seleção por QUALIDADE:")
    quality_model = selector.select_best_model("quality")
    if quality_model:
        print(f"   Modelo: {quality_model['name']}")
        print(f"   Qualidade: {quality_model['quality']}")
        print(f"   Timeout: {quality_model['timeout']}s")
    
    # Configuração automática
    print("\n3. Configuração AUTOMÁTICA:")
    auto_config = auto_select_trading_model("speed")
    print(f"   Configuração: {auto_config}")


if __name__ == "__main__":
    main()
