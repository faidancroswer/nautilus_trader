# Enhanced Alligator Strategy Architecture

## Component Diagram

```mermaid
graph TD
    A[Market Data Feed] --> B[Nautilus Trader Engine]
    B --> C[Technical Indicators Suite]
    
    C --> D1[Alligator Indicator]
    C --> D2[RSI Indicator]
    C --> D3[MACD Indicator]
    C --> D4[Bollinger Bands Indicator]
    C --> D5[Stochastic Oscillator Indicator]
    
    D1 --> E[Indicator Values Processor]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    
    E --> F[Ollama AI Agent]
    
    F --> G[Risk Management System]
    
    G --> H[Order Management System]
    
    H --> I[Exchange Connector]
    
    I --> J[Live Trading Account]
    
    subgraph "Analysis Layer"
        C
        D1
        D2
        D3
        D4
        D5
        E
    end
    
    subgraph "Decision Layer"
        F
        G
    end
    
    subgraph "Execution Layer"
        H
        I
    end
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style F fill:#fff3e0
    style G fill:#ffebee
    style H fill:#f1f8e9
    style I fill:#fce4ec
    style J fill:#fafafa
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant MD as Market Data
    participant NT as Nautilus Trader
    participant TI as Technical Indicators
    participant AI as Ollama AI Agent
    participant RM as Risk Management
    participant OM as Order Management
    participant EX as Exchange
    
    MD->>NT: Real-time bars
    NT->>TI: Bar data
    TI->>TI: Calculate indicators
    TI-->>AI: Indicator values
    AI->>AI: Analyze market conditions
    AI-->>RM: Trading signal
    RM->>RM: Apply risk controls
    RM-->>OM: Order parameters
    OM->>EX: Submit order
    EX-->>OM: Order confirmation
    OM-->>RM: Execution report
    RM-->>AI: Trade result
```

## Class Structure

```mermaid
classDiagram
    class Strategy {
        +config: EnhancedAlligatorConfig
        +instrument: Instrument
        +alligator: AlligatorIndicator
        +rsi: RSIIndicator
        +macd: MACDIndicator
        +bollinger_bands: BollingerBandsIndicator
        +stochastic: StochasticIndicator
        +ai_agent: OllamaAgent
        +risk_manager: RiskManager
        +on_start()
        +on_bar(bar: Bar)
        +on_stop()
        +buy()
        +sell()
        +close_position()
    }
    
    class EnhancedAlligatorConfig {
        +instrument_id: InstrumentId
        +bar_type: BarType
        +trade_size: Decimal
        +ai_model: str
        +risk_params: RiskParams
    }
    
    class OllamaAgent {
        +model: str
        +host: str
        +port: int
        +analyze_market(context: MarketContext)
        +make_decision(indicators: IndicatorValues)
    }
    
    class RiskManager {
        +max_position_size: Decimal
        +max_drawdown: Decimal
        +volatility_adjustment: bool
        +calculate_position_size(account_info: AccountInfo)
        +check_risk_limits(signal: TradingSignal)
    }
    
    class MarketContext {
        +current_price: float
        +indicator_values: dict
        +account_info: AccountInfo
        +open_positions: list
        +historical_performance: dict
    }
    
    Strategy --> EnhancedAlligatorConfig
    Strategy --> OllamaAgent
    Strategy --> RiskManager
    Strategy --> MarketContext