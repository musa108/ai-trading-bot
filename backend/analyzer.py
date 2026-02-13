import os
try:
    from transformers import BertTokenizer, BertForSequenceClassification, pipeline
    import torch
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

class SentimentAnalyzer:
    def __init__(self):
        self.nlp = None
        # Check if we should use the heavy ML model (can cause OOM on small servers)
        self.use_ml = os.getenv('USE_ML_ANALYSIS', 'true').lower() == 'true'
        
        if ML_AVAILABLE and self.use_ml:
            try:
                print("🧠 Loading Sentiment Model (FinBERT)...")
                # FinBERT is specifically trained for financial sentiment
                self.tokenizer = BertTokenizer.from_pretrained('yiyanghkust/finbert-tone')
                self.model = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-tone')
                self.nlp = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)
                print("✅ Model loaded successfully")
            except Exception as e:
                print(f"⚠️ Could not load ML model (likely OOM): {e}")
                print("🔄 Falling back to Keyword Analysis")
                self.nlp = None
        else:
            if not self.use_ml:
                print("ℹ️ ML Analysis disabled via environment variable")
            else:
                print("ℹ️ ML libraries not installed. Using Keyword Analysis.")

    def analyze_news(self, text_list):
        if not text_list:
            return []
        
        if self.nlp:
            try:
                return self.nlp(text_list)
            except Exception:
                pass
        
        # Fallback Keywords
        results = []
        positive_keywords = ["surge", "up", "bullish", "profit", "gain", "higher", "positive", "high", "strong", "growth", "adoption", "breakout"]
        negative_keywords = ["drop", "down", "bearish", "loss", "lower", "negative", "low", "caution", "weak", "decline"]
        
        for text in text_list:
            score = 0
            text_lower = text.lower()
            for k in positive_keywords:
                if k in text_lower: score += 1
            for k in negative_keywords:
                if k in text_lower: score -= 1
            
            label = "Neutral"
            if score > 0: label = "Positive"
            elif score < 0: label = "Negative"
            results.append({"label": label, "score": score})
            
        return results

    def analyze_betting_value(self, event_data):
        # EV calculation: (Probability of Winning * Amount Won per Bet) - (Probability of Losing * Amount Lost per Bet)
        # Simplified for demo: Look for "value" in odds vs a simulated AI probability
        probabilities = {
            "Lakers vs Celtics": 0.58,  # AI thinks Lakers 58%
            "Man City vs Arsenal": 0.55, # AI thinks Man City 55%
            "Super Bowl LVIII": 0.52     # AI thinks 49ers 52%
        }
        
        event = event_data["event"]
        ai_prob = probabilities.get(event, 0.5)
        decimal_odds = event_data["odds_home"]
        
        ev = (ai_prob * (decimal_odds - 1)) - (1 - ai_prob)
        
        return {
            "ev": round(ev, 2),
            "suggestion": "Bet" if ev > 0.05 else "Avoid",
            "confidence": f"{int(ai_prob * 100)}%"
        }

    def get_aggregated_sentiment(self, text_list):
        results = self.analyze_news(text_list)
        if not results:
            return "Neutral"
        
        # Simple weighted logic or majority vote
        sentiments = [res['label'] for res in results]
        positive = sentiments.count('Positive')
        negative = sentiments.count('Negative')
        
        if positive > negative:
            return "Bullish"
        elif negative > positive:
            return "Bearish"
        else:
            return "Neutral"
