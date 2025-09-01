#!/usr/bin/env python3
"""
Sistema de Trading Multi-Símbolo Robusto
XAUUSD e BTCUSD com fallback sem IA
"""

import logging
import time
import sys
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('robust_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RobustOllamaAgent:
    """
    Agente Ollama com fallback robusto
    """
    
    def __init__(self):
        self.available_models = self._get_available_models()
        self.selected_model = self._select_best_model()
        self.ai_enabled = self.selected_model is not None
        
        if self.ai_enabled:
            logger.info(f"IA habilitada com modelo: {self.selected_model['name']}")
        else:
            logger.warning("IA desabilitada - usando lógica técnica pura")
    
    def _get_available_models(self) -> List[Dict]:
        """Verifica modelos disponíveis"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [{"name": m['name'], "size": m.get('size', 0)} for m in models]
            else:
                return []
        except:
            return []
    
    def _select_best_model(self) -> Optional[Dict]:
        """Seleciona o melhor modelo disponível"""
        if not self.available_models:
            return None
        
        # Ordem de preferência por velocidade
        preferred_order = ["llama3:8b", "llama3.2:1b", "llama3:latest", "phi3:latest"]
        
        for preferred in preferred_order:
            for model in self.available_models:
                if model["name"] == preferred:
                    # Testar se funciona
                    if self._test_model(model["name"]):
                        return {
                            "name": model["name"],
                            "timeout": 10 if "1b" in model["name"] else 15,
                            "temperature": 0.1 if "1b" in model["name"] else 0.2
                        }
        
        return None
    
    def _test_model(self, model_name: str) -> bool:
        """Testa se um modelo funciona"""
        try:
            import requests
            payload = {
                "model": model_name,
                "prompt": "BUY",
                "stream": False,
                "max_tokens": 5
            }
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_decision(self, symbol: str, analysis: Dict[str, Any]) -> str:
        """Obter decisão com fallback"""
        if self.ai_enabled:
            return self._get_ai_decision(symbol, analysis)
        else:
            return self._get_technical_decision(symbol, analysis)
    
    def _get_ai_decision(self, symbol: str, analysis: Dict[str, Any]) -> str:
        """Decisão usando IA"""
        try:
            import requests
            
            prompt = self._create_prompt(symbol, analysis)
            
            payload = {
                "model": self.selected_model["name"],
                "prompt": prompt,
                "stream": False,
                "temperature": self.selected_model["temperature"],
                "max_tokens": 20
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=self.selected_model["timeout"]
            )
            
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
                logger.warning(f"IA falhou, usando lógica técnica para {symbol}")
                return self._get_technical_decision(symbol, analysis)
                
        except Exception as e:
            logger.warning(f"Erro na IA para {symbol}, usando lógica técnica: {e}")
            return self._get_technical_decision(symbol, analysis)
    
    def _get_technical_decision(self, symbol: str, analysis: Dict[str, Any]) -> str:
        """Decisão usando apenas lógica técnica (fallback)"""
        try:
            alligator = analysis['alligator']
            indicators = analysis['indicators']
            
            # Lógica técnica pura baseada no Alligator
            alignment = alligator['alignment']
            strength = alligator['strength']
            rsi = indicators['rsi']
            macd = indicators['macd']
            
            # Condições para BUY
            if (alignment == "bullish" and 
                strength > 0.5 and 
                rsi < 70 and 
                macd > 0):
                return 'OPEN_BUY'
            
            # Condições para SELL
            elif (alignment == "bearish" and 
                  strength > 0.5 and 
                  rsi > 30 and 
                  macd < 0):
                return 'OPEN_SELL'
            
            # Condições para fechar
            elif (alignment == "neutral" or 
                  rsi > 80 or 
                  rsi < 20):
                return 'CLOSE_POSITION'
            
            else:
                return 'HOLD'
                
        except Exception as e:
            logger.error(f"Erro na lógica técnica para {symbol}: {e}")
            return 'HOLD'
    
    def _create_prompt(self, symbol: str, analysis: Dict[str, Any]) -> str:
        """Cria prompt otimizado"""
        alligator = analysis['alligator']
        indicators = analysis['indicators']
        
        return f"""{symbol} {analysis['current_price']:.2f}
ALG:{alligator['alignment']} RSI:{indicators['rsi']:.0f} MACD:{indicators['macd']:.4f}
VOL:{indicators['volatility_percent']:.1f}%

BUY/SELL/HOLD/CLOSE?"""


class RobustMultiSymbolStrategy:
    """
    Estratégia robusta para múltiplos símbolos
    """
    
    def __init__(self, symbols: List[str] = ["XAUUSD", "BTCUSD"]):
        self.symbols = symbols
        self.ai_agent = RobustOllamaAgent()
        self.last_execution = {symbol: 0 for symbol in symbols}
        self.execution_interval = 30
        
        # Configurações por símbolo
        self.configs = {
            "XAUUSD": {
                "lot_size": 0.01,
                "sl_points": 200,
                "tp_points": 400,
                "max_risk": 1.0
            },
            "BTCUSD": {
                "lot_size": 0.01,
                "sl_points": 500,
                "tp_points": 1000,
                "max_risk": 0.5
            }
        }
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Análise técnica robusta"""
        try:
            # Obter dados
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
            if rates is None:
                return None
            
            df = pd.DataFrame(rates)
            close = df['close']
            high = df['high']
            low = df['low']
            
            # Alligator
            jaw = close.rolling(13).mean().shift(8)
            teeth = close.rolling(8).mean().shift(5)
            lips = close.rolling(5).mean().shift(3)
            
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
            
            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            
            # Volatilidade
            tr = np.maximum(high - low, 
                           np.maximum(abs(high - close.shift(1)), 
                                    abs(low - close.shift(1))))
            atr = tr.rolling(14).mean()
            volatility_percent = atr.iloc[-1] / current_price * 100
            
            return {
                "symbol": symbol,
                "current_price": float(current_price),
                "alligator": {
                    "jaw": float(last_jaw),
                    "teeth": float(last_teeth),
                    "lips": float(last_lips),
                    "alignment": alignment,
                    "strength": abs(float(strength))
                },
                "indicators": {
                    "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
                    "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0,
                    "volatility_percent": float(volatility_percent)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de {symbol}: {e}")
            return None
    
    def execute_symbol_strategy(self, symbol: str):
        """Executa estratégia para um símbolo"""
        try:
            current_time = time.time()
            
            # Controle de frequência
            if current_time - self.last_execution[symbol] < self.execution_interval:
                return
            
            # Análise
            analysis = self.analyze_symbol(symbol)
            if not analysis:
                return
            
            # Decisão (IA ou técnica)
            decision = self.ai_agent.get_decision(symbol, analysis)
            
            # Executar
            self._execute_decision(symbol, decision, analysis)
            
            self.last_execution[symbol] = current_time
            
        except Exception as e:
            logger.error(f"Erro na execução para {symbol}: {e}")
    
    def _execute_decision(self, symbol: str, decision: str, analysis: Dict[str, Any]):
        """Executa decisão de trading"""
        try:
            config = self.configs[symbol]
            positions = mt5.positions_get(symbol=symbol)
            has_positions = len(positions) > 0 if positions else False
            
            if decision == "OPEN_BUY" and not has_positions:
                self._open_position(symbol, "BUY", config, analysis)
            elif decision == "OPEN_SELL" and not has_positions:
                self._open_position(symbol, "SELL", config, analysis)
            elif decision == "CLOSE_POSITION" and has_positions:
                self._close_positions(symbol)
            
            ai_status = "IA" if self.ai_agent.ai_enabled else "TÉCNICA"
            logger.info(f"{symbol} ({ai_status}): {decision}")
            
        except Exception as e:
            logger.error(f"Erro ao executar decisão para {symbol}: {e}")
    
    def _open_position(self, symbol: str, direction: str, config: Dict, analysis: Dict):
        """Abre posição robusta"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False
            
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
            
            # Tamanho da posição
            lot_size = config["lot_size"]
            
            # Preços
            if direction == "BUY":
                price = mt5.symbol_info_tick(symbol).ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = mt5.symbol_info_tick(symbol).bid
                order_type = mt5.ORDER_TYPE_SELL
            
            # SL e TP
            point = symbol_info.point
            sl_points = config["sl_points"]
            tp_points = config["tp_points"]
            
            if direction == "BUY":
                sl = price - sl_points * point
                tp = price + tp_points * point
            else:
                sl = price + sl_points * point
                tp = price - tp_points * point
            
            # Ordem
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 50,
                "magic": 234000 + hash(symbol) % 1000,
                "comment": f"Robust {symbol} {direction}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"{symbol} {direction}: {lot_size} lots at {price:.2f}")
                return True
            else:
                logger.error(f"Falha ao abrir {symbol} {direction}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao abrir posição {symbol}: {e}")
            return False
    
    def _close_positions(self, symbol: str):
        """Fecha posições"""
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
                    "comment": f"Robust Close {symbol}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"{symbol} posição {position.ticket} fechada")
                    
        except Exception as e:
            logger.error(f"Erro ao fechar posições {symbol}: {e}")
    
    def run_trading(self):
        """Executa trading robusto"""
        logger.info(f"Iniciando trading robusto para: {', '.join(self.symbols)}")
        
        if self.ai_agent.ai_enabled:
            logger.info("🤖 Modo IA ativado")
        else:
            logger.info("📊 Modo técnico puro ativado")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Executar para cada símbolo
                for symbol in self.symbols:
                    self.execute_symbol_strategy(symbol)
                
                # Log de status
                if iteration % 10 == 0:
                    self._log_status()
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Trading interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro no trading: {e}")
    
    def _log_status(self):
        """Log do status"""
        try:
            account_info = mt5.account_info()
            if account_info:
                total_positions = 0
                for symbol in self.symbols:
                    positions = mt5.positions_get(symbol=symbol)
                    count = len(positions) if positions else 0
                    total_positions += count
                    if count > 0:
                        logger.info(f"{symbol}: {count} posições")
                
                logger.info(f"Saldo: {account_info.balance:.2f} | "
                          f"Equity: {account_info.equity:.2f} | "
                          f"Posições: {total_positions}")
        except Exception as e:
            logger.error(f"Erro no log: {e}")


def main():
    """Função principal robusta"""
    logger.info("=== SISTEMA ROBUSTO MULTI-SÍMBOLO ===")
    
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
    
    logger.info(f"Conta: {account_info.login} | Saldo: {account_info.balance}")
    
    # Verificar símbolos
    symbols = ["XAUUSD", "BTCUSD"]
    available_symbols = []
    
    for symbol in symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
            available_symbols.append(symbol)
            logger.info(f"✓ {symbol} disponível")
        else:
            logger.warning(f"✗ {symbol} não encontrado")
    
    if not available_symbols:
        logger.error("Nenhum símbolo disponível")
        mt5.shutdown()
        return
    
    # Criar estratégia
    strategy = RobustMultiSymbolStrategy(available_symbols)
    
    try:
        strategy.run_trading()
    except Exception as e:
        logger.error(f"Erro no sistema: {e}")
    finally:
        mt5.shutdown()
        logger.info("Sistema encerrado")


if __name__ == "__main__":
    main()
