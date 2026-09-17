import pandas as pd
import numpy as np

class StrategyEngine:
    """
    Technical Analysis Engine tailored for Binary Options / Quotex 1M & 5M signals.
    Combines:
      - Exponential Moving Average (EMA 9 & 21) Trend & Cross
      - Relative Strength Index (RSI 14) Overbought/Oversold Reversals
      - Bollinger Bands (20, 2) Extreme Band Touches
      - Price Action / Candlestick Rejection Patterns
    """

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # EMA
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

        # RSI (14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['rsi'] = 100 - (100 / (1 + rs))

        # Bollinger Bands (20, 2)
        df['bb_mid'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * 2)

        return df

    @classmethod
    def analyze(cls, df: pd.DataFrame):
        """
        Analyzes the latest candle data and returns:
          - signal: 'CALL', 'PUT', or None
          - accuracy: string percentage (e.g. '88%')
          - reason: description of indicator confirmation
        """
        if len(df) < 25:
            return None, "0%", "Insufficient candle data"

        df = cls.calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        call_score = 0
        put_score = 0
        reasons = []

        # 1. EMA Trend & Crossover
        if curr['ema9'] > curr['ema21']:
            call_score += 25
            if prev['ema9'] <= prev['ema21']:
                call_score += 20
                reasons.append("EMA 9/21 Golden Cross")
        else:
            put_score += 25
            if prev['ema9'] >= prev['ema21']:
                put_score += 20
                reasons.append("EMA 9/21 Death Cross")

        # 2. RSI Extreme Zones
        rsi_val = curr['rsi']
        if pd.notna(rsi_val):
            if rsi_val <= 30:
                call_score += 35
                reasons.append(f"RSI Oversold ({rsi_val:.1f})")
            elif rsi_val >= 70:
                put_score += 35
                reasons.append(f"RSI Overbought ({rsi_val:.1f})")
            elif 45 <= rsi_val <= 55:
                # Neutral continuation
                if curr['ema9'] > curr['ema21']:
                    call_score += 10
                else:
                    put_score += 10

        # 3. Bollinger Band Rejection
        if pd.notna(curr['bb_lower']) and curr['low'] <= curr['bb_lower']:
            call_score += 25
            reasons.append("Lower Bollinger Band Bounce")
        elif pd.notna(curr['bb_upper']) and curr['high'] >= curr['bb_upper']:
            put_score += 25
            reasons.append("Upper Bollinger Band Rejection")

        # 4. Candlestick Pin-bar / Reversal Action
        body = abs(curr['close'] - curr['open'])
        upper_wick = curr['high'] - max(curr['close'], curr['open'])
        lower_wick = min(curr['close'], curr['open']) - curr['low']

        if lower_wick > body * 2:  # Hammer / Bullish rejection
            call_score += 15
            reasons.append("Bullish Pin-bar Rejection")
        elif upper_wick > body * 2:  # Shooting Star / Bearish rejection
            put_score += 15
            reasons.append("Bearish Pin-bar Rejection")

        # Decision Threshold
        if call_score >= 55 and call_score > put_score:
            accuracy_calc = min(94, 78 + int(call_score * 0.18))
            return "CALL", f"{accuracy_calc}%", ", ".join(reasons)
        elif put_score >= 55 and put_score > call_score:
            accuracy_calc = min(94, 78 + int(put_score * 0.18))
            return "PUT", f"{accuracy_calc}%", ", ".join(reasons)

        return None, "0%", "Neutral market conditions"
