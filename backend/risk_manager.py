import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Dict, Optional

load_dotenv()

class RiskManager:
    """
    Comprehensive risk management system for autonomous trading.
    Enforces position limits, daily loss limits, and portfolio diversification.
    """
    
    def __init__(self):
        def get_env_float(key, default):
            val = os.getenv(key)
            if not val or val.strip() == "":
                return default
            try:
                # Remove common symbols like % or $ that users might include
                clean_val = val.replace('%', '').replace('$', '').strip()
                return float(clean_val)
            except ValueError:
                print(f"⚠️ Warning: Invalid value for {key}: '{val}'. Using default: {default}")
                return default

        self.initial_capital = get_env_float('INITIAL_CAPITAL', 10000.0)
        # STRICTER LIMITS FOR REAL MONEY
        self.max_daily_loss_pct = get_env_float('MAX_DAILY_LOSS_PCT', 2.0)
        self.max_position_size_pct = get_env_float('MAX_POSITION_SIZE_PCT', 5.0)
        self.max_stop_loss_pct = get_env_float('MAX_STOP_LOSS_PCT', 3.0)
        
        # Track daily performance
        self.daily_start_capital = None
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Position tracking
        self.open_positions: Dict[str, float] = {}  # symbol -> position_value
        
    def reset_daily_limits(self):
        """Reset daily tracking at market open"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.daily_start_capital = self.get_current_capital()
            self.daily_pnl = 0.0
            self.last_reset_date = today
            print(f"Daily limits reset. Starting capital: ${self.daily_start_capital:,.2f}")
    
    def get_current_capital(self) -> float:
        """Get current total capital - logic now depends on daily_pnl being updated by live equity"""
        if self.daily_start_capital is not None:
             return self.daily_start_capital + self.daily_pnl
        return self.initial_capital
    
    def can_trade(self) -> tuple[bool, str]:
        """
        Check if trading is allowed based on daily loss limits.
        Returns: (allowed, reason)
        """
        self.reset_daily_limits()
        
        current_capital = self.get_current_capital()
        daily_loss = self.daily_start_capital - current_capital
        daily_loss_pct = (daily_loss / self.daily_start_capital) * 100
        
        if daily_loss_pct >= self.max_daily_loss_pct:
            return False, f"Daily loss limit reached: {daily_loss_pct:.2f}% (max: {self.max_daily_loss_pct}%)"
        
        return True, "Trading allowed"
    
    def calculate_position_size(self, symbol: str, signal_confidence: float, current_price: float) -> tuple[int, float]:
        """
        Calculate position size using Kelly Criterion with safety caps.
        
        Args:
            symbol: Trading symbol
            signal_confidence: AI confidence (0-1)
            current_price: Current asset price
            
        Returns:
            (shares, position_value)
        """
        current_capital = self.get_current_capital()
        
        # Kelly Criterion: f = (bp - q) / b
        # where b = odds, p = win probability, q = 1-p
        # Simplified: use confidence as win probability
        win_prob = signal_confidence
        loss_prob = 1 - win_prob
        expected_return = 1.5  # Assume 1.5:1 reward/risk ratio
        
        kelly_fraction = (expected_return * win_prob - loss_prob) / expected_return
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25% (quarter Kelly)
        
        # Apply maximum position size limit
        max_position_value = current_capital * (self.max_position_size_pct / 100)
        kelly_position_value = current_capital * kelly_fraction
        
        position_value = min(kelly_position_value, max_position_value)
        
        # Crypto symbols often require fractional shares
        if "/" in symbol or "USD" in symbol:
            shares = round(position_value / current_price, 4) # 4 decimals for crypto
        else:
            shares = int(position_value / current_price) # Integer for stocks (default)
            
        actual_position_value = shares * current_price
        
        return shares, actual_position_value
    
    def validate_trade(self, symbol: str, shares: int, price: float, side: str) -> tuple[bool, str]:
        """
        Validate if a trade meets all risk criteria.
        
        Args:
            symbol: Trading symbol
            shares: Number of shares
            price: Entry price
            side: 'buy' or 'sell'
            
        Returns:
            (valid, reason)
        """
        # Check if trading is allowed
        can_trade, reason = self.can_trade()
        if not can_trade:
            return False, reason
        
        if side == 'buy':
            position_value = shares * price
            current_capital = self.get_current_capital()
            
            # Check position size limit
            position_pct = (position_value / current_capital) * 100
            if position_pct > self.max_position_size_pct:
                return False, f"Position size {position_pct:.2f}% exceeds limit {self.max_position_size_pct}%"
            
            # Check if we have enough capital
            if position_value > current_capital:
                return False, f"Insufficient capital: ${current_capital:,.2f} < ${position_value:,.2f}"
        
        return True, "Trade validated"
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """
        Calculate stop-loss price based on risk parameters.
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            
        Returns:
            stop_loss_price
        """
        if side == 'buy':
            # For long positions, stop loss is below entry
            stop_loss = entry_price * (1 - self.max_stop_loss_pct / 100)
        else:
            # For short positions, stop loss is above entry
            stop_loss = entry_price * (1 + self.max_stop_loss_pct / 100)
        
        return round(stop_loss, 2)
    
    def update_position(self, symbol: str, position_value: float):
        """Track open position"""
        self.open_positions[symbol] = position_value
    
    def close_position(self, symbol: str, pnl: float):
        """Close position and update P&L"""
        if symbol in self.open_positions:
            del self.open_positions[symbol]
        self.daily_pnl += pnl
        print(f"Position closed: {symbol}, P&L: ${pnl:,.2f}, Total Daily P&L: ${self.daily_pnl:,.2f}")
    
    def get_portfolio_exposure(self) -> float:
        """Get total portfolio exposure as percentage"""
        if not self.open_positions:
            return 0.0
        
        total_exposure = sum(self.open_positions.values())
        current_capital = self.get_current_capital()
        return (total_exposure / current_capital) * 100
    
    def get_risk_metrics(self, live_positions: Optional[List[Dict]] = None, current_equity: Optional[float] = None) -> Dict:
        """
        Get current risk metrics for monitoring.
        If live_positions is provided, it syncs the internal state with Alpaca.
        """
        # Sync with live equity if provided to calculate real daily P&L
        if current_equity is not None:
            if self.daily_start_capital is None:
                self.daily_start_capital = current_equity
            
            # Reset if it's a new day
            self.reset_daily_limits()
            if self.daily_start_capital is None: # In case reset hit
                 self.daily_start_capital = current_equity

            self.daily_pnl = current_equity - self.daily_start_capital
        
        current_capital = self.get_current_capital()
        
        # Sync with live positions if provided
        if live_positions is not None:
            self.open_positions = {p['symbol']: p['market_value'] for p in live_positions}
        
        daily_loss_pct = ((self.daily_start_capital - current_capital) / self.daily_start_capital) * 100
        
        return {
            "current_capital": current_capital,
            "daily_pnl": self.daily_pnl,
            "daily_loss_pct": daily_loss_pct,
            "daily_loss_limit": self.max_daily_loss_pct,
            "portfolio_exposure_pct": self.get_portfolio_exposure(),
            "open_positions": len(self.open_positions),
            "can_trade": self.can_trade()[0]
        }
