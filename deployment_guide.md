# Enhanced Alligator Strategy Deployment Guide

## Overview
This document provides step-by-step instructions for deploying the enhanced Alligator strategy with AI integration in various environments.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+
- **Processor**: Intel i7/AMD Ryzen 7 or equivalent
- **Memory**: 16GB RAM minimum (32GB recommended)
- **Storage**: 50GB available disk space
- **Network**: Stable internet connection

### Software Requirements
1. **Python 3.11+**
2. **Git**
3. **Ollama 0.1.0+**
4. **Nautilus Trader dependencies**
5. **Docker (optional, for containerized deployment)**

## Installation Steps

### Step 1: Install Ollama
```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull required AI model
ollama pull llama3
```

### Step 2: Install Nautilus Trader
```bash
# Clone the Nautilus Trader repository
git clone https://github.com/nautechsystems/nautilus_trader.git
cd nautilus_trader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Nautilus Trader
pip install -e .
```

### Step 3: Install Additional Dependencies
```bash
# Install required Python packages
pip install pandas numpy requests matplotlib

# Install exchange connectors (if needed)
pip install nautilus-trader[ib]  # Interactive Brokers
pip install nautilus-trader[bybit]  # Bybit
```

### Step 4: Configure Environment
```bash
# Create .env file with required environment variables
cat > .env << EOF
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3
EOF
```

## Development Environment Setup

### Local Development
1. **Clone Strategy Repository**:
   ```bash
   git clone <strategy_repository_url>
   cd enhanced-alligator-strategy
   ```

2. **Install Development Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Configure IDE**:
   - Set up Python interpreter to use virtual environment
   - Install recommended extensions/plugins
   - Configure linting and formatting tools

### Testing Environment
1. **Set Up Test Data**:
   ```bash
   # Download historical data for backtesting
   python scripts/download_test_data.py
   ```

2. **Run Unit Tests**:
   ```bash
   python -m pytest tests/unit_tests/ -v
   ```

3. **Run Integration Tests**:
   ```bash
   python -m pytest tests/integration_tests/ -v
   ```

## Configuration

### Environment-Specific Configuration
Create separate configuration files for each environment:

#### Development Configuration (`config/dev.yaml`)
```yaml
# Development environment settings
risk_management:
  max_risk_percent: 1.0
  max_drawdown_percent: 10.0

ai_agent:
  temperature: 0.7
  timeout: 30

logging:
  level: DEBUG
  file: logs/dev_strategy.log
```

#### Staging Configuration (`config/staging.yaml`)
```yaml
# Staging environment settings
risk_management:
  max_risk_percent: 1.5
  max_drawdown_percent: 15.0

ai_agent:
  temperature: 0.5
  timeout: 20

logging:
  level: INFO
  file: logs/staging_strategy.log
```

#### Production Configuration (`config/prod.yaml`)
```yaml
# Production environment settings
risk_management:
  max_risk_percent: 2.0
  max_drawdown_percent: 20.0

ai_agent:
  temperature: 0.3
  timeout: 15

logging:
  level: WARNING
  file: logs/prod_strategy.log
```

## Deployment Process

### Step 1: Code Deployment
1. **Tag Release**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Deploy to Target Environment**:
   ```bash
   # For production deployment
   git checkout v1.0.0
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Configuration Deployment
1. **Copy Environment Configuration**:
   ```bash
   cp config/prod.yaml config/current.yaml
   ```

2. **Set Environment Variables**:
   ```bash
   export ENVIRONMENT=prod
   export CONFIG_FILE=config/current.yaml
   ```

### Step 3: Service Deployment
1. **Create Service Definition** (Linux systemd):
   ```ini
   # /etc/systemd/system/enhanced-alligator.service
   [Unit]
   Description=Enhanced Alligator Trading Strategy
   After=network.target

   [Service]
   Type=simple
   User=trading
   WorkingDirectory=/opt/enhanced-alligator
   Environment=ENVIRONMENT=prod
   Environment=CONFIG_FILE=config/prod.yaml
   ExecStart=/opt/enhanced-alligator/venv/bin/python strategy_runner.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

