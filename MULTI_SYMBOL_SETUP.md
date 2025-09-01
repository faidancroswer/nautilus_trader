# 🚀 Sistema de Trading AI Multi-Símbolo - XAUUSD & BTCUSD

Sistema modificado para operar com **OURO (XAUUSD)** e **BITCOIN (BTCUSD)** na conta real FBS.

## ✅ **Modificações Realizadas**

### 1. **Novos Arquivos Criados**
- `multi_symbol_ai_trading.py` - Sistema principal multi-símbolo
- `multi_symbol_config.json` - Configurações específicas por símbolo
- `test_symbols.py` - Teste de disponibilidade dos símbolos
- `start_multi_symbol_trading.py` - Menu de execução
- `start_gold_bitcoin_trading.bat` - Execução rápida no Windows

### 2. **Arquivo Original Modificado**
- `advanced_ai_alligator.py` - Adaptado para múltiplos símbolos

## 📊 **Configurações Específicas por Símbolo**

### 🥇 **XAUUSD (Ouro)**
```json
{
  "lot_size": 0.01,
  "sl_points": 200,
  "tp_points": 400,
  "max_risk_percent": 1.0,
  "min_spread": 30,
  "volatility_multiplier": 2.0,
  "trading_hours": "24/5"
}
```

### ₿ **BTCUSD (Bitcoin)**
```json
{
  "lot_size": 0.01,
  "sl_points": 500,
  "tp_points": 1000,
  "max_risk_percent": 0.5,
  "min_spread": 50,
  "volatility_multiplier": 5.0,
  "trading_hours": "24/7"
}
```

## 🎯 **Resultados dos Testes**

### ✅ **Símbolos Verificados no FBS**
- **XAUUSD**: ✓ Disponível (Spread: ~29 pontos, Preço: ~$2,650)
- **BTCUSD**: ✓ Disponível (Spread: ~2400 pontos, Preço: ~$108,000)

### ⚙️ **Configurações Técnicas Adaptadas**

#### **Para XAUUSD (Ouro)**
- **Alligator**: Períodos padrão (13, 8, 5)
- **RSI**: 14 períodos
- **MACD**: (12, 26, 9)
- **Stop Loss**: 200 pontos (adaptado ao spread)
- **Take Profit**: 400 pontos (Risk:Reward 1:2)

#### **Para BTCUSD (Bitcoin)**
- **Alligator**: Períodos maiores (21, 13, 8) para suavizar volatilidade
- **RSI**: 21 períodos (menos sensível)
- **MACD**: (12, 26, 9)
- **Stop Loss**: 500 pontos (volatilidade extrema)
- **Take Profit**: 1000 pontos (Risk:Reward 1:2)

## 🚀 **Como Executar**

### **Opção 1: Menu Interativo (Recomendado)**
```bash
python start_multi_symbol_trading.py
```

### **Opção 2: Windows (Duplo Clique)**
```
start_gold_bitcoin_trading.bat
```

### **Opção 3: Execução Direta**
```bash
# Sistema multi-símbolo (novo)
python multi_symbol_ai_trading.py

# Sistema avançado (modificado)
python advanced_ai_alligator.py
```

## 📋 **Menu de Opções**

1. **🚀 Trading Multi-Símbolo** - Sistema novo otimizado para ambos os símbolos
2. **⚡ Trading Rápido** - Sistema original otimizado para velocidade
3. **📊 Trading Avançado** - Sistema com análise completa (agora multi-símbolo)
4. **🔍 Testar Símbolos** - Verificar disponibilidade no broker
5. **📈 Ver Posições** - Status atual das posições
6. **⚙️ Configurar** - Setup do sistema

## 🎛️ **Configurações de Risco Adaptadas**

### **Gestão de Risco Global**
- **Risco máximo total**: 2.0% do equity
- **Risco por símbolo**: 
  - XAUUSD: 1.0% máximo
  - BTCUSD: 0.5% máximo (devido à volatilidade extrema)

### **Position Sizing Dinâmico**
- **Ouro**: Ajustado pela volatilidade (multiplicador 2.0x)
- **Bitcoin**: Ajustado pela volatilidade extrema (multiplicador 5.0x)
- **Lot mínimo**: 0.01 para ambos
- **Lot máximo**: 0.1 (Ouro) / 0.05 (Bitcoin)

## 🧠 **Prompts AI Otimizados**

### **Para XAUUSD**
```
GOLD TRADING - High volatility precious metal
Spread consideration: 30+ points minimum
Market sessions affect volatility significantly
```

### **Para BTCUSD**
```
BITCOIN TRADING - Extreme volatility cryptocurrency
24/7 market with high spreads: 50+ points
News and sentiment drive major moves
```

## ⚡ **Otimizações de Performance**

### **Execução Paralela**
- Cada símbolo é analisado independentemente
- Threading para execução simultânea
- Cache específico por símbolo

### **Configurações Ollama Otimizadas**
- **Timeout**: 10-12 segundos
- **Temperature**: 0.2 (decisões consistentes)
- **Max Tokens**: 50 (respostas rápidas)
- **Cache**: 45 segundos por símbolo

## 📊 **Monitoramento**

### **Logs Específicos**
- `multi_symbol_trading.log` - Sistema multi-símbolo
- `fast_ai_trading.log` - Sistema rápido
- `advanced_ai_trading.log` - Sistema avançado

### **Métricas por Símbolo**
- Número de posições ativas
- P&L por símbolo
- Frequência de decisões
- Taxa de acerto da IA

## ⚠️ **Considerações Importantes**

### **Spreads e Custos**
- **XAUUSD**: Spread ~29 pontos ($0.29)
- **BTCUSD**: Spread ~2400 pontos ($24.00)
- Considere os custos no cálculo de lucro

### **Volatilidade**
- **Ouro**: Volatilidade moderada-alta
- **Bitcoin**: Volatilidade extrema
- Position sizing adaptado automaticamente

### **Horários de Trading**
- **Ouro**: 24h/5 dias (segunda a sexta)
- **Bitcoin**: 24h/7 dias (incluindo fins de semana)

## 🔧 **Troubleshooting**

### **Se Ollama não funcionar**
```bash
# Verificar se está rodando
ollama list

# Reiniciar
ollama serve
```

### **Se símbolos não aparecerem**
- Verificar se estão habilitados no MT5
- Tentar símbolos alternativos: #GOLD, #BTC
- Contatar suporte FBS

### **Se houver erros de conexão**
- Verificar internet
- Reiniciar MT5
- Verificar credenciais da conta

## 🎉 **Sistema Pronto!**

O sistema foi **modificado com sucesso** para operar com:
- ✅ **XAUUSD (Ouro)** - Configurado e testado
- ✅ **BTCUSD (Bitcoin)** - Configurado e testado
- ✅ **Ollama LLM** - Integrado e otimizado
- ✅ **Nautilus Framework** - Compatível
- ✅ **FBS Broker** - Símbolos verificados

**Execute**: `python start_multi_symbol_trading.py` ou clique em `start_gold_bitcoin_trading.bat`
