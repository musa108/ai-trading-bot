import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest
from typing import Optional, Dict
from risk_manager import RiskManager
from wallet_manager import WalletManager

load_dotenv()

class TradingExecutor:
    """
    Autonomous trading execution engine using Alpaca API.
    Handles order placement, position management, and stop-loss automation.
    """
    
    def __init__(self, risk_manager: RiskManager, wallet_manager: WalletManager = None):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        self.risk_manager = risk_manager
        self.is_trading = False
        self.wallet_manager = wallet_manager
        
        if not self.api_key or not self.secret_key:
            print("⚠️ Warning: Alpaca API credentials not found. Trading functionality will be limited.")
            self.trading_client = None
            self.data_client = None
            self.crypto_data_client = None
            return
        
        # Initialize Alpaca clients
        is_paper = "paper" in self.base_url
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=is_paper)
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        self.crypto_data_client = CryptoHistoricalDataClient(self.api_key, self.secret_key)
        
        print(f"Trading Executor initialized (Paper Trading: {self.base_url})")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            if "/" in symbol: # Crypto symbol like BTC/USD
                request = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
                quote = self.crypto_data_client.get_crypto_latest_quote(request)
            else: # Stock symbol
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quote = self.data_client.get_stock_latest_quote(request)
            
            if symbol in quote:
                return float(quote[symbol].ask_price)
            return None
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def execute_trade(self, symbol: str, signal: str, confidence: float, reason: str) -> Dict:
        """
        Execute a trade based on AI signal.
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTC/USD')
            signal: 'Buy', 'Sell', or 'Hold'
            confidence: AI confidence score (0-1)
            reason: Reasoning for the trade
            
        Returns:
            Trade execution result
        """
        if not self.is_trading:
            return {"status": "error", "message": "Trading is not active"}
        
        if signal == 'Hold':
            return {"status": "skipped", "message": "Hold signal - no action taken"}
        
        # Get current price
        current_price = self.get_current_price(symbol)
        if not current_price:
            return {"status": "error", "message": f"Could not fetch price for {symbol}"}
        
        # Determine order side
        side = OrderSide.BUY if signal == 'Buy' else OrderSide.SELL
        
        # Calculate position size
        shares, position_value = self.risk_manager.calculate_position_size(
            symbol, confidence, current_price
        )
        
        if shares == 0:
            return {"status": "skipped", "message": "Position size too small"}
        
        # Validate trade
        valid, validation_msg = self.risk_manager.validate_trade(
            symbol, shares, current_price, side.value
        )
        
        if not valid:
            return {"status": "rejected", "message": validation_msg}
        
        # Calculate stop loss
        stop_loss_price = self.risk_manager.calculate_stop_loss(current_price, side.value)
        
        try:
            # Determine order parameters
            is_crypto = "/" in symbol or "USD" in symbol
            
            # Create order data
            if is_crypto:
                # Alpaca does NOT support bracket orders for crypto yet
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=shares,
                    side=side,
                    time_in_force=TimeInForce.GTC
                )
            else:
                # Create bracket order for stocks (entry + stop loss + take profit)
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=shares,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.BRACKET,
                    stop_loss=StopLossRequest(stop_price=stop_loss_price),
                    take_profit={"limit_price": current_price * 1.10}  # 10% profit target
                )
            
            order = self.trading_client.submit_order(order_data)
            
            # Update risk manager
            self.risk_manager.update_position(symbol, position_value)
            
            return {
                "status": "success",
                "order_id": order.id,
                "symbol": symbol,
                "side": side.value,
                "shares": shares,
                "entry_price": current_price,
                "stop_loss": stop_loss_price,
                "position_value": position_value,
                "confidence": confidence,
                "reason": reason
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Order failed: {str(e)}"}
    
    def get_positions(self) -> list:
        """Get all open positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "market_value": float(p.market_value),
                    "pnl": float(p.unrealized_pl),
                    "pnl_pct": float(p.unrealized_plpc) * 100
                }
                for p in positions
            ]
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []
    
    def close_position(self, symbol: str) -> Dict:
        """Close a specific position"""
        try:
            position = self.trading_client.get_open_position(symbol)
            pnl = float(position.unrealized_pl)
            
            # Close the position
            self.trading_client.close_position(symbol)
            
            # Update risk manager
            self.risk_manager.close_position(symbol, pnl)
            
            return {
                "status": "success",
                "symbol": symbol,
                "pnl": pnl,
                "message": f"Position closed with P&L: ${pnl:,.2f}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to close position: {str(e)}"}
    
    def close_all_positions(self) -> Dict:
        """Emergency close all positions"""
        try:
            positions = self.get_positions()
            results = []
            
            for position in positions:
                result = self.close_position(position['symbol'])
                results.append(result)
            
            return {
                "status": "success",
                "closed_positions": len(results),
                "details": results
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to close all positions: {str(e)}"}
    
    def start_trading(self):
        """Enable autonomous trading"""
        self.is_trading = True
        print("🟢 Autonomous trading STARTED")
    
    def stop_trading(self):
        """Disable autonomous trading"""
        self.is_trading = False
        print("🔴 Autonomous trading STOPPED")
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "pnl": float(account.equity) - float(account.last_equity),
                "pnl_pct": ((float(account.equity) - float(account.last_equity)) / float(account.last_equity)) * 100
            }
        except Exception as e:
            print(f"Error fetching account info: {e}")
            return {}
