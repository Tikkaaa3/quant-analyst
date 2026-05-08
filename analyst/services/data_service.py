import os
import json
import requests
import pandas as pd
import numpy as np
import time
from dotenv import load_dotenv

load_dotenv()


class DataService:
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.cache_dir = os.path.join("data", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_stock_data(self, ticker: str):
        """Fetches daily price data and returns a cleaned Pandas DataFrame."""
        cache_path = os.path.join(self.cache_dir, f"{ticker}_price.csv")
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path, index_col=0, parse_dates=True)

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "apikey": self.api_key,
            "outputsize": "compact",  # Last 100 days
        }

        print("DEBUG: Sleeping for 2 seconds to respect API limits...")
        time.sleep(2)
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

        df.to_csv(cache_path)
        return df

    def fetch_news_sentiment(self, ticker: str):
        """Fetches latest news and sentiment for a ticker."""
        cache_path = os.path.join(self.cache_dir, f"{ticker}_news.json")
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                cached = json.load(f)
            return cached.get("feed", [])

        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": self.api_key,
            "limit": 50,
        }

        print("DEBUG: Sleeping for 2 seconds to respect API limits...")
        time.sleep(2)
        response = requests.get(self.base_url, params=params)
        data = response.json()

        if "feed" not in data:
            print(f"DEBUG Raw API Response: {data}")

        with open(cache_path, "w") as f:
            json.dump(data, f)

        return data.get("feed", [])
