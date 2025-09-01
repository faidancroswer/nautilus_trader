@echo off
title Trading AI - OURO e BITCOIN
color 0A

echo ========================================
echo   SISTEMA DE TRADING AI MULTI-SIMBOLO
echo   XAUUSD (Ouro) e BTCUSD (Bitcoin)
echo   Configurado para conta real FBS
echo ========================================
echo.

echo Verificando sistema...
python test_symbols.py

echo.
echo Iniciando menu de trading...
python start_multi_symbol_trading.py

pause
