# Autonomous Trading System - Setup Guide

## 🚨 CRITICAL: Read Before Starting

This system will execute **REAL TRADES** with **REAL MONEY**. You can lose your entire capital. Only proceed if you:
- Understand trading risks and market volatility
- Have capital you can afford to lose
- Accept full responsibility for all trades

## Step 1: Get Alpaca API Credentials

1. Go to [https://alpaca.markets](https://alpaca.markets)
2. Create a free account
3. Navigate to "Paper Trading" section
4. Generate API keys (Key ID + Secret Key)

**IMPORTANT**: Start with **Paper Trading** (free, no real money) to test the system.

## Step 2: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   ALPACA_API_KEY=your_actual_key_here
   ALPACA_SECRET_KEY=your_actual_secret_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   
   # Crypto Wallet (Optional - for DeFi)
   CRYPTO_PRIVATE_KEY=your_private_key
   CRYPTO_RPC_URL=https://cloudflare-eth.com
   CRYPTO_WALLET_ADDRESS=your_public_address
   ```

3. Adjust risk parameters (optional):
   ```
   INITIAL_CAPITAL=10000
   MAX_DAILY_LOSS_PCT=2.0        # Stop trading if you lose 2% in a day
   MAX_POSITION_SIZE_PCT=10.0    # Max 10% of capital per trade
   MAX_STOP_LOSS_PCT=5.0         # 5% stop-loss per position
   ```

## Step 3: Install Dependencies

```bash
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Step 4: Start the Server

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 5: Test the System

### Check Portfolio Status
```bash
curl http://localhost:8000/portfolio/status
```

### Start Autonomous Trading
```bash
curl -X POST http://localhost:8000/execute/start
```

### Execute a Test Trade
```bash
curl -X POST "http://localhost:8000/execute/trade?symbol=AAPL&signal=Buy&confidence=0.85&reason=AI+Bullish+Signal"
```

### Stop Trading
```bash
curl -X POST http://localhost:8000/execute/stop
```

### Emergency Close All Positions
```bash
curl -X POST http://localhost:8000/portfolio/close_all
```

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/execute/start` | POST | Start autonomous trading |
| `/execute/stop` | POST | Stop autonomous trading |
| `/execute/trade` | POST | Execute single trade |
| `/portfolio/status` | GET | Get positions & account info |
| `/portfolio/performance` | GET | Get performance metrics |
| `/portfolio/close/{symbol}` | POST | Close specific position |
| `/portfolio/close_all` | POST | Emergency close all |

## Risk Management Features

✅ **Daily Loss Limit**: Trading stops if daily loss exceeds 2%  
✅ **Position Sizing**: Kelly Criterion with 10% max per trade  
✅ **Stop-Loss**: Automatic 5% stop-loss on all positions  
✅ **Bracket Orders**: Entry + stop-loss + take-profit in one order  
✅ **Trade Logging**: All trades saved to `trade_history.json`

## Transitioning to Live Trading

**Only after 2+ weeks of successful paper trading:**

1. Generate **Live Trading** API keys from Alpaca
2. Update `.env`:
   ```
   ALPACA_BASE_URL=https://api.alpaca.markets  # LIVE TRADING
   ```
3. Start with **minimum capital** ($1,000)
4. Monitor closely for first week
5. Gradually increase capital if performance is stable

## Monitoring & Safety

- Check `/portfolio/status` regularly
- Monitor `trade_history.json` for audit trail
- Use `/execute/stop` to pause trading anytime
- Use `/portfolio/close_all` for emergency exits
- Daily loss limit is **hard-coded** and cannot be exceeded

## Support

For Alpaca API issues: [https://alpaca.markets/docs](https://alpaca.markets/docs)  
For system issues: Check backend logs and `trade_history.json`
