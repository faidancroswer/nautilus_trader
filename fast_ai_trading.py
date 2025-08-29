#!/usr/bin/env python3
"""
Sistema de Trading AI Otimizado para Velocidade com Ollama
Configurado para conta real FBS
"""

import logging
import time
import sys
import json
import requests
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from ollama_config import setup_ollama_for_trading, OllamaConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fast_ai_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FastTechnicalAnalyzer:
    """
    Analisador técnico otimizado para velocidade
    """
    
    @staticmethod
    def calculate_alligator_fast(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Cálculo rápido do Alligator
        """
        close = df['close']
        
        # Alligator lines com cálculo otimizado
        jaw = close.rolling(13).mean().shift(8)
        teeth = close.rolling(8).mean().shift(5)
        lips = close.rolling(5).mean().shift(3)
        
        current_price = close.iloc[-1]
        last_jaw = jaw.iloc[-1] if not pd.isna(jaw.iloc[-1]) else current_price
        last_teeth = teeth.iloc[-1] if not pd.isna(teeth.iloc[-1]) else current_price
        last_lips = lips.iloc[-1] if not pd.isna(lips.iloc[-1]) else current_price
        
        # Determinar alinhamento rapidamente
        if current_price > last_lips > last_teeth > last_jaw:
            alignment = "bullish"
        elif current_price < last_lips < last_teeth < last_jaw:
            alignment = "bearish"
        else:
            alignment = "neutral"
        
        return {
            "jaw": float(last_jaw),
            "teeth": float(last_teeth),
            "lips": float(last_lips),
            "alignment": alignment,
            "strength": abs(current_price - last_jaw) / current_price * 100
        }
    
    @staticmethod
    def calculate_fast_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Cálculo rápido de indicadores essenciais
        """
        close = df['close']
        high = df['high']
        low = df['low']
        
        # RSI rápido (período menor para mais sensibilidade)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(10).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(10).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD simplificado
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        
        # Volatilidade (ATR simplificado)
        tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
        atr = tr.rolling(10).mean()
        
        return {
            "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
            "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0,
            "volatility": float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.001,
            "price_change": float((close.iloc[-1] - close.iloc[-10]) / close.iloc[-10] * 100)
        }


class FastOllamaAgent:
    """
    Agente Ollama otimizado para decisões rápidas
    """
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.url = config.get_api_url()
        self.cache = {}
        self.last_decision_time = 0
        
    def get_fast_decision(self, analysis: Dict[str, Any]) -> str:
        """
        Decisão rápida com cache inteligente
        """
        try:
            # Cache baseado em condições de mercado
            cache_key = self._get_cache_key(analysis)
            current_time = time.time()
            
            # Usar cache se disponível e recente
            if (cache_key in self.cache and 
                current_time - self.cache[cache_key]['time'] < self.config.cache_duration):
                logger.info(f"Usando decisão em cache: {self.cache[cache_key]['decision']}")
                return self.cache[cache_key]['decision']
            
            # Gerar prompt ultra-compacto
            prompt = self._generate_ultra_fast_prompt(analysis)
            
            # Fazer requisição otimizada
            decision = self._make_fast_request(prompt)
            
            # Armazenar no cache
            self.cache[cache_key] = {
                'decision': decision,
                'time': current_time
            }
            
            # Limpar cache antigo
            self._clean_cache()
            
            return decision
            
        except Exception as e:
            logger.error(f"Erro na decisão rápida: {e}")
            return "HOLD"
    
    def _get_cache_key(self, analysis: Dict[str, Any]) -> str:
        """Gera chave de cache baseada em condições críticas"""
        alligator = analysis['alligator']
        indicators = analysis['indicators']
        
        return f"{alligator['alignment']}_{int(indicators['rsi']/10)}_{int(analysis['current_price']*10000)}"
    
    def _generate_ultra_fast_prompt(self, analysis: Dict[str, Any]) -> str:
        """
        Prompt ultra-compacto para respostas rápidas
        """
        alligator = analysis['alligator']
        indicators = analysis['indicators']
        
        return f"""EURUSD {analysis['current_price']:.5f}
ALG:{alligator['alignment']} RSI:{indicators['rsi']:.0f} MACD:{indicators['macd']:.5f}
VOL:{indicators['volatility']:.5f} CHG:{indicators['price_change']:.1f}%
POS:{analysis['positions']}

RULES: Bull=BUY Bear=SELL Mixed=HOLD Exit=CLOSE
RESPOND: BUY/SELL/HOLD/CLOSE"""
    
    def _make_fast_request(self, prompt: str) -> str:
        """
        Requisição ultra-rápida ao Ollama
        """
        payload = self.config.get_optimized_payload(prompt)
        
        try:
            response = requests.post(
                self.url, 
                json=payload, 
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                decision_text = result.get('response', '').strip().upper()
                
                # Parsing rápido
                if 'BUY' in decision_text and 'OPEN' not in decision_text:
                    return 'OPEN_BUY'
                elif 'SELL' in decision_text and 'OPEN' not in decision_text:
                    return 'OPEN_SELL'
                elif 'CLOSE' in decision_text:
                    return 'CLOSE_POSITION'
                else:
                    return 'HOLD'
            else:
                logger.warning(f"API error: {response.status_code}")
                return "HOLD"
                
        except requests.exceptions.Timeout:
            logger.warning("Request timeout - usando HOLD")
            return "HOLD"
        except Exception as e:
            logger.error(f"Request error: {e}")
            return "HOLD"
    
    def _clean_cache(self):
        """Limpa cache antigo"""
        if len(self.cache) > self.config.max_cache_size:
            # Remove entradas mais antigas
            current_time = time.time()
            old_keys = [k for k, v in self.cache.items() 
                       if current_time - v['time'] > self.config.cache_duration * 2]
            for key in old_keys:
                del self.cache[key]


class FastTradingStrategy:
    """
    Estratégia de trading otimizada para velocidade
    """
    
    def __init__(self, symbol="EURUSD", lot_size=0.1):
        self.symbol = symbol
        self.lot_size = lot_size
        self.timeframe = mt5.TIMEFRAME_M1
        
        # Configurar Ollama para velocidade máxima
        self.ollama_config = setup_ollama_for_trading("speed")
        self.ai_agent = FastOllamaAgent(self.ollama_config)
        self.analyzer = FastTechnicalAnalyzer()
        
        # Controle de execução
        self.last_execution = 0
        self.min_interval = 30  # segundos entre execuções
        
    def execute_fast_strategy(self):
        """
        Execução rápida da estratégia
        """
        current_time = time.time()
        
        # Controle de frequência
        if current_time - self.last_execution < self.min_interval:
            return
        
        try:
            # Obter dados mínimos necessários
            df = self._get_fast_data()
            if df is None or len(df) < 30:
                return
            
            # Análise rápida
            analysis = self._create_fast_analysis(df)
            
            # Decisão AI rápida
            decision = self.ai_agent.get_fast_decision(analysis)
            
            # Executar decisão
            self._execute_decision(decision, analysis)
            
            self.last_execution = current_time
            
        except Exception as e:
            logger.error(f"Erro na execução rápida: {e}")
    
    def _get_fast_data(self) -> Optional[pd.DataFrame]:
        """Obter dados de mercado rapidamente"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 50)
            if rates is None:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            logger.error(f"Erro ao obter dados: {e}")
            return None
    
    def _create_fast_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Criar análise rápida"""
        alligator = self.analyzer.calculate_alligator_fast(df)
        indicators = self.analyzer.calculate_fast_indicators(df)
        
        # Obter posições
        positions = mt5.positions_get(symbol=self.symbol)
        position_count = len(positions) if positions else 0
        
        return {
            "current_price": float(df['close'].iloc[-1]),
            "alligator": alligator,
            "indicators": indicators,
            "positions": position_count,
            "timestamp": datetime.now()
        }
    
    def _execute_decision(self, decision: str, analysis: Dict[str, Any]):
        """Executar decisão de trading"""
        positions = mt5.positions_get(symbol=self.symbol)
        has_positions = len(positions) > 0 if positions else False
        
        if decision == "OPEN_BUY" and not has_positions:
            self._open_position("BUY", analysis)
        elif decision == "OPEN_SELL" and not has_positions:
            self._open_position("SELL", analysis)
        elif decision == "CLOSE_POSITION" and has_positions:
            self._close_all_positions()
        
        logger.info(f"Decisão executada: {decision}")
    
    def _open_position(self, direction: str, analysis: Dict[str, Any]):
        """Abrir posição rapidamente"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                return False
            
            if direction == "BUY":
                price = mt5.symbol_info_tick(self.symbol).ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = mt5.symbol_info_tick(self.symbol).bid
                order_type = mt5.ORDER_TYPE_SELL
            
            # SL e TP dinâmicos baseados na volatilidade
            volatility = analysis['indicators']['volatility']
            sl_points = max(50, min(150, int(volatility * 100000)))
            tp_points = sl_points * 2  # Risk:Reward 1:2
            
            point = symbol_info.point
            if direction == "BUY":
                sl = price - sl_points * point
                tp = price + tp_points * point
            else:
                sl = price + sl_points * point
                tp = price - tp_points * point
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": self.lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Fast AI {direction}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"{direction} position opened: {self.lot_size} lots at {price}")
                return True
            else:
                logger.error(f"Failed to open {direction} position")
                return False
                
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return False
    
    def _close_all_positions(self):
        """Fechar todas as posições"""
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions:
            return
        
        for position in positions:
            try:
                if position.type == mt5.POSITION_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(self.symbol).bid
                else:
                    order_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(self.symbol).ask
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.symbol,
                    "volume": position.volume,
                    "type": order_type,
                    "position": position.ticket,
                    "price": price,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "Fast AI Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_FOK,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"Position {position.ticket} closed")
                    
            except Exception as e:
                logger.error(f"Error closing position {position.ticket}: {e}")


def main():
    """
    Função principal - Trading rápido com Ollama
    """
    logger.info("Iniciando Fast AI Trading System com Ollama")
    
    # Inicializar MT5
    if not mt5.initialize():
        logger.error(f"Falha ao inicializar MT5: {mt5.last_error()}")
        return
    
    # Verificar conta
    account_info = mt5.account_info()
    if not account_info:
        logger.error("Falha ao obter informações da conta")
        mt5.shutdown()
        return
    
    logger.info(f"Conectado à conta MT5: {account_info.login}")
    logger.info(f"Saldo: {account_info.balance} {account_info.currency}")
    logger.info(f"Servidor: {account_info.server}")
    
    # Criar estratégia
    strategy = FastTradingStrategy()
    
    try:
        logger.info("Iniciando loop de trading rápido...")
        iteration = 0
        
        while True:
            iteration += 1
            
            # Executar estratégia
            strategy.execute_fast_strategy()
            
            # Log de status a cada 10 iterações
            if iteration % 10 == 0:
                account_info = mt5.account_info()
                if account_info:
                    logger.info(f"Iteração {iteration} - Saldo: {account_info.balance} - Equity: {account_info.equity}")
            
            # Pausa curta para não sobrecarregar
            time.sleep(5)  # 5 segundos entre verificações
            
    except KeyboardInterrupt:
        logger.info("Parando sistema de trading...")
    except Exception as e:
        logger.error(f"Erro no sistema: {e}")
    finally:
        mt5.shutdown()
        logger.info("Sistema encerrado")


if __name__ == "__main__":
    main()
