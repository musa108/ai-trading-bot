import os
import asyncio
from dotenv import load_dotenv
from executor import TradingExecutor
from risk_manager import RiskManager
from wallet_manager import WalletManager

load_dotenv()

async def debug_trade():
    print("🛠️ Starting Trade Debugger...")
    
    risk_manager = RiskManager()
    wallet_manager = WalletManager()
    executor = TradingExecutor(risk_manager, wallet_manager)
    executor.start_trading()
    
    symbol = "BTC/USD"
    print(f"🔎 Testing trade for {symbol}...")
    
    # Force a Buy signal
    result = executor.execute_trade(
        symbol=symbol,
        signal="Buy",
        confidence=0.85,
        reason="DEBUG TEST"
    )
    
    print(f"📊 Result: {result}")

if __name__ == "__main__":
    asyncio.run(debug_trade())
