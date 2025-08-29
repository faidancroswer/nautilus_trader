# Sistema de Trading AI com Ollama - FBS

Sistema de trading automatizado otimizado para velocidade usando Ollama LLM e MetaTrader 5, configurado para conta real FBS.

## 🚀 Características Principais

- **Trading Rápido**: Decisões em menos de 10 segundos
- **IA Avançada**: Usa Ollama com modelo Llama3:8b
- **Análise Técnica**: Alligator, RSI, MACD, Bollinger Bands
- **Gestão de Risco**: Position sizing dinâmico
- **Cache Inteligente**: Evita chamadas desnecessárias à IA
- **Conta Real FBS**: Configurado para ambiente de produção

## 📋 Pré-requisitos

### Software Necessário
1. **Python 3.8+**
2. **MetaTrader 5** (instalado e configurado com conta FBS)
3. **Ollama** (https://ollama.ai/download)

### Pacotes Python
- MetaTrader5
- pandas
- numpy
- requests

## 🛠️ Instalação Rápida

### 1. Configuração Automática
```bash
python setup_fast_trading.py
```

Este script irá:
- Verificar todos os pré-requisitos
- Instalar pacotes Python necessários
- Verificar/iniciar o Ollama
- Baixar o modelo Llama3:8b (se necessário)
- Criar arquivos de configuração

### 2. Execução
```bash
python run_fast_trading.py
```

## 📁 Estrutura dos Arquivos

```
nautilus_trader/
├── fast_ai_trading.py          # Sistema otimizado para velocidade
├── advanced_ai_alligator.py    # Sistema com análise completa
├── ollama_config.py            # Configuração do Ollama
├── setup_fast_trading.py       # Script de configuração
├── run_fast_trading.py         # Menu de execução
└── README_TRADING_AI.md        # Este arquivo
```

## ⚡ Modos de Operação

### 1. Trading Rápido (Recomendado)
- **Arquivo**: `fast_ai_trading.py`
- **Velocidade**: ~5-10 segundos por decisão
- **Características**:
  - Prompts otimizados
  - Cache inteligente
  - Análise técnica simplificada
  - Ideal para scalping

### 2. Trading Avançado
- **Arquivo**: `advanced_ai_alligator.py`
- **Velocidade**: ~15-30 segundos por decisão
- **Características**:
  - Análise técnica completa
  - Prompts detalhados
  - Mais indicadores
  - Ideal para swing trading

## 🔧 Configuração do Ollama

### Configurações de Velocidade
```python
# Configuração otimizada para velocidade
timeout = 8 segundos
max_retries = 1
temperature = 0.1
max_tokens = 30
cache_duration = 60 segundos
```

### Configurações de Precisão
```python
# Configuração otimizada para precisão
timeout = 20 segundos
max_retries = 3
temperature = 0.3
max_tokens = 100
cache_duration = 15 segundos
```

## 📊 Estratégia de Trading

### Indicadores Utilizados
1. **Alligator Indicator**
   - Jaw: SMA(13) deslocado 8 períodos
   - Teeth: SMA(8) deslocado 5 períodos
   - Lips: SMA(5) deslocado 3 períodos

2. **RSI (14 períodos)**
   - Overbought: > 70
   - Oversold: < 30

3. **MACD (12, 26, 9)**
   - Linha MACD
   - Linha de Sinal
   - Histograma

4. **Bollinger Bands (20, 2)**
   - Banda Superior
   - Média Móvel
   - Banda Inferior

### Lógica de Decisão
- **OPEN_BUY**: Alinhamento bullish + RSI < 70 + MACD > 0
- **OPEN_SELL**: Alinhamento bearish + RSI > 30 + MACD < 0
- **CLOSE_POSITION**: Sinais opostos ou condições extremas
- **HOLD**: Sinais mistos ou incertos

## ⚙️ Configurações de Risco

### Position Sizing
- **Risco por trade**: 1.5% do equity
- **Lote mínimo**: 0.01
- **Lote máximo**: 0.5
- **Ajuste por volatilidade**: Sim

### Stop Loss e Take Profit
- **SL dinâmico**: 50-150 pips (baseado na volatilidade)
- **TP dinâmico**: 2x o SL (Risk:Reward 1:2)
- **Trailing stop**: Não implementado

## 🚨 Configuração da Conta FBS

### 1. MetaTrader 5
1. Instale o MT5 da FBS
2. Faça login com sua conta real
3. Certifique-se de que o símbolo EURUSD está disponível
4. Habilite o trading automatizado

### 2. Configurações Importantes
- **Símbolo**: EURUSD
- **Timeframe**: M1 (1 minuto)
- **Magic Number**: 234000
- **Slippage**: 20 pontos

## 📈 Monitoramento

### Logs
- `fast_ai_trading.log`: Log do sistema rápido
- `advanced_ai_trading.log`: Log do sistema avançado
- `trading_startup.log`: Log de inicialização

### Métricas Importantes
- Tempo de resposta da IA
- Taxa de acerto das decisões
- Drawdown máximo
- Profit factor

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Ollama não responde
```bash
# Verificar se está rodando
ollama list

# Reiniciar serviço
ollama serve
```

#### 2. MT5 não conecta
- Verificar credenciais da conta
- Verificar conexão com internet
- Reiniciar MT5

#### 3. Modelo não encontrado
```bash
# Baixar modelo
ollama pull llama3:8b
```

#### 4. Erro de permissão de trading
- Habilitar trading automatizado no MT5
- Verificar se a conta permite EAs

### Comandos Úteis

```bash
# Verificar status do Ollama
curl http://localhost:11434/api/tags

# Testar modelo
ollama run llama3:8b "Test trading decision"

# Verificar logs
tail -f fast_ai_trading.log
```

## 📞 Suporte

### Verificação do Sistema
```bash
python run_fast_trading.py
# Escolha opção 4: Testar Conexões
# Escolha opção 5: Ver Status do Sistema
```

### Logs Detalhados
Para debug, edite o nível de log:
```python
logging.basicConfig(level=logging.DEBUG)
```

## ⚠️ Avisos Importantes

1. **Conta Real**: Este sistema está configurado para conta real. Use com cuidado.
2. **Risco**: Trading automatizado envolve riscos. Monitore sempre.
3. **Backtesting**: Teste em conta demo primeiro.
4. **Conectividade**: Mantenha conexão estável com internet.
5. **Recursos**: O sistema usa recursos do computador. Mantenha-o ligado.

## 🎯 Performance Esperada

### Sistema Rápido
- **Latência**: 5-10 segundos
- **Frequência**: A cada 30 segundos
- **Uso de CPU**: Baixo
- **Uso de RAM**: ~100MB

### Sistema Avançado
- **Latência**: 15-30 segundos
- **Frequência**: A cada 60 segundos
- **Uso de CPU**: Médio
- **Uso de RAM**: ~200MB

## 📝 Próximas Melhorias

- [ ] Interface gráfica
- [ ] Múltiplos símbolos
- [ ] Backtesting integrado
- [ ] Notificações por email/Telegram
- [ ] Dashboard web
- [ ] Análise de sentimento de mercado

---

**Desenvolvido para trading profissional com FBS**
**Use com responsabilidade e sempre monitore suas posições**
