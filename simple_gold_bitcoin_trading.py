#!/usr/bin/env python3
"""
Sistema Simples e Robusto para XAUUSD e BTCUSD
Funciona com ou sem Ollama
"""

import logging
import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimpleAI:
    """IA simples com fallback técnico"""
    
    def __init__(self):
        self.ai_working = self._test_ollama()
        if self.ai_working:
            logger.info("🤖 IA Ollama funcionando")
        else:
            logger.info("📊 Usando lógica técnica pura")
    
    def _test_ollama(self) -> bool:
        """Testa se Ollama está funcionando"""
        try:
            import requests
            
            # Testar conexão
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code != 200:
                return False
            
            # Testar modelo mais simples primeiro
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            # Tentar modelos em ordem de velocidade
            test_models = ["llama3:8b", "llama3.2:1b", "llama3:latest"]
            
            for model in test_models:
                if model in model_names:
                    # Teste rápido
                    test_response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": model,
                            "prompt": "BUY",
                            "stream": False,
                            "max_tokens": 3
                        },
                        timeout=8
                    )
                    
                    if test_response.status_code == 200:
                        self.working_model = model
                        logger.info(f"Modelo funcionando: {model}")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Ollama não disponível: {e}")
            return False
    
    def get_decision(self, symbol: str, price: float, alligator: dict, rsi: float, macd: float) -> str:
        """Decisão de trading"""
        if self.ai_working:
            return self._ai_decision(symbol, price, alligator, rsi, macd)
        else:
            return self._technical_decision(alligator, rsi, macd)
    
    def _ai_decision(self, symbol: str, price: float, alligator: dict, rsi: float, macd: float) -> str:
        """Decisão usando IA"""
        try:
            import requests
            
            prompt = f"{symbol} {price:.2f} ALG:{alligator['alignment']} RSI:{rsi:.0f} MACD:{macd:.4f} BUY/SELL/HOLD?"
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.working_model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "max_tokens": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '').upper()
                if 'BUY' in result:
                    return 'OPEN_BUY'
                elif 'SELL' in result:
                    return 'OPEN_SELL'
                elif 'CLOSE' in result:
                    return 'CLOSE_POSITION'
                else:
                    return 'HOLD'
            else:
                # Fallback para lógica técnica
                return self._technical_decision(alligator, rsi, macd)
                
        except:
            # Fallback para lógica técnica
            return self._technical_decision(alligator, rsi, macd)
    
    def _technical_decision(self, alligator: dict, rsi: float, macd: float) -> str:
        """Decisão técnica pura"""
        alignment = alligator['alignment']
        strength = alligator['strength']
        
        # Lógica simples e robusta
        if alignment == "bullish" and strength > 0.3 and rsi < 70 and macd > 0:
            return 'OPEN_BUY'
        elif alignment == "bearish" and strength > 0.3 and rsi > 30 and macd < 0:
            return 'OPEN_SELL'
        elif rsi > 80 or rsi < 20:
            return 'CLOSE_POSITION'
        else:
            return 'HOLD'


