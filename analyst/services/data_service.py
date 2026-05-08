import os
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()


class DataService:
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"

    def fetch_stock_data(self, ticker: str):
        """Fetches daily price data and returns a cleaned Pandas DataFrame."""
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "apikey": self.api_key,
            "outputsize": "compact",  # Last 100 days
        }

        response = requests.get(self.base_url, params=params)
        data = response.json()

        if "Time Series (Daily)" not in data:
            raise ValueError(
                f"Error fetching data for {ticker}: {data.get('Note', 'Check API Key/Limits')}"
            )

        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
        df.columns = ["open", "high", "low", "close", "volume"]
        df.index = pd.to_datetime(df.index)
        df = df.astype(float).sort_index()

        # Engineering Features (The NumPy/Pandas part)
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["daily_return"] = df["close"].pct_change()
        df["volatility"] = df["daily_return"].rolling(window=20).std()

        return df

    def fetch_news_sentiment(self, ticker: str):
        """Fetches latest news and sentiment for a ticker."""
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": self.api_key,
            "limit": 10,
        }

        response = requests.get(self.base_url, params=params)
        data = response.json()

        # We return the 'feed' which contains headlines and summaries
        return data.get("feed", [])