2. **Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable enhanced-alligator
   sudo systemctl start enhanced-alligator
   ```

### Step 4: Monitoring Setup
1. **Configure Log Monitoring**:
   ```bash
   # Set up log rotation
   sudo cp configs/logrotate/enhanced-alligator /etc/logrotate.d/
   
   # Configure log aggregation (if using ELK stack)
   sudo cp configs/filebeat/enhanced-alligator.yml /etc/filebeat/conf.d/
   ```

2. **Set Up Health Checks**:
   ```bash
   # Create health check script
   cat > health_check.sh << 'EOF'
   #!/bin/bash
   curl -f http://localhost:8080/health || exit 1
   EOF
   
   chmod +x health_check.sh
   ```

3. **Configure Alerts**:
   ```bash
   # Set up email/SMS alerts for critical issues
   # This depends on your monitoring solution (e.g., Prometheus, Grafana, etc.)
   ```

## Containerized Deployment (Docker)

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Expose ports
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "strategy_runner.py"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped

  enhanced-alligator:
    build: .
    depends_on:
      - ollama
    environment:
      - OLLAMA_HOST=ollama
      - OLLAMA_PORT=11434
      - ENVIRONMENT=prod
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    ports:
      - "8080:8080"
    restart: unless-stopped

volumes:
  ollama-data:
```

### Deployment Commands
```bash
# Build and deploy containers
docker-compose up -d

# Scale strategy instances
docker-compose up -d --scale enhanced-alligator=3

# View logs
docker-compose logs -f enhanced-alligator

# Update deployment
docker-compose pull
docker-compose up -d
```

## Cloud Deployment

### AWS Deployment
1. **EC2 Instance Setup**:
   ```bash
   # Launch EC2 instance with appropriate AMI
   aws ec2 run-instances \
     --image-id ami-0abcdef1234567890 \
     --instance-type t3.medium \
     --key-name my-key-pair \
     --security-group-ids sg-0123456789abcdef0 \
     --subnet-id subnet-0123456789abcdef0
   ```

2. **Deploy Application**:
   ```bash
   # SSH into instance and deploy
   ssh -i my-key-pair.pem ec2-user@<instance-ip>
   git clone <repository-url>
   cd enhanced-alligator-strategy
   # Follow installation steps above
   ```

3. **Set Up Load Balancer** (if running multiple instances):
   ```bash
   # Create Application Load Balancer
   aws elbv2 create-load-balancer \
     --name enhanced-alligator-alb \
     --subnets subnet-0123456789abcdef0 subnet-0123456789abcdef1 \
     --security-groups sg-0123456789abcdef0
   ```

### Kubernetes Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-alligator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: enhanced-alligator
  template:
    metadata:
      labels:
        app: enhanced-alligator
    spec:
      containers:
      - name: enhanced-alligator
        image: myregistry/enhanced-alligator:latest
        env:
        - name: ENVIRONMENT
          value: "prod"
        - name: OLLAMA_HOST
          value: "ollama-service"
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: enhanced-alligator-service
spec:
  selector:
    app: enhanced-alligator
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

## Monitoring and Maintenance

### Health Checks
1. **Application Health**:
   ```bash
   # Check if strategy is running
   curl -f http://localhost:8080/health
   
   # Check AI agent connectivity
   curl -f http://localhost:8080/ai-health
   ```

2. **System Health**:
   ```bash
   # Monitor system resources
   top -p $(pgrep python)
   
   # Check disk space
   df -h
   
   # Check network connectivity
   ping -c 4 ollama-service
   ```

### Log Management
```bash
# Rotate logs regularly
logrotate /etc/logrotate.d/enhanced-alligator

# Monitor critical logs
tail -f logs/strategy.log | grep -E "(ERROR|CRITICAL)"

# Archive old logs
find logs/ -name "*.log.*" -mtime +30 -delete
```

### Performance Monitoring
1. **Set Up Metrics Collection**:
   ```python
   # Add Prometheus metrics endpoint
   from prometheus_client import start_http_server, Counter, Gauge
   
   # Define metrics
   trades_counter = Counter('trades_total', 'Total number of trades')
   equity_gauge = Gauge('equity_value', 'Current account equity')
   
   # Update metrics in strategy
   trades_counter.inc()
   equity_gauge.set(current_equity)
   ```

