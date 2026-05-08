# QuantAnalyst AI

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-6.0-092E20.svg)
![HTMX](https://img.shields.io/badge/HTMX-1.9-336699.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-FinBERT-EE4C2C.svg)

> An end-to-end quantitative stock analysis platform that combines real-time market data ingestion, domain-specific NLP sentiment analysis, rule-based technical scoring, and LLM-generated investment reports — delivered through a zero-JavaScript hypermedia interface.

## 🎬 Demo Video

👉 Click the image below to watch the demo on YouTube:

[![▶ Watch Demo](https://img.youtube.com/vi/t8O67ijbxIs/maxresdefault.jpg)](https://www.youtube.com/watch?v=t8O67ijbxIs)

---

## What It Does

A user enters a ticker symbol (e.g. `AAPL`, `TSLA`). The system fetches live OHLCV market data from Alpha Vantage, engineers technical features (SMA-20, daily returns, volatility, RSI), runs FinBERT sentiment analysis across up to 10 recent financial news articles, computes a bullish probability score using technical indicator rules, and sends all structured context into a LangGraph agent that prompts a 70B LLM to produce a markdown investment report. The full pipeline result — including a Plotly candlestick chart, probability gauge, sentiment breakdown, and AI narrative — is injected into the page without a full reload via HTMX.

Previous reports are persisted in a SQLite-backed vault with same-day caching: re-analyzing a ticker within the same day skips the entire ML and LLM pipeline and serves the cached result instantly.

---

## Architecture

```
Browser
  │
  │  hx-get /analyst/run_analysis/  (HTMX, no custom JS)
  ▼
Django View (run_analysis)
  │
  ├── DataService.fetch_stock_data()
  │     └── Alpha Vantage TIME_SERIES_DAILY → pandas DataFrame
  │           └── Feature engineering: SMA-20, daily_return, volatility, RSI-14
  │
  ├── [Cache check: AnalysisReport DB → skip pipeline if same-day record exists]
  │
  ├── DataService.fetch_news_sentiment()
  │     └── Alpha Vantage NEWS_SENTIMENT API → list of articles
  │
  ├── MLService.predict_price_movement()
  │     └── Rule-based scoring: SMA crossover + RSI band logic → float [0.0–1.0]
  │
  ├── MLService.analyze_sentiment()
  │     └── ProsusAI/finbert (PyTorch) → {"positive": N, "negative": N, "neutral": N}
  │
  ├── QuantAgent.run()  [LangGraph StateGraph]
  │     └── START → draft_report → END
  │           └── ChatOpenAI (OpenRouter / Llama-3.3-70B) → markdown report
  │
  ├── AnalysisReport.objects.create()  → SQLite
  │
  └── Plotly candlestick HTML + partials/results.html → injected by HTMX
```

### Two-Layer Cache Strategy

| Layer | Storage                       | Scope       | Purpose                                                    |
| ----- | ----------------------------- | ----------- | ---------------------------------------------------------- |
| L1    | `data/cache/*.csv` / `*.json` | File system | Prevents redundant Alpha Vantage API calls across restarts |
| L2    | `AnalysisReport` Django model | SQLite      | Skips the entire ML + LLM pipeline for same-day re-queries |

---

## Tech Stack

### Backend

- **Python 3** / **Django 6.0.5** — web framework and ORM
- **LangGraph 1.1.10** — LLM agent orchestration via compiled `StateGraph`
- **langchain-openai / openai** — LLM client interface
- **Transformers 5.8.0 + PyTorch 2.11.0** — `ProsusAI/finbert` inference for financial NLP
- **XGBoost 3.2.0** — installed, stubbed; intended for a trained price-movement classifier
- **pandas 3.0.2 + NumPy 2.4.4** — feature engineering and DataFrame operations
- **Plotly 6.7.0** — server-side candlestick chart generation (`full_html=False`)
- **requests 2.33.1** — Alpha Vantage API HTTP client
- **python-dotenv 1.2.2** — environment variable management

### Frontend

- **HTMX 1.9.10** — declarative AJAX form submission, partial HTML swaps, loading indicators
- **Tailwind CSS** (CDN) — utility-first dark theme UI
- **Plotly.js** (CDN) — chart runtime loaded once globally, reused by injected partials

### Database

- **SQLite** — development default; stores `AnalysisReport` records

### External Services

- **Alpha Vantage API** — `TIME_SERIES_DAILY` (price) + `NEWS_SENTIMENT` (articles)
- **OpenRouter** — LLM gateway, default model `meta-llama/llama-3.3-70b-instruct`; fully swappable via env vars

---

## Project Structure

```
quant-analyst/
├── core/                     # Django project config (settings, root URLs, WSGI/ASGI)
│
├── analyst/                  # Single Django app — all business logic
│   ├── models.py             # AnalysisReport model (ticker, price, score, sentiment, AI report)
│   ├── views.py              # 4 views: dashboard, analysis_lab, run_analysis, vault, report_detail
│   ├── urls.py               # 5 URL patterns
│   ├── services/             # Decoupled service layer
│   │   ├── data_service.py   # Alpha Vantage ingestion + feature engineering + file cache
│   │   ├── ml_service.py     # FinBERT sentiment + RSI/SMA scoring (XGBoost stub)
│   │   └── agent_graph.py    # LangGraph StateGraph + OpenRouter LLM integration
│   └── templates/
│       ├── base.html         # Sidebar layout, CDN imports, HTMX CSRF hook
│       └── analyst/
│           ├── dashboard.html       # Recent reports overview
│           ├── index.html           # (root redirect)
│           ├── vault.html           # Full report archive
│           ├── report_detail.html   # Single report full view
│           └── partials/
│               └── results.html     # HTMX swap target: chart + score + sentiment + report
│
├── models/      # Placeholder for serialized XGBoost model artifacts
├── notebooks/   # Placeholder for training / EDA notebooks
├── scripts/     # Placeholder for data pipeline / training scripts
└── data/cache/  # File-based API response cache (gitignored)
```

---

## Key Engineering Decisions

### HTMX Over a JavaScript Framework

The entire interactivity story — form submission, loading state, result injection — is handled by HTMX attributes with zero custom JavaScript. `hx-get`, `hx-target`, and `hx-indicator` on the analysis form are sufficient. This is a deliberate hypermedia architecture: the server owns all rendering state, and partial HTML fragments are the API contract.

### LangGraph Scaffold for a Single-Node Agent

The current `StateGraph` has one node (`draft_report`). Using LangGraph here is forward-looking architecture: the `AgentState` TypedDict and compiled graph give a proper scaffold for adding nodes (e.g., a `risk_assessment` node, tool-calling loops, conditional routing) without a full rewrite. The agent is intentionally built to grow, not just to work.

### OpenRouter as an LLM Gateway

Rather than coupling to OpenAI, the LLM client uses OpenRouter's OpenAI-compatible API with `meta-llama/llama-3.3-70b-instruct` as the default. All three values (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`) are env-var overridable, making the entire LLM backend swappable — GPT-4o, Claude 3.5, Mistral — with a single env change.

### FinBERT for Domain-Specific Sentiment

Rather than a generic sentiment model, `ProsusAI/finbert` is used — a BERT model fine-tuned on financial communication. It is loaded once at `MLService.__init__()` and held in memory across requests, avoiding repeated model load overhead.

### XGBoost as an Intentional Placeholder

XGBoost is installed and imported infrastructure is in place, but `predict_price_movement()` currently uses a deterministic RSI + SMA rule system. The `models/`, `notebooks/`, and `scripts/` directories exist explicitly to house the training pipeline. This is a staged implementation — the placeholder is transparent about what the system will become.

### Plotly Rendered Server-Side as a Fragment

`fig.to_html(full_html=False, include_plotlyjs=False)` produces a bare `<div>` with embedded chart data. Plotly.js is loaded once via CDN in `base.html`, and the injected partial reuses it. This avoids re-loading the Plotly runtime on every HTMX swap.

---

## Data Model

```python
class AnalysisReport(models.Model):
    ticker           = CharField(max_length=10)      # e.g. "AAPL"
    current_price    = DecimalField(10 digits, 2dp)  # Last closing price
    prediction_score = FloatField()                  # 0–100 bullish probability
    sentiment        = JSONField()                   # {"positive": N, "negative": N, "neutral": N}
    ai_report        = TextField()                   # Full markdown from LLM
    created_at       = DateTimeField(auto_now_add=True)
```

On cache miss, the pipeline runs `DELETE + INSERT` (not `UPDATE`) — one record per ticker is maintained as a rolling snapshot.

---

## Setup

### Prerequisites

- Python 3.11+
- Alpha Vantage API key (free tier)
- OpenRouter API key (or any OpenAI-compatible provider)

### Install

```bash
git clone https://github.com/Tikkaaa3/quant-analyst.git
cd quant-analyst
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```env
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# LLM provider (OpenRouter by default)
OPENAI_API_KEY=your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.3-70b-instruct
```

To use OpenAI directly:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

### Run

```bash
python manage.py migrate
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000/analyst/lab/` and enter a ticker symbol.

---

## Pages

| Route                  | Description                                          |
| ---------------------- | ---------------------------------------------------- |
| `/analyst/`            | Dashboard — summary cards + 3 most recent reports    |
| `/analyst/lab/`        | Analysis Lab — ticker input, runs the full pipeline  |
| `/analyst/vault/`      | Vault — full archive of all saved reports            |
| `/analyst/vault/<pk>/` | Report detail — full AI report for a single analysis |

---

## Current Limitations

- **XGBoost model not trained**: `predict_price_movement()` uses manual RSI/SMA rules, not a learned model. The XGBoost infrastructure (package, placeholder model dir, stubs) is in place but the training pipeline hasn't been built yet.
- **Markdown rendered as plain text**: The LLM produces markdown but templates use `whitespace-pre-wrap` instead of a markdown parser. Asterisks and `##` headers appear as literal characters.
- **No async pipeline**: The full analysis (API calls + FinBERT inference + LLM generation) runs synchronously in the Django request/response cycle. On slow connections or cold FinBERT loads, this can take 10–20 seconds.
- **File cache has no TTL**: Cached API responses in `data/cache/` persist indefinitely until manually deleted.
- **SQLite only**: No production database configuration is included.

---

## Planned Improvements

1. **Train and integrate a real XGBoost classifier** — use `notebooks/` to build a feature matrix from historical Alpha Vantage data, train on labeled price movement outcomes, serialize to `models/xgb_model.pkl`, and load it in `MLService`.

2. **Async task queue** — offload the pipeline to Celery + Redis. Return a job ID immediately, poll for completion via HTMX `hx-trigger="every 2s"` or a WebSocket, eliminating the long synchronous request.

3. **Markdown rendering** — add `markdown-it` or `django-markdownify` to render the LLM's markdown output as proper HTML in `report_detail.html` and the results partial.

4. **File cache TTL** — replace the static file cache with a time-based check (e.g., invalidate after 24 hours) or move to Django's cache framework with a configurable backend.

5. **Expand the LangGraph agent** — add a second node for risk assessment (e.g., comparing volatility against sector benchmarks), introduce tool-calling so the agent can fetch additional data mid-execution, and add conditional routing based on prediction score thresholds.

6. **CI/CD + testing** — add pytest-django unit tests for `DataService` and `MLService` (mock Alpha Vantage responses), and a GitHub Actions workflow running linting, tests, and a Docker build check on each push.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
