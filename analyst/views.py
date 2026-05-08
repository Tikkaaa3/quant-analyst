from django.shortcuts import render, get_object_or_404
import plotly.graph_objects as go
from .services.data_service import DataService
from .services.ml_service import MLService
from .services.agent_graph import QuantAgent
from .models import AnalysisReport


def analysis_lab(request):
    return render(request, "analyst/index.html")


def run_analysis(request):
    ticker = request.GET.get("ticker", "AAPL").upper()
    data_service = DataService()
    ml_service = MLService()

    context = {"ticker": ticker}

    try:
        # 1. Fetch Data (Always needed for the chart)
        df = data_service.fetch_stock_data(ticker)

        # 2. Check Database for today's cache
        from django.utils import timezone

        today = timezone.now().date()
        existing_report = AnalysisReport.objects.filter(ticker=ticker).first()
        news = []

        if existing_report and existing_report.created_at.date() == today:
            # CACHE HIT: Skip ML and LLM, use the database record
            xgboost_prob = existing_report.prediction_score / 100.0
            sentiment = existing_report.sentiment
            ai_report = existing_report.ai_report
        else:
            # CACHE MISS: Run the pipeline
            try:
                news = data_service.fetch_news_sentiment(ticker)
            except Exception as e:
                print(f"DEBUG: News service failed: {e}")

            xgboost_prob = ml_service.predict_price_movement(df)
            sentiment = ml_service.analyze_sentiment(news)

            agent = QuantAgent()
            ai_report = agent.run(
                ticker=ticker,
                price=round(df["close"].iloc[-1], 2),
                score=xgboost_prob,
                sentiment=sentiment,
            )

            # Clean the Vault: Delete any old records for this ticker
            AnalysisReport.objects.filter(ticker=ticker).delete()

            # Save the new record
            AnalysisReport.objects.create(
                ticker=ticker,
                current_price=round(df["close"].iloc[-1], 2),
                prediction_score=xgboost_prob * 100,
                sentiment=sentiment,
                ai_report=ai_report,
            )

        # Chart Generation
        df_chart = df.tail(180)
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

        initial_start = df_chart.index[-30].strftime("%Y-%m-%d")
        initial_end = df_chart.index[-1].strftime("%Y-%m-%d")

        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            xaxis=dict(range=[initial_start, initial_end]),
        )
        chart_html = fig.to_html(full_html=False, include_plotlyjs=False)

        # 4. Populate Context
        context.update(
            {
                "chart_html": chart_html,
                "news_count": len(news) if news else 0,
                "news": news[:5] if news else [],
                "prediction_score": xgboost_prob * 100,
                "sentiment": sentiment,
                "ai_report": ai_report,
            }
        )
    except Exception as e:
        context["error"] = str(e)

    return render(request, "analyst/partials/results.html", context)


def vault(request):
    reports = AnalysisReport.objects.all().order_by("-created_at")
    return render(request, "analyst/vault.html", {"reports": reports})


def dashboard(request):
    total_analyses = AnalysisReport.objects.count()
    recent_reports = AnalysisReport.objects.order_by("-created_at")[:3]
    return render(
        request,
        "analyst/dashboard.html",
        {"total_analyses": total_analyses, "recent_reports": recent_reports},
    )


def report_detail(request, pk):
    report = get_object_or_404(AnalysisReport, pk=pk)
    return render(request, "analyst/report_detail.html", {"report": report})
