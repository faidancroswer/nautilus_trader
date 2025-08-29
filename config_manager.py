# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

"""
Configuration Manager - Unified Configuration System
Manages all configuration settings for the Enhanced Alligator Strategy
"""

import logging
import os
import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AlligatorConfig:
    """Configuration for Alligator indicator parameters."""
    period: int = 13
    shift: int = 8
    teeth_period: int = 8
    teeth_shift: int = 5
    lips_period: int = 5
    lips_shift: int = 3


@dataclass
class TechnicalIndicatorsConfig:
    """Configuration for technical indicators."""
    rsi_period: int = 14
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    bb_period: int = 20
    bb_std_dev: float = 2.0
    stoch_k_period: int = 14
    stoch_d_period: int = 3


@dataclass
class AIConfig:
    """Configuration for AI agent."""
    model: str = "llama3"
    host: str = "localhost"
    port: int = 11434
    timeout: int = 30
    max_retries: int = 3
    confidence_threshold: float = 0.7
    temperature: float = 0.3
    max_tokens: int = 300


@dataclass
class RiskConfig:
    """Configuration for risk management."""
    max_risk_per_trade: float = 0.01  # 1%
    max_daily_risk: float = 0.05      # 5%
    max_drawdown_limit: float = 0.15  # 15%
    enable_adaptive_sizing: bool = True
    max_concurrent_positions: int = 3
    recovery_mode_threshold: float = 0.10


@dataclass
class TradingConfig:
    """Configuration for trading parameters."""
    instrument_id: str = "EUR/USD.IDEALPRO"
    bar_type: str = "EUR/USD.IDEALPRO-1-MINUTE-BID-EXTERNAL"
    trade_size: float = 100000.0
    min_signal_strength: float = 0.6
    enable_market_orders: bool = True
    enable_limit_orders: bool = False


@dataclass
class PerformanceConfig:
    """Configuration for performance tracking."""
    output_dir: str = "performance_reports"
    enable_real_time_reporting: bool = True
    report_interval_minutes: int = 60
    enable_learning_insights: bool = True


@dataclass
class SystemConfig:
    """Configuration for system-wide settings."""
    log_level: str = "INFO"
    enable_debug_mode: bool = False
    max_memory_mb: int = 1024
    enable_performance_monitoring: bool = True


@dataclass
class EnhancedAlligatorConfig:
    """Master configuration for Enhanced Alligator Strategy."""
    alligator: AlligatorConfig
    technical_indicators: TechnicalIndicatorsConfig
    ai: AIConfig
    risk: RiskConfig
    trading: TradingConfig
    performance: PerformanceConfig
    system: SystemConfig

    def __init__(
        self,
        # Alligator parameters
        jaw_period: int = 13,
        jaw_shift: int = 8,
        teeth_period: int = 8,
        teeth_shift: int = 5,
        lips_period: int = 5,
        lips_shift: int = 3,

        # Technical indicators
        rsi_period: int = 14,
        macd_fast_period: int = 12,
        macd_slow_period: int = 26,
        macd_signal_period: int = 9,
        bb_period: int = 20,
        bb_std_dev: float = 2.0,
        stoch_k_period: int = 14,
        stoch_d_period: int = 3,

        # AI configuration
        ollama_model: str = "llama3",
        ollama_host: str = "localhost",
        ollama_port: int = 11434,
        ai_timeout: int = 30,
        ai_max_retries: int = 3,
        ai_confidence_threshold: float = 0.7,

        # Risk management
        max_risk_per_trade: float = 0.01,
        max_daily_risk: float = 0.05,
        max_drawdown_limit: float = 0.15,
        enable_adaptive_sizing: bool = True,
        max_concurrent_positions: int = 3,

        # Trading parameters
        instrument_id: str = "EUR/USD.IDEALPRO",
        bar_type: str = "EUR/USD.IDEALPRO-1-MINUTE-BID-EXTERNAL",
        trade_size: float = 100000.0,
        min_signal_strength: float = 0.6,

        # Performance tracking
        performance_output_dir: str = "performance_reports",
        enable_real_time_reporting: bool = True,

        # System settings
        log_level: str = "INFO",
        enable_debug_mode: bool = False
    ):
        """Initialize configuration with all parameters."""
        self.alligator = AlligatorConfig(
            period=jaw_period,
            shift=jaw_shift,
            teeth_period=teeth_period,
            teeth_shift=teeth_shift,
            lips_period=lips_period,
            lips_shift=lips_shift
        )

        self.technical_indicators = TechnicalIndicatorsConfig(
            rsi_period=rsi_period,
            macd_fast_period=macd_fast_period,
            macd_slow_period=macd_slow_period,
            macd_signal_period=macd_signal_period,
            bb_period=bb_period,
            bb_std_dev=bb_std_dev,
            stoch_k_period=stoch_k_period,
            stoch_d_period=stoch_d_period
        )

        self.ai = AIConfig(
            model=ollama_model,
            host=ollama_host,
            port=ollama_port,
            timeout=ai_timeout,
            max_retries=ai_max_retries,
            confidence_threshold=ai_confidence_threshold
        )

        self.risk = RiskConfig(
            max_risk_per_trade=max_risk_per_trade,
            max_daily_risk=max_daily_risk,
            max_drawdown_limit=max_drawdown_limit,
            enable_adaptive_sizing=enable_adaptive_sizing,
            max_concurrent_positions=max_concurrent_positions
        )

        self.trading = TradingConfig(
            instrument_id=instrument_id,
            bar_type=bar_type,
            trade_size=trade_size,
            min_signal_strength=min_signal_strength
        )

        self.performance = PerformanceConfig(
            output_dir=performance_output_dir,
            enable_real_time_reporting=enable_real_time_reporting
        )

        self.system = SystemConfig(
            log_level=log_level,
            enable_debug_mode=enable_debug_mode
        )


