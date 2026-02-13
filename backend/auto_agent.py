import asyncio
import time
from datetime import datetime
from typing import Dict, List
from scanner import MarketScanner
from analyzer import SentimentAnalyzer
from risk_manager import RiskManager
from executor import TradingExecutor
from wallet_manager import WalletManager
from portfolio import Portfolio

class AutoAgent:
    """
    The Brain of the Autonomous Trading System.
    Orchestrates scanning, analysis, risk checking, and execution in a continuous loop.
    """
    
    def __init__(self, executor: TradingExecutor, wallet_manager: WalletManager, portfolio: Portfolio = None):
        self.executor = executor
        self.wallet_manager = wallet_manager
        self.portfolio = portfolio
        self.scanner = MarketScanner()
        self.analyzer = SentimentAnalyzer()
        self.risk_manager = executor.risk_manager
        
        self.is_running = False
        self.loop_interval = 60 # Seconds between scan cycles
        self.active_strategies = ["sentiment_momentum", "mean_reversion"]
        
        print("🤖 AutoAgent initialized - Waiting for start command")

    async def start(self):
        """Start the autonomous trading loop"""
        self.is_running = True
        print("🚀 AutoAgent STARTED - Autonomous Mode Active")
        
        while self.is_running:
            try:
                await self.run_cycle()
                await asyncio.sleep(self.loop_interval)
            except Exception as e:
                print(f"❌ Error in AutoAgent loop: {e}")
                await asyncio.sleep(5) # Short pause on error

    def stop(self):
        """Stop the autonomous trading loop"""
        self.is_running = False
        print("🛑 AutoAgent STOPPED")

    async def run_cycle(self):
        """Execute one full trading cycle"""
        print(f"\n--- 🔄 Cycle Start: {datetime.now().strftime('%H:%M:%S')} ---")
        
        # 0. MONITOR RISK (Stop Losses)
        await self.monitor_risk()
        
        # 1. PERIODIC REBALANCE (e.g. every 60 cycles)
        await self.rebalance_portfolio()
        
        # 1. RISK CHECK: Can we trade?
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            print(f"⚠️ Trading Skipped: {reason}")
            return

        # 2. SCAN: Fetch potential opportunities
        # CRYPTO-ONLY MODE: 24/7 trading (stocks require market hours)
        assets = [
            {"symbol": "BTC/USD", "type": "crypto", "id": "bitcoin"},
            {"symbol": "ETH/USD", "type": "crypto", "id": "ethereum"},
        ]
        
        # 3. ANALYZE & EXECUTE
        for asset in assets:
            if not self.is_running: break # Stop immediately if commanded
            
            symbol = asset["symbol"]
            print(f"🔎 Analyzing {symbol}...")
            
            # A. Sentiment Analysis
            # In real system: fetch news here. mocking for demo logic.
            mock_news = [f"{symbol} reporting high growth and strong adoption."]
            sentiment = self.analyzer.get_aggregated_sentiment(mock_news)
            
            # B. Technical Analysis (Mocked via logic for now)
            # Real system would call scanner.get_technical_indicators(symbol)
            technical_signal = "Buy" # Placeholder
            
            # C. Decision Logic
            signal = "Hold"
            confidence = 0.0
            
            if sentiment == "Bullish" and technical_signal == "Buy":
                signal = "Buy"
                confidence = 0.85
            elif sentiment == "Bearish":
                signal = "Sell"
                confidence = 0.75
                
            # D. Execution
            if signal != "Hold":
                print(f"⚡ Signal Generated: {signal} {symbol} ({confidence*100}%)")
                
                # ROUTING: Stocks -> Alpaca, Crypto -> Check preference or default to Alpaca for now
                if asset["type"] == "crypto" and self.wallet_manager.w3:
                     # REAL DEFI EXECUTION
                     print(f"💡 Executing On-Chain Swap for {symbol}")
                     # In a real scenario, we'd map symbol to contract address (e.g. USDC -> ETH)
                     # For this demo we'll assume a swap of 0.01 ETH for testing
                     tx = self.wallet_manager.execute_swap(
                         token_in="ETH",
                         token_out=symbol,
                         amount=0.01
                     )
                     print(f"✅ On-Chain TX Sent: {tx['tx_hash']}")
                
                # Execute via existing Executor (Alpaca)
                result = self.executor.execute_trade(
                    symbol=symbol, 
                    signal=signal, 
                    confidence=confidence, 
                    reason=f"AutoAgent: {sentiment} Sentiment"
                )
                
                if result['status'] == 'success':
                    print(f"✅ Trade Executed: {result['side']} {result['shares']} {symbol}")
                    # Log to portfolio tracker
                    if self.portfolio:
                        self.portfolio.log_trade(result)
                else:
                    print(f"⚠️ Trade Rejected: {result['message']}")
            else:
                 print(f"Result: {symbol} - Hold (No strong signal)")
                 
        if self.wallet_manager.get_balance().get("balance_eth", 0) < 0.05:
            print("⚠️ Low ETH Balance for Gas")

    async def monitor_risk(self):
        """Monitor open positions for manual stop-loss (esp. for crypto)"""
        print("🛡️ Monitoring Active Risk...")
        try:
            positions = self.executor.get_positions()
            
            for pos in positions:
                symbol = pos['symbol']
                # Alpaca doesn't support bracket orders for crypto, so we monitor manually
                pnl_pct = pos['pnl_pct']
                
                # Check Stop Loss (e.g., -3%)
                if pnl_pct <= -self.risk_manager.max_stop_loss_pct:
                    print(f"🚨 STOP LOSS HIT for {symbol} ({pnl_pct:.2f}%)")
                    result = self.executor.close_position(symbol)
                    if result['status'] == 'success' and self.portfolio:
                        self.portfolio.close_trade(symbol, pos['current_price'], pos['pnl'])
                
                # Check Take Profit (Fallback, e.g., +10%)
                elif pnl_pct >= 10.0:
                    print(f"💰 TAKE PROFIT HIT for {symbol} ({pnl_pct:.2f}%)")
                    result = self.executor.close_position(symbol)
                    if result['status'] == 'success' and self.portfolio:
                        self.portfolio.close_trade(symbol, pos['current_price'], pos['pnl'])
        except Exception as e:
            print(f"Error in risk monitor: {e}")

    async def rebalance_portfolio(self):
        """
        Check and rebalance portfolio allocations.
        Target: 50% Crypto, 30% Stocks, 20% Cash
        """
        print("⚖️ Checking Portfolio Balance...")
        
        # 1. Get total portfolio value
        positions = self.executor.get_positions()
        account = self.executor.get_account_info()
        total_value = account.get("portfolio_value", 0)
        
        if total_value == 0: return

        # 2. Calculate current allocations
        crypto_value = sum(p["market_value"] for p in positions if p["symbol"] in ["BTC", "ETH"])
        stock_value = sum(p["market_value"] for p in positions if p["symbol"] not in ["BTC", "ETH"])
        
        crypto_alloc = crypto_value / total_value
        stock_alloc = stock_value / total_value
        
        print(f"Current Allocation: Crypto {crypto_alloc:.1%}, Stocks {stock_alloc:.1%}")
        
        # 3. Rebalance if deviation > 5%
        # (Simplified logic: Close overweight, Open underweight would be in main loop)
        if crypto_alloc > 0.55:
            print("📉 Crypto Overweight - Reducing exposure")
            # Logic to sell portion of crypto
            
        elif stock_alloc > 0.35:
             print("📉 Stocks Overweight - Reducing exposure")
             # Logic to sell portion of stocks