2. **Configure Alerts**:
   ```yaml
   # Alert rules for Prometheus
   groups:
   - name: enhanced-alligator-alerts
     rules:
     - alert: StrategyDown
       expr: up{job="enhanced-alligator"} == 0
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "Enhanced Alligator strategy is down"
   ```

### Backup and Recovery
1. **Regular Backups**:
   ```bash
   # Backup configuration and logs
   tar -czf backups/$(date +%Y%m%d)_enhanced_alligator.tar.gz \
       config/ logs/ strategy_state.pkl
   
   # Upload to cloud storage
   aws s3 cp backups/$(date +%Y%m%d)_enhanced_alligator.tar.gz \
       s3://my-backups/enhanced-alligator/
   ```

2. **Disaster Recovery**:
   ```bash
   # Restore from backup
   aws s3 cp s3://my-backups/enhanced-alligator/20230101_enhanced_alligator.tar.gz .
   tar -xzf 20230101_enhanced_alligator.tar.gz
   ```

## Troubleshooting

### Common Issues and Solutions

#### Ollama Connection Issues
```bash
# Check if Ollama service is running
systemctl status ollama

# Restart Ollama service
systemctl restart ollama

# Test Ollama API
curl http://localhost:11434/api/tags
```

#### Strategy Initialization Failures
```bash
# Check strategy logs
tail -f logs/strategy.log

# Verify configuration
python validate_config.py

# Test individual components
python test_indicators.py
```

#### Performance Degradation
```bash
# Profile strategy performance
python -m cProfile -o profile.out strategy_runner.py

# Analyze profiling results
python -m pstats profile.out
```

### Rollback Procedures
1. **Rollback to Previous Version**:
   ```bash
   # Revert to previous Git tag
   git checkout v0.9.0
   
   # Restart services
   systemctl restart enhanced-alligator
   ```

2. **Restore from Backup**:
   ```bash
   # Stop strategy
   systemctl stop enhanced-alligator
   
   # Restore configuration and state
   tar -xzf backups/20230101_enhanced_alligator.tar.gz
   
   # Start strategy
   systemctl start enhanced-alligator
   ```

## Security Considerations

### Credential Management
1. **Use Secret Management**:
   ```bash
   # Store secrets in environment variables or secret management service
   export API_KEY=$(aws secretsmanager get-secret-value --secret-id trading-api-key --query SecretString --output text)
   ```

2. **Encrypt Sensitive Data**:
   ```python
   # Use encryption for sensitive configuration data
   from cryptography.fernet import Fernet
   
   # Encrypt configuration values
   key = Fernet.generate_key()
   cipher_suite = Fernet(key)
   encrypted_value = cipher_suite.encrypt(b"secret_value")
   ```

### Network Security
1. **Firewall Configuration**:
   ```bash
   # Restrict access to strategy ports
   ufw allow from 10.0.0.0/8 to any port 8080
   ufw deny 8080
   ```

2. **TLS/SSL Encryption**:
   ```bash
   # Use reverse proxy with SSL termination
   # Example nginx configuration
   server {
       listen 443 ssl;
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       location / {
           proxy_pass http://localhost:8080;
       }
   }
   ```

## Compliance and Auditing

### Audit Trail
1. **Log All Activities**:
   ```python
   # Implement comprehensive logging
   import logging
   logger = logging.getLogger(__name__)
   
   def execute_trade(signal):
       logger.info(f"Executing trade: {signal}")
       # ... trade execution logic
       logger.info(f"Trade executed successfully: {order_id}")
   ```

2. **Maintain Configuration History**:
   ```bash
   # Track configuration changes
   git log --oneline config/
   ```

### Regulatory Compliance
1. **Implement Required Controls**:
   ```python
   # Add pre-trade risk checks
   def pre_trade_check(order):
       if order.size > config.max_position_size:
           raise ValueError("Order size exceeds maximum position size")
       # ... additional checks
   ```

2. **Generate Compliance Reports**:
   ```python
   # Create daily compliance reports
   def generate_compliance_report():
       # ... report generation logic
       return report
   ```

This deployment guide provides a comprehensive framework for deploying the enhanced Alligator strategy across different environments. Proper deployment ensures reliable operation and optimal performance of the trading system.