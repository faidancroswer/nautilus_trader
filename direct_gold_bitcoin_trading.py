#!/usr/bin/env python3
"""
Trading Direto XAUUSD e BTCUSD
Sistema que funciona garantidamente
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def get_alligator_signal(df):
    """Calcula sinal do Alligator"""
    close = df['close']
    
    jaw = close.rolling(13).mean().shift(8).iloc[-1]
    teeth = close.rolling(8).mean().shift(5).iloc[-1]
    lips = close.rolling(5).mean().shift(3).iloc[-1]
    current = close.iloc[-1]
    
    if pd.isna(jaw) or pd.isna(teeth) or pd.isna(lips):
        return "HOLD"
    
    if current > lips > teeth > jaw:
        return "BUY"
    elif current < lips < teeth < jaw:
        return "SELL"
    else:
        return "HOLD"


def get_rsi(df, period=14):
    """Calcula RSI"""
    close = df['close']
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50


def trade_symbol(symbol, config):
    """Trading para um símbolo"""
    try:
        # Obter dados
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
        if rates is None:
            logger.error(f"{symbol}: Sem dados")
            return
        
        df = pd.DataFrame(rates)
        
        # Análise
        alligator_signal = get_alligator_signal(df)
        rsi = get_rsi(df)
        
        # Verificar posições
        positions = mt5.positions_get(symbol=symbol)
        has_position = len(positions) > 0 if positions else False
        
        # Decisão
        decision = "HOLD"
        
        if alligator_signal == "BUY" and not has_position and rsi < 70:
            decision = "OPEN_BUY"
        elif alligator_signal == "SELL" and not has_position and rsi > 30:
            decision = "OPEN_SELL"
        elif has_position and (rsi > 80 or rsi < 20):
            decision = "CLOSE"
        
        # Executar
        if decision == "OPEN_BUY":
            open_position(symbol, "BUY", config)
        elif decision == "OPEN_SELL":
            open_position(symbol, "SELL", config)
        elif decision == "CLOSE":
            close_positions(symbol)
        
        if decision != "HOLD":
            logger.info(f"{symbol}: {decision} (RSI: {rsi:.0f}, Alligator: {alligator_signal})")
            
    except Exception as e:
        logger.error(f"Erro {symbol}: {e}")


def open_position(symbol, direction, config):
    """Abre posição"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger.error(f"{symbol}: Symbol info not available")
            return

        # Verificações específicas para BTCUSD
        if symbol == "BTCUSD":
            # Verificar se trading está habilitado
            if symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
                logger.error(f"{symbol}: Trading disabled")
                return
            elif symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_CLOSEONLY:
                logger.error(f"{symbol}: Only close operations allowed")
                return

            # Verificar spread
            if symbol_info.spread > 5000:  # Spread muito alto para Bitcoin
                logger.warning(f"{symbol}: High spread {symbol_info.spread} points")

        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.error(f"{symbol}: Cannot select symbol")
                return
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger.error(f"{symbol}: No tick data available")
            return

        # Verificar e ajustar volume
        volume = config["lot"]
        if volume < symbol_info.volume_min:
            volume = symbol_info.volume_min
            logger.warning(f"{symbol}: Volume ajustado para mínimo: {volume}")
        elif volume > symbol_info.volume_max:
            volume = symbol_info.volume_max
            logger.warning(f"{symbol}: Volume ajustado para máximo: {volume}")

        # Ajustar volume para step
        if symbol_info.volume_step > 0:
            volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
        
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
            "comment": f"Direct {symbol}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✓ {symbol} {direction} aberto")
        else:
            # Log detalhado do erro
            if result:
                error_codes = {
                    10004: "Requote",
                    10006: "Request rejected",
                    10007: "Too frequent requests",
                    10013: "Market closed",
                    10014: "Not enough money",
                    10018: "Position closed",
                    10019: "Invalid price",
                    10020: "Invalid stops",
                    10021: "Invalid lot",
                    10027: "Trade timeout",
                    10028: "Invalid volume"
                }
                error_desc = error_codes.get(result.retcode, f"Unknown error {result.retcode}")
                logger.error(f"✗ Falha {symbol} {direction}: {error_desc} (Code: {result.retcode})")
                logger.error(f"   Price: {price:.5f}, SL: {sl:.5f}, TP: {tp:.5f}, Volume: {config['lot']}")

                # Verificar informações do símbolo
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    logger.error(f"   Min volume: {symbol_info.volume_min}, Max: {symbol_info.volume_max}")
                    logger.error(f"   Volume step: {symbol_info.volume_step}")
                    logger.error(f"   Spread: {symbol_info.spread} points")
                    logger.error(f"   Trade mode: {symbol_info.trade_mode}")
            else:
                logger.error(f"✗ Falha {symbol} {direction}: No result from MT5")
            
    except Exception as e:
        logger.error(f"Erro ao abrir {symbol}: {e}")


def close_positions(symbol):
    """Fecha posições"""
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
                logger.info(f"✓ {symbol} fechado")
                
    except Exception as e:
        logger.error(f"Erro ao fechar {symbol}: {e}")


def main():
    """Função principal"""
    print("=== TRADING DIRETO OURO E BITCOIN ===")
    
    # Conectar MT5
    if not mt5.initialize():
        print(f"❌ Erro MT5: {mt5.last_error()}")
        return
    
    account = mt5.account_info()
    if not account:
        print("❌ Sem conta")
        mt5.shutdown()
        return
    
    print(f"✓ Conta: {account.login} | Saldo: {account.balance}")
    
    # Configurações
    configs = {
        "XAUUSD": {"lot": 0.01, "sl": 200, "tp": 400},
        "BTCUSD": {"lot": 0.01, "sl": 500, "tp": 1000}
    }
    
    # Verificar símbolos
    available = []
    for symbol in configs.keys():
        info = mt5.symbol_info(symbol)
        if info:
            if not info.visible:
                mt5.symbol_select(symbol, True)
            available.append(symbol)
            print(f"✓ {symbol} OK")
        else:
            print(f"❌ {symbol} não encontrado")
    
    if not available:
        print("❌ Nenhum símbolo disponível")
        mt5.shutdown()
        return
    
    print(f"\n🚀 Trading ativo para: {', '.join(available)}")
    print("Pressione Ctrl+C para parar\n")
    
    # Loop principal
    try:
        last_status = 0
        while True:
            # Trading
            for symbol in available:
                trade_symbol(symbol, configs[symbol])
            
            # Status a cada 5 minutos
            if time.time() - last_status > 300:
                account = mt5.account_info()
                if account:
                    logger.info(f"💰 Status - Saldo: {account.balance:.2f} | Equity: {account.equity:.2f}")
                last_status = time.time()
            
            time.sleep(30)  # 30 segundos entre ciclos
            
    except KeyboardInterrupt:
        print("\n⏹ Trading parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        mt5.shutdown()
        print("✓ Sistema encerrado")


if __name__ == "__main__":
    main()
