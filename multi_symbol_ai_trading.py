#!/usr/bin/env python3
"""
Sistema de Trading AI Multi-Símbolo
Configurado para XAUUSD (Ouro) e BTCUSD (Bitcoin)
Otimizado para velocidade com Ollama
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
from concurrent.futures import ThreadPoolExecutor
import threading
from model_selector import auto_select_trading_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_symbol_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SymbolConfig:
    """
    Configuração específica para cada símbolo
    """
    
    SYMBOL_CONFIGS = {
        "XAUUSD": {
            "name": "Gold",
            "lot_size": 0.01,  # Menor devido ao valor alto
            "sl_points": 200,  # Maior spread e volatilidade
            "tp_points": 400,  # Risk:Reward 1:2
            "max_risk_percent": 1.0,  # Menor risco devido à volatilidade
            "min_spread": 30,  # Spread típico do ouro
            "volatility_multiplier": 2.0,  # Ouro é mais volátil
            "pip_value_multiplier": 100,  # Ajuste para ouro
            "trading_hours": "24/5",  # Ouro negocia 24h
            "session_volatility": {
                "asian": 0.8,
                "london": 1.2,
                "ny": 1.0
            }
        },
        "BTCUSD": {
            "name": "Bitcoin",
            "lot_size": 0.01,  # Muito pequeno devido ao valor
            "sl_points": 500,  # Bitcoin tem movimentos grandes
            "tp_points": 1000,  # Risk:Reward 1:2
            "max_risk_percent": 0.5,  # Risco muito baixo devido à volatilidade extrema
            "min_spread": 50,  # Spread maior para crypto
            "volatility_multiplier": 5.0,  # Bitcoin é extremamente volátil
            "pip_value_multiplier": 1,  # Bitcoin em USD
            "trading_hours": "24/7",  # Bitcoin negocia 24/7
            "session_volatility": {
                "asian": 0.9,
                "london": 1.1,
                "ny": 1.3
            }
        }
    }
    
    @classmethod
    def get_config(cls, symbol: str) -> Dict[str, Any]:
        """Retorna configuração para o símbolo"""
        return cls.SYMBOL_CONFIGS.get(symbol, cls.SYMBOL_CONFIGS["XAUUSD"])


class MultiSymbolTechnicalAnalyzer:
    """
    Analisador técnico adaptado para múltiplos símbolos
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.config = SymbolConfig.get_config(symbol)
    
    def calculate_alligator_adapted(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Alligator adaptado para características do símbolo
        """
        close = df['close']
        
        # Períodos ajustados baseados na volatilidade do símbolo
        volatility_factor = self.config["volatility_multiplier"]
        
        # Ajustar períodos para símbolos mais voláteis
        if volatility_factor > 2.0:  # Bitcoin
            jaw_period = 21  # Período maior para suavizar
            teeth_period = 13
            lips_period = 8
        else:  # Ouro
            jaw_period = 13
            teeth_period = 8
            lips_period = 5
        
        jaw = close.rolling(jaw_period).mean().shift(8)
        teeth = close.rolling(teeth_period).mean().shift(5)
        lips = close.rolling(lips_period).mean().shift(3)
        
        current_price = close.iloc[-1]
        last_jaw = jaw.iloc[-1] if not pd.isna(jaw.iloc[-1]) else current_price
        last_teeth = teeth.iloc[-1] if not pd.isna(teeth.iloc[-1]) else current_price
        last_lips = lips.iloc[-1] if not pd.isna(lips.iloc[-1]) else current_price
        
        # Determinar alinhamento
        if current_price > last_lips > last_teeth > last_jaw:
            alignment = "bullish"
            strength = (current_price - last_jaw) / current_price * 100
        elif current_price < last_lips < last_teeth < last_jaw:
            alignment = "bearish"
            strength = (last_jaw - current_price) / current_price * 100
        else:
            alignment = "neutral"
            strength = 0
        
        return {
            "jaw": float(last_jaw),
            "teeth": float(last_teeth),
            "lips": float(last_lips),
            "alignment": alignment,
            "strength": abs(float(strength))
        }
    
    def calculate_adapted_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Indicadores técnicos adaptados para o símbolo
        """
        close = df['close']
        high = df['high']
        low = df['low']
        
        # RSI adaptado
        rsi_period = 14 if self.config["volatility_multiplier"] < 3.0 else 21
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD adaptado
        if self.symbol == "BTCUSD":
            fast, slow, signal = 12, 26, 9  # Padrão para crypto
        else:
            fast, slow, signal = 8, 21, 5   # Mais sensível para ouro
        
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        
        # ATR adaptado
        tr = np.maximum(high - low, 
                       np.maximum(abs(high - close.shift(1)), 
                                abs(low - close.shift(1))))
        atr = tr.rolling(14).mean()
        
        # Volatilidade normalizada para o símbolo
        normalized_volatility = atr.iloc[-1] / close.iloc[-1] * 100
        
        return {
            "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
            "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0,
            "macd_signal": float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else 0,
            "atr": float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0,
            "volatility_percent": float(normalized_volatility),
            "price_change_1h": float((close.iloc[-1] - close.iloc[-60]) / close.iloc[-60] * 100) if len(close) >= 60 else 0
        }


class MultiSymbolOllamaAgent:
    """
    Agente Ollama especializado para múltiplos símbolos
    """
    
    def __init__(self, model: str = None):
        # Seleção automática do melhor modelo disponível
        if model is None:
            model_config = auto_select_trading_model("speed")
            self.model = model_config["model"]
            self.timeout = model_config["timeout"]
            self.temperature = model_config["temperature"]
            self.max_tokens = model_config["max_tokens"]
        else:
            self.model = model
            self.timeout = 15
            self.temperature = 0.2
            self.max_tokens = 50

        self.url = "http://localhost:11434/api/generate"
        self.cache = {}
        self.cache_duration = 45  # segundos

        logger.info(f"Ollama Agent inicializado com modelo: {self.model} (timeout: {self.timeout}s)")
        
    def get_symbol_decision(self, symbol: str, analysis: Dict[str, Any]) -> str:
        """
        Decisão específica para cada símbolo
        """
        try:
            # Cache por símbolo
            cache_key = f"{symbol}_{int(time.time() / self.cache_duration)}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Prompt específico para o símbolo
            prompt = self._generate_symbol_prompt(symbol, analysis)
            
            # Fazer requisição
            decision = self._make_request(prompt)
            
            # Cache da decisão
            self.cache[cache_key] = decision
            
            # Limpar cache antigo
            if len(self.cache) > 10:
                oldest = min(self.cache.keys())
                del self.cache[oldest]
            
            return decision
            
        except Exception as e:
            logger.error(f"Erro na decisão para {symbol}: {e}")
            return "HOLD"
    
    def _generate_symbol_prompt(self, symbol: str, analysis: Dict[str, Any]) -> str:
        """
        Gera prompt específico para cada símbolo
        """
        config = SymbolConfig.get_config(symbol)
        alligator = analysis['alligator']
        indicators = analysis['indicators']
        
        if symbol == "XAUUSD":
            context = f"""GOLD TRADING - High volatility precious metal
Spread consideration: {config['min_spread']} points minimum
Market sessions affect volatility significantly"""
        else:  # BTCUSD
            context = f"""BITCOIN TRADING - Extreme volatility cryptocurrency  
24/7 market with high spreads: {config['min_spread']} points
News and sentiment drive major moves"""
        
        return f"""{context}

{symbol} {analysis['current_price']:.2f}
ALG: {alligator['alignment']} (S:{alligator['strength']:.1f}%)
RSI: {indicators['rsi']:.0f} MACD: {indicators['macd']:.4f}
VOL: {indicators['volatility_percent']:.2f}% CHG1H: {indicators['price_change_1h']:.1f}%

RULES:
- Strong Bull (>80% confidence): OPEN_BUY
- Strong Bear (>80% confidence): OPEN_SELL  
- Weak signals (<60% confidence): HOLD
- Opposite signals: CLOSE_POSITION

RESPOND: BUY/SELL/HOLD/CLOSE"""
    
    def _make_request(self, prompt: str) -> str:
        """Faz requisição otimizada ao Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                decision_text = result.get('response', '').strip().upper()
                
                # Parse rápido
                if 'BUY' in decision_text:
                    return 'OPEN_BUY'
                elif 'SELL' in decision_text:
                    return 'OPEN_SELL'
                elif 'CLOSE' in decision_text:
                    return 'CLOSE_POSITION'
                else:
                    return 'HOLD'
            else:
                return "HOLD"
                
        except Exception as e:
            logger.error(f"Erro na requisição: {e}")
            return "HOLD"


class MultiSymbolStrategy:
    """
    Estratégia para múltiplos símbolos
    """
    
    def __init__(self, symbols: List[str] = ["XAUUSD", "BTCUSD"]):
        self.symbols = symbols
        self.ai_agent = MultiSymbolOllamaAgent()
        self.analyzers = {symbol: MultiSymbolTechnicalAnalyzer(symbol) for symbol in symbols}
        self.last_execution = {symbol: 0 for symbol in symbols}
        self.execution_interval = 30  # segundos
        
    def get_market_data(self, symbol: str, count: int = 50) -> Optional[pd.DataFrame]:
        """Obter dados de mercado para símbolo específico"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, count)
            if rates is None:
                logger.error(f"Falha ao obter dados para {symbol}: {mt5.last_error()}")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            logger.error(f"Erro ao obter dados para {symbol}: {e}")
            return None
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Análise completa para um símbolo"""
        try:
            # Obter dados
            df = self.get_market_data(symbol)
            if df is None or len(df) < 30:
                return None
            
            # Análise técnica
            analyzer = self.analyzers[symbol]
            alligator = analyzer.calculate_alligator_adapted(df)
            indicators = analyzer.calculate_adapted_indicators(df)
            
            return {
                "symbol": symbol,
                "current_price": float(df['close'].iloc[-1]),
                "alligator": alligator,
                "indicators": indicators,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de {symbol}: {e}")
            return None
    
    def execute_symbol_strategy(self, symbol: str):
        """Executa estratégia para um símbolo específico"""
        try:
            current_time = time.time()
            
            # Controle de frequência por símbolo
            if current_time - self.last_execution[symbol] < self.execution_interval:
                return
            
            # Análise do símbolo
            analysis = self.analyze_symbol(symbol)
            if not analysis:
                return
            
            # Decisão AI
            decision = self.ai_agent.get_symbol_decision(symbol, analysis)
            
            # Executar decisão
            self._execute_decision(symbol, decision, analysis)
            
            self.last_execution[symbol] = current_time
            
        except Exception as e:
            logger.error(f"Erro na execução para {symbol}: {e}")
    
    def _execute_decision(self, symbol: str, decision: str, analysis: Dict[str, Any]):
        """Executa decisão de trading para símbolo específico"""
        try:
            config = SymbolConfig.get_config(symbol)
            positions = mt5.positions_get(symbol=symbol)
            has_positions = len(positions) > 0 if positions else False
            
            if decision == "OPEN_BUY" and not has_positions:
                self._open_position(symbol, "BUY", config, analysis)
            elif decision == "OPEN_SELL" and not has_positions:
                self._open_position(symbol, "SELL", config, analysis)
            elif decision == "CLOSE_POSITION" and has_positions:
                self._close_positions(symbol)
            
            logger.info(f"{symbol}: {decision}")
            
        except Exception as e:
            logger.error(f"Erro ao executar decisão para {symbol}: {e}")
    
    def _open_position(self, symbol: str, direction: str, config: Dict[str, Any], analysis: Dict[str, Any]):
        """Abre posição com parâmetros específicos do símbolo"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger.error(f"Informações do símbolo {symbol} não disponíveis")
                return False
            
            # Verificar se símbolo está disponível
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"Falha ao selecionar símbolo {symbol}")
                    return False
            
            # Calcular tamanho da posição baseado na volatilidade
            volatility = analysis['indicators']['volatility_percent']
            base_lot = config['lot_size']
            
            # Ajustar lot size baseado na volatilidade
            if volatility > 2.0:  # Alta volatilidade
                lot_size = base_lot * 0.5
            elif volatility < 0.5:  # Baixa volatilidade
                lot_size = base_lot * 1.5
            else:
                lot_size = base_lot
            
            # Limites de lot size
            lot_size = max(0.01, min(lot_size, 0.1))
            
            # Preços
            if direction == "BUY":
                price = mt5.symbol_info_tick(symbol).ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = mt5.symbol_info_tick(symbol).bid
                order_type = mt5.ORDER_TYPE_SELL
            
            # SL e TP adaptados
            point = symbol_info.point
            sl_points = config['sl_points']
            tp_points = config['tp_points']
            
            # Ajustar baseado na volatilidade atual
            volatility_adj = min(2.0, max(0.5, volatility / 1.0))
            sl_points = int(sl_points * volatility_adj)
            tp_points = int(tp_points * volatility_adj)
            
            if direction == "BUY":
                sl = price - sl_points * point
                tp = price + tp_points * point
            else:
                sl = price + sl_points * point
                tp = price - tp_points * point
            
            # Requisição de ordem
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 50,  # Maior desvio para símbolos voláteis
                "magic": 234000 + hash(symbol) % 1000,  # Magic único por símbolo
                "comment": f"AI {symbol} {direction}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"{symbol} {direction}: {lot_size} lots at {price:.2f}")
                return True
            else:
                logger.error(f"Falha ao abrir {symbol} {direction}: {result.retcode if result else 'No result'}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao abrir posição {symbol}: {e}")
            return False
    
    def _close_positions(self, symbol: str):
        """Fecha todas as posições do símbolo"""
        try:
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                return
            
            for position in positions:
                if position.type == mt5.POSITION_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(symbol).bid
                else:
                    order_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(symbol).ask
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": position.volume,
                    "type": order_type,
                    "position": position.ticket,
                    "price": price,
                    "deviation": 50,
                    "magic": position.magic,
                    "comment": f"AI Close {symbol}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"{symbol} posição {position.ticket} fechada")
                    
        except Exception as e:
            logger.error(f"Erro ao fechar posições {symbol}: {e}")
    
    def run_parallel_trading(self):
        """Executa trading paralelo para todos os símbolos"""
        logger.info(f"Iniciando trading paralelo para: {', '.join(self.symbols)}")
        
        try:
            while True:
                # Executar estratégia para cada símbolo em paralelo
                with ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
                    futures = [
                        executor.submit(self.execute_symbol_strategy, symbol) 
                        for symbol in self.symbols
                    ]
                    
                    # Aguardar conclusão
                    for future in futures:
                        try:
                            future.result(timeout=30)
                        except Exception as e:
                            logger.error(f"Erro na execução paralela: {e}")
                
                # Log de status
                self._log_portfolio_status()
                
                # Pausa entre ciclos
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Parando trading paralelo...")
        except Exception as e:
            logger.error(f"Erro no trading paralelo: {e}")
    
    def _log_portfolio_status(self):
        """Log do status do portfólio"""
        try:
            account_info = mt5.account_info()
            if account_info:
                total_positions = 0
                for symbol in self.symbols:
                    positions = mt5.positions_get(symbol=symbol)
                    symbol_positions = len(positions) if positions else 0
                    total_positions += symbol_positions
                    if symbol_positions > 0:
                        logger.info(f"{symbol}: {symbol_positions} posições ativas")
                
                logger.info(f"Portfolio - Saldo: {account_info.balance:.2f} | "
                          f"Equity: {account_info.equity:.2f} | "
                          f"Posições: {total_positions}")
        except Exception as e:
            logger.error(f"Erro no log do portfolio: {e}")


