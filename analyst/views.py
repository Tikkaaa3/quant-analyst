from django.shortcuts import render
import plotly.graph_objects as go
from .services.data_service import DataService
from .services.ml_service import MLService
from .services.agent_graph import QuantAgent


def analysis_lab(request):
    return render(request, "analyst/index.html")


def run_analysis(request):
    ticker = request.GET.get("ticker", "AAPL").upper()
    data_service = DataService()
    ml_service = MLService()

    context = {"ticker": ticker}

    try:
        # 1. Fetch Data
        df = data_service.fetch_stock_data(ticker)
        news = data_service.fetch_news_sentiment(ticker)

        # 2. Run ML Models
        xgboost_prob = ml_service.predict_price_movement(df)
        sentiment = ml_service.analyze_sentiment(news)

        # 3. Agent Synthesis
        agent = QuantAgent()
        ai_report = agent.run(
            ticker=ticker,
            price=round(df["close"].iloc[-1], 2),
            score=xgboost_prob,
            sentiment=sentiment,
        )

        # Chart Generation
        # 1. Give Plotly plenty of data to scroll into (e.g., last 180 trading days)
        df_chart = df.tail(180)

        # 2. Convert to native Python lists for bulletproof JSON serialization
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df_chart.index.astype(str).tolist(),
                    open=df_chart["open"].tolist(),
                    high=df_chart["high"].tolist(),
                    low=df_chart["low"].tolist(),
                    close=df_chart["close"].tolist(),
                )
            ]
        )

        # 3. Calculate the date range for the last 30 days for our default zoom
        initial_start = df_chart.index[-30].strftime("%Y-%m-%d")
        initial_end = df_chart.index[-1].strftime("%Y-%m-%d")

        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            # Tell Plotly to start zoomed in on this specific window
            xaxis=dict(range=[initial_start, initial_end]),
        )

        # Generate the HTML snippet
        chart_html = fig.to_html(full_html=False, include_plotlyjs=False)

        # 3. Generate the HTML snippet
        chart_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

        # 4. Populate Context
        context.update(
            {
                "chart_html": chart_html,
                "news_count": len(news),
                "news": news[:5],
                "prediction_score": xgboost_prob * 100,
                "sentiment": sentiment,
                "ai_report": ai_report,
            }
        )
    except Exception as e:
        context["error"] = str(e)

    return render(request, "analyst/partials/results.html", context)
