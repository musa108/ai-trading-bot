from datetime import datetime
from typing import Dict, List
import json
import os

class Portfolio:
    """
    Portfolio tracking and performance analytics.
    Maintains trade history and calculates performance metrics.
    """
    
    def __init__(self):
        self.trades_file = "trade_history.json"
        self.trades: List[Dict] = self.load_trades()
        self.initial_capital = 10000.0
    
    def load_trades(self) -> List[Dict]:
        """Load trade history from file"""
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_trades(self):
        """Save trade history to file"""
        with open(self.trades_file, 'w') as f:
            json.dump(self.trades, f, indent=2)
    
    def log_trade(self, trade_data: Dict):
        """
        Log a trade execution.
        
        Args:
            trade_data: Trade details from executor
        """
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "order_id": trade_data.get("order_id"),
            "symbol": trade_data.get("symbol"),
            "side": trade_data.get("side"),
            "shares": trade_data.get("shares"),
            "entry_price": trade_data.get("entry_price"),
            "stop_loss": trade_data.get("stop_loss"),
            "position_value": trade_data.get("position_value"),
            "confidence": trade_data.get("confidence"),
            "reason": trade_data.get("reason"),
            "status": "open"
        }
        
        self.trades.append(trade_record)
        self.save_trades()
        print(f"Trade logged: {trade_record['symbol']} {trade_record['side']} x{trade_record['shares']}")
    
    def close_trade(self, symbol: str, exit_price: float, pnl: float):
        """
        Mark a trade as closed and record P&L.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            pnl: Profit/Loss
        """
        # Find the most recent open trade for this symbol
        for trade in reversed(self.trades):
            if trade['symbol'] == symbol and trade['status'] == 'open':
                trade['status'] = 'closed'
                trade['exit_price'] = exit_price
                trade['exit_timestamp'] = datetime.now().isoformat()
                trade['pnl'] = pnl
                trade['pnl_pct'] = (pnl / trade['position_value']) * 100
                self.save_trades()
                print(f"Trade closed: {symbol}, P&L: ${pnl:,.2f} ({trade['pnl_pct']:.2f}%)")
                break
    
    def get_open_trades(self) -> List[Dict]:
        """Get all currently open trades"""
        return [t for t in self.trades if t['status'] == 'open']
    
    def get_closed_trades(self) -> List[Dict]:
        """Get all closed trades"""
        return [t for t in self.trades if t['status'] == 'closed']
    
    def get_performance_metrics(self) -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Returns:
            Performance statistics
        """
        closed_trades = self.get_closed_trades()
        
        if not closed_trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0
            }
        
        # Calculate basic metrics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in closed_trades)
        
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = abs(sum(t['pnl'] for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Simplified Sharpe ratio (assuming risk-free rate = 0)
        returns = [t['pnl_pct'] for t in closed_trades]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_dev = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 0
        sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "best_trade": max(closed_trades, key=lambda x: x['pnl'])['pnl'] if closed_trades else 0,
            "worst_trade": min(closed_trades, key=lambda x: x['pnl'])['pnl'] if closed_trades else 0
        }
    
    def get_daily_summary(self) -> Dict:
        """Get today's trading summary"""
        today = datetime.now().date()
        today_trades = [
            t for t in self.trades
            if datetime.fromisoformat(t['timestamp']).date() == today
        ]
        
        closed_today = [t for t in today_trades if t['status'] == 'closed']
        daily_pnl = sum(t['pnl'] for t in closed_today)
        
        return {
            "date": today.isoformat(),
            "trades_executed": len(today_trades),
            "trades_closed": len(closed_today),
            "daily_pnl": round(daily_pnl, 2),
            "trades": today_trades
        }
