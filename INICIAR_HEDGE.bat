@echo off
REM ============================================
REM Estratégia de Hedge - Launcher Único
REM ============================================

echo ╔════════════════════════════════════════════╗
echo ║  ESTRATÉGIA DE HEDGE - EUR/USD ^& US30     ║
echo ║  Capital: $1000 ^| Lote: 0.025            ║
echo ╚════════════════════════════════════════════╝
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado! Instale Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Verificar MT5
echo 🔍 Verificando MetaTrader 5...
python -c "import MetaTrader5 as mt5; print('✅ MT5 OK' if mt5.version() else '❌ MT5 não encontrado')" 2>nul
if errorlevel 1 (
    echo ❌ MetaTrader5 não instalado ou não encontrado
    echo    Instale com: pip install MetaTrader5
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════════
echo  OPÇÕES:
echo ════════════════════════════════════════════
echo  [1] Executar EUR/USD + US30 (Recomendado)
echo  [2] Executar apenas EUR/USD
echo  [3] Executar apenas US30
echo  [4] Dashboard de Monitoramento
echo  [5] Sair
echo ════════════════════════════════════════════
echo.

set /p choice="Escolha uma opção (1-5): "

if "%choice%"=="1" goto multi
if "%choice%"=="2" goto eurusd
if "%choice%"=="3" goto us30
if "%choice%"=="4" goto dashboard
if "%choice%"=="5" goto end

echo ❌ Opção inválida
pause
exit /b 1

:multi
echo.
echo 🚀 Iniciando EUR/USD + US30...
echo 📊 Para monitorar, execute: python hedge_dashboard.py
echo ⏸️ Pressione Ctrl+C para parar
echo.
python hedge_multi_symbol.py
goto end

:eurusd
echo.
echo 🚀 Iniciando EUR/USD...
echo ⏸️ Pressione Ctrl+C para parar
echo.
python hedge_strategy.py --symbol EURUSD --lot 0.025 --magic 888999
goto end

:us30
echo.
echo 🚀 Iniciando US30...
echo ⏸️ Pressione Ctrl+C para parar
echo.
python hedge_strategy.py --symbol US30 --lot 0.025 --magic 888998
goto end

:dashboard
echo.
echo 📊 Iniciando Dashboard...
echo 🔄 Atualização a cada 15 segundos
echo ⏸️ Pressione Ctrl+C para sair
echo.
python hedge_dashboard.py --symbols EURUSD US30 --magic 888999
goto end

:end
echo.
echo ✅ Encerrado
pause
