# Configuração para execução da estratégia Alligator com MT5

# Instrumento para negociar (exemplo: EUR/USD)
INSTRUMENT_ID = "EUR/USD.FBS"  # Ajuste conforme necessário

# Tipo de barra (exemplo: 1 minuto)
BAR_TYPE = "EUR/USD.FBS-1-MINUTE-BID-INTERNAL"

# Tamanho da posição (em unidades da moeda base)
TRADE_SIZE = 1000

# Configurações do Alligator
JAW_PERIOD = 13
JAW_SHIFT = 8
TEETH_PERIOD = 8
TEETH_SHIFT = 5
LIPS_PERIOD = 5
LIPS_SHIFT = 3

# Configurações do MT5
MT5_PATH = ""  # Caminho para o terminal MT5, se necessário
ACCOUNT_LOGIN = ""  # Número da conta MT5
ACCOUNT_PASSWORD = ""  # Senha da conta MT5