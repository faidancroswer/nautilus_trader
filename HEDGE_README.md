# Estratégia de Hedge - EUR/USD & US30

Implementação da estratégia de swing trade com hedge gradual baseada na metodologia do Sr. Johnny.

## 📋 Características

- ✅ **Sem Stop-Loss**: Proteção via hedge gradual
- ✅ **Análise de Equilíbrio**: Linha mensal + MA 20 semanal
- ✅ **Multi-Símbolo**: EUR/USD + US30 simultaneamente
- ✅ **Proteção de Notícias**: Evita operar em eventos de alto impacto
- ✅ **Espaçamento Adaptativo**: 700-1500 pips baseado em ATR
- ✅ **Lote Fixo**: 0.025 por símbolo ($1000 capital)

## 🚀 Início Rápido

### 1. Executar Estratégia para Um Símbolo

```bash
# EUR/USD
python hedge_strategy.py --symbol EURUSD --lot 0.025

# US30
python hedge_strategy.py --symbol US30 --lot 0.025
```

### 2. Executar Multi-Símbolo (Recomendado)

```bash
python hedge_multi_symbol.py
```

Isso executará EUR/USD e US30 simultaneamente em processos separados.

### 3. Monitorar via Dashboard

```bash
python hedge_dashboard.py
```

Dashboard atualiza a cada 15 segundos com:
- Informações da conta
- Posições ativas por símbolo  
- Análise de equilíbrio
- P&L em tempo real
- Próximos níveis de entrada

## 📊 Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `hedge_strategy.py` | Estratégia principal com análise de equilíbrio e lógica de hedge |
| `hedge_multi_symbol.py` | Launcher para executar EUR/USD + US30 simultaneamente |
| `hedge_dashboard.py` | Dashboard de monitoramento em tempo real |
| `hedge/hedge.txt` | Transcrição da estratégia original (YouTube) |
| `hedge/hedge.jpg` | Diagrama visual da estratégia |

## 🎯 Lógica da Estratégia

### Análise de Entrada

1. **Mensal (Compass Principal)**
   - Identificar topo e fundo dos últimos 4-5 anos
   - Calcular linha de equilíbrio: `(topo + fundo) / 2`
   - Abaixo do equilíbrio → APENAS COMPRAS
   - Acima do equilíbrio → APENAS VENDAS

2. **Semanal (Confirmação)**
   - Média Móvel Simples de 20 períodos
   - Contador de velas (10 verdes + 10 vermelhas = equilíbrio)

### Gestão de Posições

**Entradas Escalonadas:**
- Máximo 4 posições por direção
- Espaçamento adaptativo: 700-1500 pips (baseado em ATR)
- Lote fixo: 0.025 (sem martingale)

**Hedge Gradual:**
1. Se 4 posições numa direção e mercado continua contra
2. Abrir posições na direção oposta (1 por vez)
3. Máximo 4 hedges também
4. Quando mercado retorna, fechar pares (1 hedge + 1 original)
5. Usar lucros das hedges para pagar prejuízos das originais
6. Objetivo: Sair no zero a zero ou lucro

### Proteção de Notícias

Evita operar próximo de:
- NFP (Primeira sexta do mês, 13:30 UTC)
- FOMC (Quartas-feiras, 19:00 UTC)
- CPI US (13:30 UTC)
- ECB (12:45 UTC)

## ⚙️ Parâmetros Configuráveis

```bash
python hedge_strategy.py \
  --symbol EURUSD \
  --lot 0.025 \
  --max-positions 4 \
  --min-spacing 700 \
  --normal-spacing 1000 \
  --max-spacing 1500 \
  --magic 888999
```

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--symbol` | EURUSD | Símbolo para negociar |
| `--lot` | 0.025 | Tamanho do lote fixo |
| `--max-positions` | 4 | Máximo de posições por direção |
| `--min-spacing` | 700 | Espaçamento mínimo em pips |
| `--normal-spacing` | 1000 | Espaçamento normal em pips |
| `--max-spacing` | 1500 | Espaçamento máximo em pips |
| `--magic` | 888999 | Magic number (EUR) / 888998 (US30) |

## ⚠️ Avisos Importantes

> **ALTO RISCO**: Esta estratégia não usa stop-loss e pode gerar drawdowns significativos (30-40%).

> **CAPITAL ADEQUADO**: Use apenas capital que pode suportar drawdowns prolongados.

> **HEDGE PACIÊNCIA**: Pode levar dias/semanas para sair de situações de hedge.

> **MONITORAMENTO**: Acompanhe constantemente via dashboard ou MyFXBook.

## 📈 Exemplo de Uso

### Iniciar Sistema Completo

1. **Terminal 1** - Executar estratégias:
```bash
python hedge_multi_symbol.py
```

2. **Terminal 2** - Monitorar:
```bash
python hedge_dashboard.py
```

### Saída Esperada

```
🚀 ESTRATÉGIA DE HEDGE - MULTI-SÍMBOLO
════════════════════════════════════════════════════════════

Símbolos: EUR/USD + US30
Capital: $1,000 USD
Lote fixo: 0.025 por símbolo
Máximo: 4 posições por direção, por símbolo
Proteção: Eventos de notícias

════════════════════════════════════════════════════════════

✅ Símbolos disponíveis: EURUSD, US30

🔄 Iniciando processo para EURUSD...
🔄 Iniciando processo para US30...

✅ Todas as estratégias foram iniciadas!
📊 Use 'python hedge_dashboard.py' para monitorar
```

## 📊 MyFXBook

Configure sua conta no MyFXBook para auditoria pública:
- Conecte sua conta FBS ao MyFXBook
- Torne a conta pública
- Compartilhe link para acompanhamento

## 🛠️ Troubleshooting

### MT5 não inicializa
```python
# Verificar se MT5 está instalado e rodando
import MetaTrader5 as mt5
print(mt5.version())
```

### Símbolos não encontrados
- Abrir MT5 manualmente
- Market Watch → Símbolos
- Habilitar EURUSD e US30

### Ordens rejeitadas
- Verificar saldo suficiente
- Verificar se símbolo permite trading
- Verificar horário de mercado

## 📝 Logs

Todos os logs são salvos em:
- `hedge_strategy.log` - Log detalhado da estratégia
- `hedge_multi_symbol.log` - Log do launcher multi-símbolo

## 🎓 Referências

- Vídeo Original: https://youtu.be/nIFEP4Zq2Lo
- Transcrição: `hedge/hedge.txt`
- Diagrama: `hedge/hedge.jpg`

## 📞 Suporte

Para dúvidas sobre a implementação:
1. Revisar logs (`hedge_strategy.log`)
2. Verificar dashboard para status atual
3. Consultar `implementation_plan.md` para detalhes técnicos

---

**Desenvolvido com base na estratégia do Sr. Johnny**  
*Swing Trade • Sem Stop Loss • Hedge Gradual*