class SimpleTrader:
    """Trader simples para XAUUSD e BTCUSD"""
    
    def __init__(self):
        self.symbols = ["XAUUSD", "BTCUSD"]
        self.ai = SimpleAI()
        self.last_trade = {symbol: 0 for symbol in self.symbols}
        
        # Configurações simples
        self.configs = {
            "XAUUSD": {"lot": 0.01, "sl": 200, "tp": 400},
            "BTCUSD": {"lot": 0.01, "sl": 500, "tp": 1000}
        }
    
    def analyze_symbol(self, symbol: str) -> dict:
        """Análise técnica simples"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 30)
            if rates is None:
                return None
            
            df = pd.DataFrame(rates)
            close = df['close']
            
            # Alligator simples
            jaw = close.rolling(13).mean().shift(8).iloc[-1]
            teeth = close.rolling(8).mean().shift(5).iloc[-1]
            lips = close.rolling(5).mean().shift(3).iloc[-1]
            current = close.iloc[-1]
            
            # Alinhamento
            if current > lips > teeth > jaw:
                alignment = "bullish"
                strength = (current - jaw) / current * 100
            elif current < lips < teeth < jaw:
                alignment = "bearish"
                strength = (jaw - current) / current * 100
            else:
                alignment = "neutral"
                strength = 0
            
            # RSI simples
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + gain / loss))
            
            # MACD simples
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = (ema12 - ema26).iloc[-1]
            
            return {
                "price": float(current),
                "alligator": {"alignment": alignment, "strength": abs(strength)},
                "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
                "macd": float(macd) if not pd.isna(macd) else 0
            }
            
        except Exception as e:
            logger.error(f"Erro na análise {symbol}: {e}")
            return None
    
    def trade_symbol(self, symbol: str):
        """Trading para um símbolo"""
        try:
            # Controle de frequência
            if time.time() - self.last_trade[symbol] < 30:
                return
            
            # Análise
            analysis = self.analyze_symbol(symbol)
            if not analysis:
                return
            
            # Decisão
            decision = self.ai.get_decision(
                symbol,
                analysis["price"],
                analysis["alligator"],
                analysis["rsi"],
                analysis["macd"]
            )
            
            # Executar
            self._execute(symbol, decision)
            self.last_trade[symbol] = time.time()
            
        except Exception as e:
            logger.error(f"Erro no trading {symbol}: {e}")
    
    def _execute(self, symbol: str, decision: str):
        """Executa decisão"""
        try:
            positions = mt5.positions_get(symbol=symbol)
            has_pos = len(positions) > 0 if positions else False
            config = self.configs[symbol]
            
            if decision == "OPEN_BUY" and not has_pos:
                self._open(symbol, "BUY", config)
            elif decision == "OPEN_SELL" and not has_pos:
                self._open(symbol, "SELL", config)
            elif decision == "CLOSE_POSITION" and has_pos:
                self._close_all(symbol)
            
            if decision != "HOLD":
                ai_mode = "IA" if self.ai.ai_working else "TEC"
                logger.info(f"{symbol} ({ai_mode}): {decision}")
                
        except Exception as e:
            logger.error(f"Erro na execução {symbol}: {e}")
    
    def _open(self, symbol: str, direction: str, config: dict):
        """Abre posição"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return
            
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
            
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return
            
            if direction == "BUY":
                price = tick.ask
                order_type = mt5.ORDER_TYPE_BUY
                sl = price - config["sl"] * symbol_info.point
                tp = price + config["tp"] * symbol_info.point
            else:
                price = tick.bid
                order_type = mt5.ORDER_TYPE_SELL
                sl = price + config["sl"] * symbol_info.point
                tp = price - config["tp"] * symbol_info.point
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": config["lot"],
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 50,
                "magic": 234000,
                "comment": f"Simple {symbol}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✓ {symbol} {direction} aberto: {config['lot']} lots")
            else:
                logger.error(f"✗ Falha {symbol} {direction}")
                
        except Exception as e:
            logger.error(f"Erro ao abrir {symbol}: {e}")
    
    def _close_all(self, symbol: str):
        """Fecha todas as posições"""
        try:
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                return
            
            for pos in positions:
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    continue
                
                if pos.type == mt5.POSITION_TYPE_BUY:
                    price = tick.bid
                    order_type = mt5.ORDER_TYPE_SELL
                else:
                    price = tick.ask
                    order_type = mt5.ORDER_TYPE_BUY
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": order_type,
                    "position": pos.ticket,
                    "price": price,
                    "deviation": 50,
                    "magic": pos.magic,
                    "comment": f"Close {symbol}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"✓ {symbol} posição fechada")
                    
        except Exception as e:
            logger.error(f"Erro ao fechar {symbol}: {e}")
    
    def run(self):
        """Executa trading"""
        logger.info("🚀 Iniciando trading simples XAUUSD e BTCUSD")
        
        try:
            while True:
                for symbol in self.symbols:
                    self.trade_symbol(symbol)
                
                # Status a cada 5 minutos
                if int(time.time()) % 300 == 0:
                    account = mt5.account_info()
                    if account:
                        logger.info(f"💰 Saldo: {account.balance:.2f} | Equity: {account.equity:.2f}")
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("⏹ Trading parado")


def main():
    """Função principal"""
    print("=== TRADING SIMPLES OURO E BITCOIN ===")
    
    # Conectar MT5
    if not mt5.initialize():
        print(f"❌ Erro MT5: {mt5.last_error()}")
        return
    
    # Verificar conta
    account = mt5.account_info()
    if not account:
        print("❌ Sem informações da conta")
        mt5.shutdown()
        return
    
    print(f"✓ Conta: {account.login}")
    print(f"✓ Saldo: {account.balance} {account.currency}")
    
    # Verificar símbolos
    symbols_ok = []
    for symbol in ["XAUUSD", "BTCUSD"]:
        info = mt5.symbol_info(symbol)
        if info:
            if not info.visible:
                mt5.symbol_select(symbol, True)
            symbols_ok.append(symbol)
            print(f"✓ {symbol} disponível")
        else:
            print(f"❌ {symbol} não encontrado")
    
    if not symbols_ok:
        print("❌ Nenhum símbolo disponível")
        mt5.shutdown()
        return
    
    # Iniciar trading
    trader = SimpleTrader()
    trader.symbols = symbols_ok
    
    print(f"\n🚀 Iniciando trading para: {', '.join(symbols_ok)}")
    print("Pressione Ctrl+C para parar")
    
    try:
        trader.run()
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        mt5.shutdown()
        print("✓ Sistema encerrado")


if __name__ == "__main__":
    main()
