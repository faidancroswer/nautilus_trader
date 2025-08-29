@echo off
echo ========================================
echo   SISTEMA DE TRADING AI COM OLLAMA
echo   Configurado para conta real FBS
echo ========================================
echo.

echo Verificando sistema...
python test_system.py

echo.
echo Iniciando sistema de trading...
python run_fast_trading.py

pause
