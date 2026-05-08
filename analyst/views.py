from django.shortcuts import render
from .services.data_service import DataService


def analysis_lab(request):
    ticker = request.GET.get("ticker", "AAPL").upper()
    service = DataService()

    try:
        # Fetch the data
        df = service.fetch_stock_data(ticker)
        news = service.fetch_news_sentiment(ticker)

        # Get the latest stats for the UI
        latest_price = df["close"].iloc[-1]
        latest_sma = df["sma_20"].iloc[-1]

        context = {
            "ticker": ticker,
            "latest_price": round(latest_price, 2),
            "latest_sma": round(latest_sma, 2),
            "news_count": len(news),
            "news": news[:5],  # Only show first 5 for test
        }
    except Exception as e:
        context = {"error": str(e)}

    return render(request, "analyst/index.html", context)