def main():
    """Função principal"""
    logger.info("=== SISTEMA MULTI-SÍMBOLO AI TRADING ===")
    logger.info("Símbolos: XAUUSD (Ouro) e BTCUSD (Bitcoin)")
    
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
    
    logger.info(f"Conta MT5: {account_info.login}")
    logger.info(f"Servidor: {account_info.server}")
    logger.info(f"Saldo: {account_info.balance} {account_info.currency}")
    
    # Verificar símbolos disponíveis
    symbols = ["XAUUSD", "BTCUSD"]
    available_symbols = []
    
    for symbol in symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            if not symbol_info.visible:
                if mt5.symbol_select(symbol, True):
                    available_symbols.append(symbol)
                    logger.info(f"✓ {symbol} selecionado")
                else:
                    logger.warning(f"✗ {symbol} não pode ser selecionado")
            else:
                available_symbols.append(symbol)
                logger.info(f"✓ {symbol} disponível")
        else:
            logger.warning(f"✗ {symbol} não encontrado no broker")
    
    if not available_symbols:
        logger.error("Nenhum símbolo disponível para trading")
        mt5.shutdown()
        return
    
    logger.info(f"Símbolos ativos: {', '.join(available_symbols)}")
    
    # Criar estratégia
    strategy = MultiSymbolStrategy(available_symbols)
    
    try:
        # Executar trading
        strategy.run_parallel_trading()
    except Exception as e:
        logger.error(f"Erro no sistema: {e}")
    finally:
        mt5.shutdown()
        logger.info("Sistema encerrado")


if __name__ == "__main__":
    main()
