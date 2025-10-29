@echo off
title TRADING OURO E BITCOIN - SISTEMA ROBUSTO
color 0A

echo ==========================================
echo   TRADING AI - XAUUSD (OURO) e BTCUSD (BITCOIN)
echo   Sistema Robusto com Fallback Tecnico
echo ==========================================
echo.

echo Escolha o sistema para executar:
echo.
echo 1. Sistema DIRETO (Recomendado - Sempre Funciona)
echo 2. Sistema SIMPLES (Com IA se disponivel)
echo 3. Sistema ROBUSTO (IA + Fallback Tecnico)
echo 4. Sistema MULTI-SIMBOLO (IA Avancada)
echo 5. Testar Conexoes
echo 0. Sair
echo.

set /p choice="Digite sua escolha (1-5): "

if "%choice%"=="1" (
    echo.
    echo Executando Sistema DIRETO...
    python direct_gold_bitcoin_trading.py
) else if "%choice%"=="2" (
    echo.
    echo Executando Sistema SIMPLES...
    python simple_gold_bitcoin_trading.py
) else if "%choice%"=="3" (
    echo.
    echo Executando Sistema ROBUSTO...
    python robust_multi_symbol_trading.py
) else if "%choice%"=="4" (
    echo.
    echo Executando Sistema MULTI-SIMBOLO...
    python multi_symbol_ai_trading.py
) else if "%choice%"=="5" (
    echo.
    echo Testando conexoes...
    python test_symbols.py
) else if "%choice%"=="0" (
    echo Saindo...
    exit
) else (
    echo Opcao invalida!
)

echo.
pause
