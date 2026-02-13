import requests
import os
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

class MarketScanner:
    def __init__(self):
        self.stock_base_url = "https://www.alphavantage.co/query"
        self.crypto_base_url = "https://api.coingecko.com/api/v3"

    def get_stock_data(self, symbol: str):
        if not ALPHA_VANTAGE_API_KEY or ALPHA_VANTAGE_API_KEY == "your_key_here":
            return {"Note": "Using demo data. Please provide API key for live stock scanning."}
        
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": "5min",
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(self.stock_base_url, params=params)
        return response.json()

    def get_crypto_prices_bulk(self, coin_ids: list):
        url = f"{self.crypto_base_url}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error fetching crypto prices: {e}")
            return {}

    def get_crypto_price(self, coin_id: str):
        # Kept for backward compatibility, uses bulk method internally
        data = self.get_crypto_prices_bulk([coin_id])
        return data

    def get_betting_odds(self, sport: str = "upcoming"):
        # Placeholder for The Odds API or similar
        # For now, we simulate odds analysis for major upcoming events
        return [
            {"event": "Lakers vs Celtics", "odds_home": 1.85, "odds_away": 2.10, "sport": "Basketball"},
            {"event": "Man City vs Arsenal", "odds_home": 1.95, "odds_draw": 3.40, "odds_away": 3.20, "sport": "Soccer"},
            {"event": "Super Bowl LVIII", "odds_home": 1.90, "odds_away": 1.90, "sport": "Football"}
        ]

    def get_bond_data(self):
        # Alpha Vantage provides some Treasury yield data
        params = {
            "function": "TREASURY_YIELD",
            "interval": "monthly",
            "maturity": "10year",
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(self.stock_base_url, params=params)
        return response.json()
