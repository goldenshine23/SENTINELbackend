import requests
import pandas as pd
import numpy as np
import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import User  # Make sure this path is correct

FINNHUB_API_KEY = 'YOUR_NEWS_API_KEY'  # Replace with your actual key or use os.getenv
NEWS_ENDPOINT = 'https://newsapi.org/v2/everything'


# === Candle Pattern Detection ===
def detect_candle_patterns(df):
    df['bullish_engulfing'] = (
        (df['close'].shift(1) < df['open'].shift(1)) &
        (df['close'] > df['open']) &
        (df['close'] > df['open'].shift(1)) &
        (df['open'] < df['close'].shift(1))
    )
    df['bearish_engulfing'] = (
        (df['close'].shift(1) > df['open'].shift(1)) &
        (df['close'] < df['open']) &
        (df['open'] > df['close'].shift(1)) &
        (df['close'] < df['open'].shift(1))
    )
    df['pin_bar'] = (
        ((df['high'] - df[['open', 'close']].max(axis=1)) > 2 * (df[['open', 'close']].min(axis=1) - df['low'])) |
        ((df[['open', 'close']].min(axis=1) - df['low']) > 2 * (df['high'] - df[['open', 'close']].max(axis=1)))
    )
    df['doji'] = abs(df['close'] - df['open']) <= ((df['high'] - df['low']) * 0.1)
    df['inside_bar'] = (df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))
    return df


# === News Sentiment Filter ===
def check_news_sentiment(symbol: str, lookback_minutes=60) -> Optional[str]:
    now = datetime.datetime.utcnow()
    from_time = (now - datetime.timedelta(minutes=lookback_minutes)).isoformat()
    params = {
        'q': symbol,
        'from': from_time,
        'sortBy': 'publishedAt',
        'apiKey': FINNHUB_API_KEY,
        'language': 'en',
        'pageSize': 10
    }
    try:
        response = requests.get(NEWS_ENDPOINT, params=params)
        news = response.json()
        if 'articles' in news and len(news['articles']) > 0:
            titles = [article['title'] for article in news['articles']]
            sentiments = [
                'positive' if 'gain' in title.lower() or 'bull' in title.lower()
                else 'negative' if 'fall' in title.lower() or 'bear' in title.lower()
                else 'neutral'
                for title in titles
            ]
            overall_sentiment = max(set(sentiments), key=sentiments.count)
            return overall_sentiment
    except:
        pass
    return None


# === Trade Signal Generator ===
def generate_trade_signal(df: pd.DataFrame, db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.bot_active:
        return 'INACTIVE'

    df = detect_candle_patterns(df)
    last = df.iloc[-1]
    rsi = last.get('rsi', 50)
    sentiment = check_news_sentiment('EURUSD')

    if df['bullish_engulfing'].iloc[-1] and last['volume'] > df['volume'].rolling(10).mean().iloc[-1] and rsi < 30 and sentiment == 'positive':
        return 'BUY'
    elif df['bearish_engulfing'].iloc[-1] and last['volume'] > df['volume'].rolling(10).mean().iloc[-1] and rsi > 70 and sentiment == 'negative':
        return 'SELL'
    elif df['pin_bar'].iloc[-1] and sentiment == 'positive' and rsi < 40:
        return 'BUY'
    elif df['pin_bar'].iloc[-1] and sentiment == 'negative' and rsi > 60:
        return 'SELL'
    elif df['inside_bar'].iloc[-1] and sentiment == 'positive':
        return 'BUY BREAKOUT'
    elif df['inside_bar'].iloc[-1] and sentiment == 'negative':
        return 'SELL BREAKOUT'
    return 'HOLD'


# === Exported strategy functions for execution.py ===
async def analyze_symbol(metaapi, account_id, symbol: str) -> Optional[dict]:
    # Simulate candle fetching (replace with real data if needed)
    candles = await metaapi.history_api.get_candles(
        account_id, symbol, timeframe='1h',
        start=datetime.datetime.utcnow() - datetime.timedelta(hours=50)
    )
    df = pd.DataFrame(candles)
    df = detect_candle_patterns(df)

    score = 0
    if df['bullish_engulfing'].iloc[-1]:
        score += 3
    if df['pin_bar'].iloc[-1]:
        score += 2

    direction = 'buy' if df['bullish_engulfing'].iloc[-1] else 'sell' if df['bearish_engulfing'].iloc[-1] else 'hold'

    return {
        'score': score,
        'direction': direction,
        'volume': df['volume'].iloc[-1]
    }


def should_trade(analysis: dict) -> bool:
    return analysis and analysis.get('score', 0) >= 3 and analysis.get('direction') in ['buy', 'sell']


def has_open_trades(account, symbol: str) -> bool:
    # This should be implemented with your account trading API
    return False  # Placeholder for demo


def calculate_lot_size(balance, risk_percentage, stop_loss_pips, pip_value=10):
    """Calculate lot size based on risk percentage."""
    risk_amount = balance * (risk_percentage / 100)
    lot_size = risk_amount / (stop_loss_pips * pip_value)
    return round(lot_size, 2)


def calculate_pips(entry_price, exit_price, symbol):
    """Calculate pips based on entry and exit price."""
    multiplier = 10000 if 'JPY' not in symbol else 100
    return round((exit_price - entry_price) * multiplier, 1)


def risk_reward_ratio(entry_price, stop_loss_price, take_profit_price, symbol):
    """Calculate Risk-Reward Ratio."""
    stop_loss_pips = calculate_pips(entry_price, stop_loss_price, symbol)
    take_profit_pips = calculate_pips(take_profit_price, entry_price, symbol)
    if stop_loss_pips == 0:
        return 0
    return round(take_profit_pips / abs(stop_loss_pips), 2)


def signal_strength(risk_reward, trend_alignment, volatility_level):
    """Evaluate signal strength based on key parameters."""
    score = 0
    if risk_reward >= 2:
        score += 1
    if trend_alignment:
        score += 1
    if volatility_level < 0.5:
        score += 1
    return ["Weak", "Moderate", "Strong"][score]


# === Trade Scoring ===
def score_trade(trade_signal):
    # Dummy scoring logic (customize this based on your rules)
    score = 0
    if trade_signal.get('trend') == 'strong':
        score += 3
    if trade_signal.get('news_sentiment') == 'positive':
        score += 2
    if trade_signal.get('structure') == 'breakout':
        score += 1
    return score


# === Async Strategy Hook (Optional) ===
async def strategy(connection):
    print("Running strategy...")
    await connection.subscribe_to_market_data('EURUSD')
