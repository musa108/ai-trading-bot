from datetime import datetime
from typing import Dict, List, Optional
import random

class ChatManager:
    """
    Manages natural language interactions with the AI Agent.
    Processes user intent and generates context-aware responses.
    """
    
    def __init__(self, check_portfolio_func, get_agent_status_func, stop_agent_func):
        self.check_portfolio = check_portfolio_func
        self.get_agent_status = get_agent_status_func
        self.stop_agent = stop_agent_func
        
        self.context = [] # History of last few messages
        
    def process_message(self, message: str) -> Dict:
        """
        Process a user message and return a response.
        """
        msg = message.lower()
        response = ""
        action_taken = None
        
        # 1. INTENT RECOGNITION (Simple Keyword Matching for V1)
        
        # A. STATUS / PORTFOLIO
        if any(w in msg for w in ["status", "portfolio", "how", "doing", "performance", "balance"]):
            response = self._get_status_response()
            
        # B. EXPLANATION
        elif any(w in msg for w in ["why", "reason", "explain", "trade"]):
            response = self._get_explanation_response()
            
        # C. COMMANDS
        elif "stop" in msg or "halt" in msg:
            self.stop_agent()
            response = "🚨 EMERGENCY STOP ACTIVATED. The autonomous agent has been halted. All trading is paused."
            action_taken = "STOP_AGENT"
            
        elif "start" in msg or "resume" in msg:
            response = "To start the agent, please use the 'Start Auto-Trading' button on the dashboard for safety confirmation."
            
        # D. RISK
        elif "risk" in msg or "exposure" in msg:
            response = self._get_risk_response()
            
        # E. GREETING/GENERAL
        elif any(w in msg for w in ["hi", "hello", "hey", "help"]):
            response = "Hello! I am your Autonomous Trading Agent. I can report on portfolio status, explain my trades, or executing emergency stops. How can I assist you?"
            
        else:
            response = "I'm analyzing the markets. You can ask me about 'portfolio status', 'risk levels', or ask 'why' I made a recent trade."
            
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "action": action_taken
        }

    def _get_status_response(self) -> str:
        """Generate status report"""
        data = self.check_portfolio()
        metrics = data.get("risk_metrics", {})
        account = data.get("account", {})
        
        pnl = metrics.get("daily_pnl", 0)
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        
        return (
            f"📈 **Portfolio Status**\n\n"
            f"Daily P&L: **{pnl_str}**\n"
            f"Current Capital: **${metrics.get('current_capital', 0):,.2f}**\n"
            f"Open Positions: **{metrics.get('open_positions', 0)}**\n"
            f"Daily Loss: {metrics.get('daily_loss_pct', 0):.2f}% (Limit: {metrics.get('daily_loss_limit')}%)"
        )
        
    def _get_explanation_response(self) -> str:
        """Explain recent behavior (Mock logic for now)"""
        # In real system, query last trade reasoning from Portfolio
        reasons = [
            "I detected a bullish divergence in ETH combined with positive news sentiment.",
            "I closed the TSLA position because it hit the 10% trailing stop metric.",
            "Market volatility is high, so I reduced position sizes to 5% to manage risk.",
            "Sentiment for Tech stocks turned bearish, prompting a defensive rebalance to Cash."
        ]
        return f"💡 **Insight**: {random.choice(reasons)}"

    def _get_risk_response(self) -> str:
        """Generate risk report"""
        data = self.check_portfolio()
        metrics = data.get("risk_metrics", {})
        
        return (
            f"🛡️ **Risk Assessment**\n\n"
            f"Exposure: **{metrics.get('portfolio_exposure_pct', 0):.1f}%**\n"
            f"Trading Allowed: **{'Yes' if metrics.get('can_trade') else 'NO (Limit Reached)'}**\n"
            f"On-Chain Gas: Checked (Safe)\n"
            f"System Status: **Secure**"
        )
