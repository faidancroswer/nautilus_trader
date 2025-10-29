#!/usr/bin/env python3
"""
AI Performance Optimizer Agent
Automatically adjusts trading strategy for maximum performance and profit
Uses LLM to analyze performance and optimize parameters in real-time
"""

import logging
import time
import json
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import deque
import MetaTrader5 as mt5

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('ai_performance_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OptimizationMode(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    win_rate: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    last_update: datetime = None


@dataclass
class StrategyParameters:
    """Dynamic strategy parameters"""
    sl_points: float = 500
    tp_points: float = 1000
    max_risk_percent: float = 1.0
    max_lot_size: float = 0.01
    jaw_period: int = 21
    teeth_period: int = 13
    lips_period: int = 8
    min_volatility_threshold: float = 0.002
    max_spread_percentage: float = 0.5
    ai_temperature: float = 0.7
    cache_ttl: int = 30
    position_sizing_method: str = "fixed"  # fixed, volatility_based, kelly_criterion


@dataclass
class OptimizationResult:
    """Result of optimization cycle"""
    timestamp: datetime
    old_parameters: StrategyParameters
    new_parameters: StrategyParameters
    expected_improvement: float
    reasoning: str
    confidence: float


class LLMPerformanceOptimizer:
    """Advanced LLM-based performance optimizer"""

    def __init__(self, model: str = "llama3.2:3b", host: str = "localhost", port: int = 11434):
        self.model = model
        self.url = f"http://{host}:{port}/api/generate"
        self.session = requests.Session()

        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.parameters = StrategyParameters()
        self.optimization_history = deque(maxlen=100)

        # Trading history
        self.trade_history = []
        self.equity_curve = []
        self.performance_snapshots = []

        # Optimization settings
        self.optimization_mode = OptimizationMode.ADAPTIVE
        self.optimization_interval = 300  # 5 minutes
        self.min_trades_for_optimization = 5
        self.last_optimization = None

        # Performance targets
        self.target_win_rate = 0.55
        self.target_profit_factor = 1.5
        self.max_acceptable_drawdown = 0.10

        logger.info("LLM Performance Optimizer initialized")

    def record_trade(self, trade_info: Dict[str, Any]):
        """Record a completed trade for analysis"""
        trade = {
            'timestamp': datetime.now(),
            'ticket': trade_info.get('ticket'),
            'symbol': trade_info.get('symbol', 'BTCUSD'),
            'type': trade_info.get('type'),
            'volume': trade_info.get('volume', 0.01),
            'open_price': trade_info.get('open_price'),
            'close_price': trade_info.get('close_price'),
            'open_time': trade_info.get('open_time'),
            'close_time': trade_info.get('close_time'),
            'sl': trade_info.get('sl'),
            'tp': trade_info.get('tp'),
            'profit': trade_info.get('profit', 0.0),
            'commission': trade_info.get('commission', 0.0),
            'swap': trade_info.get('swap', 0.0),
            'strategy_params': asdict(self.parameters)
        }

        self.trade_history.append(trade)
        self._update_metrics()

        logger.info(f"Trade recorded: {trade['profit']:.2f} profit")

    def _update_metrics(self):
        """Update performance metrics from trade history"""
        if not self.trade_history:
            return

        # Basic metrics
        self.metrics.total_trades = len(self.trade_history)
        self.metrics.winning_trades = len([t for t in self.trade_history if t['profit'] > 0])
        self.metrics.losing_trades = len([t for t in self.trade_history if t['profit'] <= 0])

        # Profit/loss calculations
        profits = [t['profit'] for t in self.trade_history if t['profit'] > 0]
        losses = [t['profit'] for t in self.trade_history if t['profit'] <= 0]

        self.metrics.total_profit = sum(profits)
        self.metrics.total_loss = sum(losses)
        self.metrics.avg_win = np.mean(profits) if profits else 0
        self.metrics.avg_loss = np.mean(losses) if losses else 0

        # Win rate
        self.metrics.win_rate = self.metrics.winning_trades / max(self.metrics.total_trades, 1)

        # Profit factor
        self.metrics.profit_factor = abs(self.metrics.total_profit / max(abs(self.metrics.total_loss), 1))

        # Consecutive trades
        consecutive = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0

        for trade in reversed(self.trade_history):
            if trade['profit'] > 0:
                consecutive += 1
                max_consecutive_wins = max(max_consecutive_wins, consecutive)
            else:
                break

        self.metrics.consecutive_wins = max_consecutive_wins

        consecutive = 0
        for trade in reversed(self.trade_history):
            if trade['profit'] <= 0:
                consecutive += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive)
            else:
                break

        self.metrics.consecutive_losses = max_consecutive_losses

        # Drawdown calculation
        self._calculate_drawdown()

        # Sharpe ratio (simplified)
        if len(self.trade_history) > 1:
            returns = [t['profit'] for t in self.trade_history]
            self.metrics.sharpe_ratio = np.mean(returns) / max(np.std(returns), 0.001) * np.sqrt(252)

        self.metrics.last_update = datetime.now()

    def _calculate_drawdown(self):
        """Calculate drawdown from equity curve"""
        if not self.trade_history:
            return

        # Build equity curve
        equity = 0
        equity_curve = []

        for trade in self.trade_history:
            equity += trade['profit']
            equity_curve.append(equity)

        if not equity_curve:
            return

        equity_curve = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (running_max - equity_curve) / running_max

        self.metrics.max_drawdown = np.max(drawdown)
        self.metrics.current_drawdown = drawdown[-1] if len(drawdown) > 0 else 0

        self.equity_curve = equity_curve.tolist()

    def _generate_optimization_prompt(self) -> str:
        """Generate comprehensive prompt for LLM optimization"""

        prompt = f"""
        You are an expert quantitative trading analyst specializing in AI-driven cryptocurrency trading optimization.

        CURRENT PERFORMANCE METRICS:
        - Total Trades: {self.metrics.total_trades}
        - Win Rate: {self.metrics.win_rate:.2%}
        - Profit Factor: {self.metrics.profit_factor:.2f}
        - Average Win: ${self.metrics.avg_win:.2f}
        - Average Loss: ${self.metrics.avg_loss:.2f}
        - Max Drawdown: {self.metrics.max_drawdown:.2%}
        - Current Drawdown: {self.metrics.current_drawdown:.2%}
        - Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}
        - Consecutive Wins: {self.metrics.consecutive_wins}
        - Consecutive Losses: {self.metrics.consecutive_losses}

        CURRENT STRATEGY PARAMETERS:
        - Stop Loss: {self.parameters.sl_points} points
        - Take Profit: {self.parameters.tp_points} points
        - Max Risk: {self.parameters.max_risk_percent}%
        - Max Lot Size: {self.parameters.max_lot_size}
        - Alligator Jaw: {self.parameters.jaw_period}
        - Alligator Teeth: {self.parameters.teeth_period}
        - Alligator Lips: {self.parameters.lips_period}
        - Min Volatility Threshold: {self.parameters.min_volatility_threshold}
        - Max Spread: {self.parameters.max_spread_percentage}%
        - Position Sizing: {self.parameters.position_sizing_method}

        TARGET PERFORMANCE:
        - Win Rate: {self.target_win_rate:.0%}
        - Profit Factor: {self.target_profit_factor:.1f}
        - Max Drawdown: {self.max_acceptable_drawdown:.0%}

        RECENT TRADES (last 10):
        """

        # Add recent trades
        recent_trades = self.trade_history[-10:]
        for i, trade in enumerate(recent_trades, 1):
            prompt += f"""
        {i}. {trade['type']} {trade['volume']} lots
           Profit: ${trade['profit']:.2f}
           Duration: {(trade['close_time'] - trade['open_time']).total_seconds()/60:.0f} min
           """

        prompt += f"""

        OPTIMIZATION MODE: {self.optimization_mode.value.upper()}

        Analyze the performance and provide specific parameter adjustments to improve profitability.
        Consider:
        1. Risk-adjusted returns
        2. Market volatility adaptation
        3. Drawdown control
        4. Win rate improvement
        5. Profit factor optimization

        Provide your response in this exact JSON format:
        {{
            "analysis": "Brief analysis of current performance",
            "recommendations": {{
                "sl_points": <number>,
                "tp_points": <number>,
                "max_risk_percent": <number>,
                "max_lot_size": <number>,
                "jaw_period": <number>,
                "teeth_period": <number>,
                "lips_period": <number>,
                "min_volatility_threshold": <number>,
                "max_spread_percentage": <number>,
                "position_sizing_method": "fixed|volatility_based|kelly_criterion"
            }},
            "expected_improvement": <number>,
            "confidence": <number between 0-1>,
            "reasoning": "Detailed explanation of the optimization strategy"
        }}

        Keep parameter changes conservative and realistic. Values must be reasonable for BTCUSD trading.
        """

        return prompt

    def _call_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call LLM for optimization analysis"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 1000
            }

            response = self.session.post(self.url, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                # Extract JSON from response
                try:
                    # Find JSON in the response
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1

                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        optimization_data = json.loads(json_str)
                        return optimization_data
                    else:
                        logger.error("No JSON found in LLM response")
                        return None

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM JSON response: {e}")
                    logger.error(f"Response text: {response_text[:500]}...")
                    return None
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None

    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and constrain parameter values"""
        validated = {}

        # Stop loss (100-2000 points)
        validated['sl_points'] = max(100, min(2000, float(params.get('sl_points', self.parameters.sl_points))))

        # Take profit (200-4000 points)
        validated['tp_points'] = max(200, min(4000, float(params.get('tp_points', self.parameters.tp_points))))

        # Risk percentage (0.1-5%)
        validated['max_risk_percent'] = max(0.1, min(5.0, float(params.get('max_risk_percent', self.parameters.max_risk_percent))))

        # Lot size (0.01-0.1)
        validated['max_lot_size'] = max(0.01, min(0.1, float(params.get('max_lot_size', self.parameters.max_lot_size))))

        # Alligator periods (5-50)
        validated['jaw_period'] = max(5, min(50, int(params.get('jaw_period', self.parameters.jaw_period))))
        validated['teeth_period'] = max(3, min(30, int(params.get('teeth_period', self.parameters.teeth_period))))
        validated['lips_period'] = max(3, min(20, int(params.get('lips_period', self.parameters.lips_period))))

        # Volatility threshold (0.001-0.01)
        validated['min_volatility_threshold'] = max(0.001, min(0.01, float(params.get('min_volatility_threshold', self.parameters.min_volatility_threshold))))

        # Spread percentage (0.1-2%)
        validated['max_spread_percentage'] = max(0.1, min(2.0, float(params.get('max_spread_percentage', self.parameters.max_spread_percentage))))

        # Position sizing method
        valid_methods = ['fixed', 'volatility_based', 'kelly_criterion']
        validated['position_sizing_method'] = params.get('position_sizing_method', self.parameters.position_sizing_method)
        if validated['position_sizing_method'] not in valid_methods:
            validated['position_sizing_method'] = 'fixed'

        return validated

    def optimize(self) -> Optional[OptimizationResult]:
        """Run optimization cycle"""
        if len(self.trade_history) < self.min_trades_for_optimization:
            logger.info(f"Insufficient trades for optimization ({len(self.trade_history)} < {self.min_trades_for_optimization})")
            return None

        # Check if enough time has passed since last optimization
        if self.last_optimization:
            time_since_last = datetime.now() - self.last_optimization
            if time_since_last.total_seconds() < self.optimization_interval:
                logger.debug(f"Skipping optimization - last optimization {time_since_last.total_seconds():.0f}s ago")
                return None

        logger.info("Starting performance optimization cycle...")

        # Generate prompt and call LLM
        prompt = self._generate_optimization_prompt()
        optimization_data = self._call_llm(prompt)

        if not optimization_data:
            logger.error("Failed to get optimization recommendations from LLM")
            return None

        # Validate parameters
        validated_params = self._validate_parameters(optimization_data.get('recommendations', {}))

        # Create optimization result
        old_params = StrategyParameters(**asdict(self.parameters))
        new_params = StrategyParameters(**validated_params)

        result = OptimizationResult(
            timestamp=datetime.now(),
            old_parameters=old_params,
            new_parameters=new_params,
            expected_improvement=optimization_data.get('expected_improvement', 0.0),
            reasoning=optimization_data.get('reasoning', ''),
            confidence=optimization_data.get('confidence', 0.0)
        )

        # Apply optimizations if confidence is high enough
        if result.confidence >= 0.6:
            self.parameters = new_params
            self.optimization_history.append(result)
            self.last_optimization = datetime.now()

            logger.info("✅ Optimization applied successfully!")
            logger.info(f"Expected improvement: {result.expected_improvement:.1%}")
            logger.info(f"Confidence: {result.confidence:.1%}")
            logger.info(f"Reasoning: {result.reasoning[:200]}...")

            # Log parameter changes
            self._log_parameter_changes(old_params, new_params)

        else:
            logger.info(f"⚠️ Optimization skipped - low confidence: {result.confidence:.1%}")

        return result

    def _log_parameter_changes(self, old: StrategyParameters, new: StrategyParameters):
        """Log parameter changes"""
        changes = []

        if old.sl_points != new.sl_points:
            changes.append(f"SL: {old.sl_points} → {new.sl_points}")
        if old.tp_points != new.tp_points:
            changes.append(f"TP: {old.tp_points} → {new.tp_points}")
        if old.max_risk_percent != new.max_risk_percent:
            changes.append(f"Risk: {old.max_risk_percent}% → {new.max_risk_percent}%")
        if old.max_lot_size != new.max_lot_size:
            changes.append(f"Lot: {old.max_lot_size} → {new.max_lot_size}")
        if old.min_volatility_threshold != new.min_volatility_threshold:
            changes.append(f"Min Vol: {old.min_volatility_threshold} → {new.min_volatility_threshold}")
        if old.position_sizing_method != new.position_sizing_method:
            changes.append(f"Sizing: {old.position_sizing_method} → {new.position_sizing_method}")

        if changes:
            logger.info(f"Parameter changes: {', '.join(changes)}")

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        return {
            'current_metrics': asdict(self.metrics),
            'current_parameters': asdict(self.parameters),
            'optimization_history': [
                {
                    'timestamp': opt.timestamp.isoformat(),
                    'expected_improvement': opt.expected_improvement,
                    'confidence': opt.confidence,
                    'reasoning': opt.reasoning[:200] + '...' if len(opt.reasoning) > 200 else opt.reasoning
                }
                for opt in list(self.optimization_history)[-5:]
            ],
            'performance_summary': {
                'total_trades': self.metrics.total_trades,
                'win_rate': f"{self.metrics.win_rate:.1%}",
                'profit_factor': f"{self.metrics.profit_factor:.2f}",
                'total_pnl': self.metrics.total_profit + self.metrics.total_loss,
                'max_drawdown': f"{self.metrics.max_drawdown:.1%}",
                'sharpe_ratio': f"{self.metrics.sharpe_ratio:.2f}"
            }
        }

    def export_trade_history(self, filename: str = None) -> str:
        """Export trade history to CSV"""
        if filename is None:
            filename = f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        if self.trade_history:
            df = pd.DataFrame(self.trade_history)
            df.to_csv(filename, index=False)
            logger.info(f"Trade history exported to {filename}")
            return filename
        else:
            logger.warning("No trade history to export")
            return filename


class PerformanceMonitorThread(threading.Thread):
    """Background thread for continuous performance monitoring"""

    def __init__(self, optimizer: LLMPerformanceOptimizer):
        super().__init__(daemon=True)
        self.optimizer = optimizer
        self.running = False

    def run(self):
        """Main monitoring loop"""
        self.running = True
        logger.info("Performance monitoring thread started")

        while self.running:
            try:
                # Run optimization
                result = self.optimizer.optimize()

                # Generate periodic reports
                if not result:
                    self._log_status_update()

                # Sleep for optimization interval
                time.sleep(self.optimizer.optimization_interval)

            except Exception as e:
                logger.error(f"Error in monitoring thread: {e}")
                time.sleep(60)  # Wait before retrying

    def _log_status_update(self):
        """Log periodic status update"""
        if self.optimizer.metrics.total_trades > 0:
            logger.info(f"Status Update: {self.optimizer.metrics.total_trades} trades, "
                       f"Win Rate: {self.optimizer.metrics.win_rate:.1%}, "
                       f"P&L: ${self.optimizer.metrics.total_profit + self.optimizer.metrics.total_loss:.2f}")

    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        logger.info("Performance monitoring thread stopped")


# Integration with existing strategy
def integrate_with_strategy(strategy_instance):
    """Integrate optimizer with existing trading strategy"""
    optimizer = LLMPerformanceOptimizer()
    monitor = PerformanceMonitorThread(optimizer)

    # Hook into strategy's trade execution
    original_close_position = strategy_instance.close_position
    original_open_position = strategy_instance.open_position_optimized

    def enhanced_close_position(position):
        """Enhanced close position with optimization tracking"""
        result = original_close_position(position)

        # Record trade for optimization
        if result:
            trade_info = {
                'ticket': position.ticket,
                'type': 'SELL' if position.type == mt5.POSITION_TYPE_BUY else 'BUY',
                'volume': position.volume,
                'open_price': position.price_open,
                'close_price': position.price_current,
                'open_time': datetime.fromtimestamp(position.time_open),
                'close_time': datetime.now(),
                'sl': position.sl,
                'tp': position.tp,
                'profit': position.profit,
                'commission': position.swap,
                'swap': position.swap
            }
            optimizer.record_trade(trade_info)

        return result

    # Apply parameter updates to strategy
    def update_strategy_parameters():
        """Update strategy parameters from optimizer"""
        config = strategy_instance.config
        config.sl_points = optimizer.parameters.sl_points
        config.tp_points = optimizer.parameters.tp_points
        config.max_risk_percent = optimizer.parameters.max_risk_percent
        config.max_lot_size = optimizer.parameters.max_lot_size
        config.jaw_period = optimizer.parameters.jaw_period
        config.teeth_period = optimizer.parameters.teeth_period
        config.lips_period = optimizer.parameters.lips_period
        config.min_volatility_threshold = optimizer.parameters.min_volatility_threshold
        config.max_spread_percentage = optimizer.parameters.max_spread_percentage

        logger.info("Strategy parameters updated from optimizer")

    # Hook into optimization results
    original_optimize = optimizer.optimize
    def enhanced_optimize():
        result = original_optimize()
        if result and result.confidence >= 0.6:
            update_strategy_parameters()
        return result

    optimizer.optimize = enhanced_optimize
    strategy_instance.close_position = enhanced_close_position

    # Start monitoring
    monitor.start()

    logger.info("Performance optimizer integrated with strategy")

    return optimizer, monitor


if __name__ == "__main__":
    # Test the optimizer
    optimizer = LLMPerformanceOptimizer()

    # Add some sample trades for testing
    sample_trades = [
        {'ticket': 123, 'type': 'BUY', 'volume': 0.01, 'open_price': 45000, 'close_price': 45500,
         'open_time': datetime.now() - timedelta(hours=1), 'close_time': datetime.now() - timedelta(minutes=30),
         'sl': 44500, 'tp': 46000, 'profit': 50.0, 'commission': 0.5, 'swap': 0.0},
        {'ticket': 124, 'type': 'SELL', 'volume': 0.01, 'open_price': 45200, 'close_price': 44800,
         'open_time': datetime.now() - timedelta(minutes=25), 'close_time': datetime.now() - timedelta(minutes=5),
         'sl': 45700, 'tp': 44500, 'profit': 40.0, 'commission': 0.5, 'swap': 0.0},
        {'ticket': 125, 'type': 'BUY', 'volume': 0.01, 'open_price': 44900, 'close_price': 44700,
         'open_time': datetime.now() - timedelta(minutes=4), 'close_time': datetime.now(),
         'sl': 44400, 'tp': 45900, 'profit': -20.0, 'commission': 0.5, 'swap': 0.0},
        {'ticket': 126, 'type': 'SELL', 'volume': 0.01, 'open_price': 44800, 'close_price': 45000,
         'open_time': datetime.now() - timedelta(minutes=3), 'close_time': datetime.now(),
         'sl': 45300, 'tp': 44300, 'profit': -20.0, 'commission': 0.5, 'swap': 0.0},
        {'ticket': 127, 'type': 'BUY', 'volume': 0.01, 'open_price': 45050, 'close_price': 45300,
         'open_time': datetime.now() - timedelta(minutes=2), 'close_time': datetime.now(),
         'sl': 44550, 'tp': 46050, 'profit': 25.0, 'commission': 0.5, 'swap': 0.0}
    ]

    for trade in sample_trades:
        optimizer.record_trade(trade)

    # Run optimization
    result = optimizer.optimize()

    if result:
        print("Optimization completed successfully!")
        print(f"Expected improvement: {result.expected_improvement:.1%}")
        print(f"Confidence: {result.confidence:.1%}")
        print(f"Reasoning: {result.reasoning}")

    # Generate report
    report = optimizer.get_optimization_report()
    print("\nPerformance Report:")
    print(json.dumps(report, indent=2, default=str))