class ConfigManager:
    """
    Unified configuration management system for the Enhanced Alligator Strategy.

    This manager provides:
    - Configuration loading from multiple formats (JSON, YAML)
    - Environment variable integration
    - Configuration validation
    - Dynamic configuration reloading
    - Configuration templates and presets
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration manager.

        Parameters
        ----------
        config_dir : str
            Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.current_config: Optional[EnhancedAlligatorConfig] = None
        self.config_file: Optional[Path] = None

        logger.info(f"ConfigManager initialized - config directory: {config_dir}")

    def load_config(self, config_file: str = "enhanced_alligator_config.json") -> EnhancedAlligatorConfig:
        """
        Load configuration from file.

        Parameters
        ----------
        config_file : str
            Name of the configuration file

        Returns
        -------
        EnhancedAlligatorConfig
            Loaded configuration object
        """
        config_path = self.config_dir / config_file

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    if config_path.suffix.lower() == '.json':
                        config_data = json.load(f)
                    elif config_path.suffix.lower() in ['.yml', '.yaml']:
                        config_data = yaml.safe_load(f)
                    else:
                        raise ValueError(f"Unsupported config file format: {config_path.suffix}")

                self.current_config = self._dict_to_config(config_data)
                self.config_file = config_path

                logger.info(f"Configuration loaded from {config_path}")
                return self.current_config

            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                logger.info("Using default configuration")

        # Create default configuration
        self.current_config = self._create_default_config()
        self.save_config(config_file)

        return self.current_config

    def save_config(self, config_file: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Parameters
        ----------
        config_file : Optional[str]
            Name of the configuration file (uses current if None)
        """
        if not self.current_config:
            logger.warning("No configuration to save")
            return

        if config_file:
            self.config_file = self.config_dir / config_file
        elif not self.config_file:
            self.config_file = self.config_dir / "enhanced_alligator_config.json"

        try:
            config_data = self._config_to_dict(self.current_config)

            with open(self.config_file, 'w') as f:
                if self.config_file.suffix.lower() == '.json':
                    json.dump(config_data, f, indent=2)
                elif self.config_file.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(config_data, f, default_flow_style=False)

            logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.

        Parameters
        ----------
        updates : Dict[str, Any]
            Dictionary of configuration updates
        """
        if not self.current_config:
            logger.warning("No configuration loaded to update")
            return

        try:
            # Navigate through nested configuration structure
            for key_path, value in updates.items():
                keys = key_path.split('.')
                obj = self.current_config

                # Navigate to the correct attribute
                for key in keys[:-1]:
                    if hasattr(obj, key):
                        obj = getattr(obj, key)
                    else:
                        logger.warning(f"Invalid configuration path: {key_path}")
                        continue

                # Set the value
                final_key = keys[-1]
                if hasattr(obj, final_key):
                    setattr(obj, final_key, value)
                    logger.info(f"Updated configuration: {key_path} = {value}")
                else:
                    logger.warning(f"Unknown configuration key: {final_key}")

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")

    def validate_config(self, config: EnhancedAlligatorConfig) -> bool:
        """
        Validate configuration parameters.

        Parameters
        ----------
        config : EnhancedAlligatorConfig
            Configuration to validate

        Returns
        -------
        bool
            True if configuration is valid
        """
        try:
            # Validate Alligator parameters
            assert config.alligator.period > 0, "Alligator period must be positive"
            assert config.alligator.shift >= 0, "Alligator shift must be non-negative"
            assert config.alligator.teeth_period > 0, "Teeth period must be positive"
            assert config.alligator.teeth_shift >= 0, "Teeth shift must be non-negative"
            assert config.alligator.lips_period > 0, "Lips period must be positive"
            assert config.alligator.lips_shift >= 0, "Lips shift must be non-negative"

            # Validate technical indicators
            assert config.technical_indicators.rsi_period > 0, "RSI period must be positive"
            assert config.technical_indicators.macd_fast_period > 0, "MACD fast period must be positive"
            assert config.technical_indicators.macd_slow_period > config.technical_indicators.macd_fast_period, "MACD slow period must be greater than fast period"
            assert config.technical_indicators.bb_period > 0, "Bollinger Bands period must be positive"
            assert config.technical_indicators.bb_std_dev > 0, "Bollinger Bands std dev must be positive"

            # Validate AI configuration
            assert config.ai.timeout > 0, "AI timeout must be positive"
            assert config.ai.max_retries >= 0, "AI max retries must be non-negative"
            assert 0.0 <= config.ai.confidence_threshold <= 1.0, "AI confidence threshold must be between 0 and 1"

            # Validate risk configuration
            assert 0.0 < config.risk.max_risk_per_trade <= 1.0, "Max risk per trade must be between 0 and 1"
            assert 0.0 < config.risk.max_daily_risk <= 1.0, "Max daily risk must be between 0 and 1"
            assert 0.0 < config.risk.max_drawdown_limit <= 1.0, "Max drawdown limit must be between 0 and 1"

            # Validate trading configuration
            assert config.trading.trade_size > 0, "Trade size must be positive"
            assert 0.0 <= config.trading.min_signal_strength <= 1.0, "Min signal strength must be between 0 and 1"

            logger.info("Configuration validation passed")
            return True

        except AssertionError as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return False

    def create_preset(self, preset_name: str) -> EnhancedAlligatorConfig:
        """
        Create configuration preset.

        Parameters
        ----------
        preset_name : str
            Name of the preset ('conservative', 'moderate', 'aggressive')

        Returns
        -------
        EnhancedAlligatorConfig
            Configuration preset
        """
        if preset_name == 'conservative':
            return EnhancedAlligatorConfig(
                max_risk_per_trade=0.005,  # 0.5%
                max_daily_risk=0.02,       # 2%
                max_drawdown_limit=0.10,   # 10%
                ai_confidence_threshold=0.8,
                min_signal_strength=0.7,
                trade_size=50000.0
            )
        elif preset_name == 'moderate':
            return EnhancedAlligatorConfig(
                max_risk_per_trade=0.01,   # 1%
                max_daily_risk=0.05,       # 5%
                max_drawdown_limit=0.15,   # 15%
                ai_confidence_threshold=0.7,
                min_signal_strength=0.6,
                trade_size=100000.0
            )
        elif preset_name == 'aggressive':
            return EnhancedAlligatorConfig(
                max_risk_per_trade=0.02,   # 2%
                max_daily_risk=0.08,       # 8%
                max_drawdown_limit=0.20,   # 20%
                ai_confidence_threshold=0.6,
                min_signal_strength=0.5,
                trade_size=200000.0
            )
        else:
            logger.warning(f"Unknown preset: {preset_name}, using moderate")
            return self.create_preset('moderate')

    def _create_default_config(self) -> EnhancedAlligatorConfig:
        """Create default configuration."""
        return EnhancedAlligatorConfig()

    def _config_to_dict(self, config: EnhancedAlligatorConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary."""
        return asdict(config)

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> EnhancedAlligatorConfig:
        """Convert dictionary to configuration object."""
        try:
            # Extract nested dictionaries
            alligator = config_dict.get('alligator', {})
            technical_indicators = config_dict.get('technical_indicators', {})
            ai = config_dict.get('ai', {})
            risk = config_dict.get('risk', {})
            trading = config_dict.get('trading', {})
            performance = config_dict.get('performance', {})
            system = config_dict.get('system', {})

            # Create configuration object
            return EnhancedAlligatorConfig(
                # Alligator parameters
                jaw_period=alligator.get('period', 13),
                jaw_shift=alligator.get('shift', 8),
                teeth_period=alligator.get('teeth_period', 8),
                teeth_shift=alligator.get('teeth_shift', 5),
                lips_period=alligator.get('lips_period', 5),
                lips_shift=alligator.get('lips_shift', 3),

                # Technical indicators
                rsi_period=technical_indicators.get('rsi_period', 14),
                macd_fast_period=technical_indicators.get('macd_fast_period', 12),
                macd_slow_period=technical_indicators.get('macd_slow_period', 26),
                macd_signal_period=technical_indicators.get('macd_signal_period', 9),
                bb_period=technical_indicators.get('bb_period', 20),
                bb_std_dev=technical_indicators.get('bb_std_dev', 2.0),
                stoch_k_period=technical_indicators.get('stoch_k_period', 14),
                stoch_d_period=technical_indicators.get('stoch_d_period', 3),

                # AI configuration
                ollama_model=ai.get('model', 'llama3'),
                ollama_host=ai.get('host', 'localhost'),
                ollama_port=ai.get('port', 11434),
                ai_timeout=ai.get('timeout', 30),
                ai_max_retries=ai.get('max_retries', 3),
                ai_confidence_threshold=ai.get('confidence_threshold', 0.7),

                # Risk management
                max_risk_per_trade=risk.get('max_risk_per_trade', 0.01),
                max_daily_risk=risk.get('max_daily_risk', 0.05),
                max_drawdown_limit=risk.get('max_drawdown_limit', 0.15),
                enable_adaptive_sizing=risk.get('enable_adaptive_sizing', True),
                max_concurrent_positions=risk.get('max_concurrent_positions', 3),

                # Trading parameters
                instrument_id=trading.get('instrument_id', 'EUR/USD.IDEALPRO'),
                bar_type=trading.get('bar_type', 'EUR/USD.IDEALPRO-1-MINUTE-BID-EXTERNAL'),
                trade_size=trading.get('trade_size', 100000.0),
                min_signal_strength=trading.get('min_signal_strength', 0.6),

                # Performance tracking
                performance_output_dir=performance.get('output_dir', 'performance_reports'),
                enable_real_time_reporting=performance.get('enable_real_time_reporting', True),

                # System settings
                log_level=system.get('log_level', 'INFO'),
                enable_debug_mode=system.get('enable_debug_mode', False)
            )

        except Exception as e:
            logger.error(f"Error converting dict to config: {e}")
            return self._create_default_config()

    def reload_config(self) -> bool:
        """
        Reload configuration from file.

        Returns
        -------
        bool
            True if reload was successful
        """
        if not self.config_file or not self.config_file.exists():
            logger.warning("No configuration file to reload")
            return False

        try:
            old_config = self.current_config
            new_config = self.load_config(self.config_file.name)

            if self.validate_config(new_config):
                logger.info("Configuration reloaded successfully")
                return True
            else:
                logger.error("Reloaded configuration failed validation, keeping old config")
                self.current_config = old_config
                return False

        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            return False

    def get_environment_config(self) -> Dict[str, str]:
        """
        Get configuration from environment variables.

        Returns
        -------
        Dict[str, str]
            Environment configuration
        """
        env_config = {}

        # Trading configuration
        env_config['instrument_id'] = os.getenv('ENHANCED_ALLIGATOR_INSTRUMENT', 'EUR/USD.IDEALPRO')
        env_config['ollama_model'] = os.getenv('OLLAMA_MODEL', 'llama3')
        env_config['ollama_host'] = os.getenv('OLLAMA_HOST', 'localhost')
        env_config['ollama_port'] = os.getenv('OLLAMA_PORT', '11434')
        env_config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')

        # Risk configuration
        env_config['max_risk_per_trade'] = os.getenv('MAX_RISK_PER_TRADE', '0.01')
        env_config['max_daily_risk'] = os.getenv('MAX_DAILY_RISK', '0.05')
        env_config['max_drawdown_limit'] = os.getenv('MAX_DRAWDOWN_LIMIT', '0.15')

        return env_config
