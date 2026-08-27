from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="MarketScope API", version="1.0.0", description="Historical stock risk and scenario analytics")
DATA_PATH = Path(__file__).parent / "data" / "stock_history.csv"


@app.get("/", response_class=HTMLResponse)
def home() -> str:
        return """
        <!doctype html>
        <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>MarketScope</title>
                <style>
                    :root { color-scheme: light; font-family: Georgia, serif; background: #f4f1ea; color: #20333a; }
                    body { margin: 0; min-height: 100vh; display: grid; place-items: center; }
                    main { width: min(680px, calc(100% - 40px)); padding: 48px 0; }
                    .eyebrow { color: #bf4f3f; font: 700 12px Arial, sans-serif; letter-spacing: .16em; text-transform: uppercase; }
                    h1 { font-size: clamp(42px, 9vw, 76px); line-height: .95; margin: 16px 0; font-weight: 500; }
                    p { font: 18px/1.6 Arial, sans-serif; color: #5c6a6d; max-width: 560px; }
                    nav { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 28px; }
                    a { background: #20333a; color: #fff; padding: 13px 18px; text-decoration: none; border-radius: 4px; font: 700 14px Arial, sans-serif; }
                    a.secondary { background: transparent; border: 1px solid #20333a; color: #20333a; }
                    .toolbar { display: flex; align-items: center; gap: 12px; margin: 28px 0 16px; font: 700 14px Arial, sans-serif; }
                    select { border: 1px solid #bfc7c6; background: #fff; padding: 11px 14px; border-radius: 4px; font: 15px Arial, sans-serif; }
                    .cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
                    article, .chart { background: #fff; border: 1px solid #e0ddd5; border-radius: 5px; padding: 18px; }
                    article small, .chart-head span { display: block; color: #788487; font: 12px Arial, sans-serif; }
                    article strong { display: block; margin-top: 8px; font: 700 25px Arial, sans-serif; }
                    .chart { margin-top: 12px; }
                    .chart-head { display: flex; justify-content: space-between; align-items: baseline; }
                    h2 { margin: 0; font: 700 18px Arial, sans-serif; }
                    canvas { display: block; width: 100%; height: 220px; margin-top: 12px; }
                    @media (max-width: 620px) { .cards { grid-template-columns: 1fr; } .toolbar { align-items: stretch; flex-direction: column; } }
                    .rule { border-top: 1px solid #d7d1c6; margin-top: 48px; padding-top: 18px; font: 13px Arial, sans-serif; color: #788487; }
                </style>
            </head>
            <body>
                <main>
                    <div class="eyebrow">MarketScope / historical risk desk</div>
                    <h1>Read the market's shape.</h1>
                    <p>A small FastAPI dashboard for exploring closing prices, annualized volatility, and drawdowns from the included Kaggle history.</p>
                    <section class="toolbar"><label for="symbol">Symbol</label><select id="symbol"></select><a href="/docs">API docs</a></section>
                    <section class="cards"><article><small>Latest close</small><strong id="close">-</strong></article><article><small>Annualized volatility</small><strong id="volatility">-</strong></article><article><small>Worst drawdown</small><strong id="drawdown">-</strong></article></section>
                    <section class="chart"><div class="chart-head"><h2>Closing price</h2><span id="range"></span></div><canvas id="price-chart"></canvas></section>
                    <section class="chart"><div class="chart-head"><h2>Drawdown</h2><span>from running high</span></div><canvas id="drawdown-chart"></canvas></section>
                    <div class="rule">Research and education only. Historical data and scenarios are not investment advice.</div>
                    <script>
                        const select = document.getElementById('symbol');
                        const money = value => '$' + Number(value).toFixed(2);
                        async function loadSymbols() { const response = await fetch('/symbols'); const data = await response.json(); data.symbols.forEach(symbol => select.add(new Option(symbol, symbol))); select.value = data.symbols[0]; loadDashboard(); }
                        async function loadDashboard() { const symbol = select.value; const [summary, series] = await Promise.all([fetch('/summary?symbol=' + symbol).then(r => r.json()), fetch('/series?symbol=' + symbol).then(r => r.json())]); document.getElementById('close').textContent = money(summary.latest_close); document.getElementById('volatility').textContent = (summary.annualized_volatility * 100).toFixed(1) + '%'; document.getElementById('drawdown').textContent = (summary.worst_drawdown * 100).toFixed(1) + '%'; document.getElementById('range').textContent = summary.start + ' to ' + summary.end; draw('price-chart', series.close, '#315f78'); draw('drawdown-chart', series.drawdown, '#bf4f3f'); }
                        function draw(id, values, color) { const canvas = document.getElementById(id), context = canvas.getContext('2d'), width = canvas.clientWidth, height = 220, ratio = window.devicePixelRatio || 1; canvas.width = width * ratio; canvas.height = height * ratio; context.scale(ratio, ratio); const min = Math.min(...values), max = Math.max(...values), span = max - min || 1; context.strokeStyle = color; context.lineWidth = 2.5; context.beginPath(); values.forEach((value, index) => { const x = index * width / (values.length - 1), y = height - 16 - (value - min) / span * (height - 32); index ? context.lineTo(x, y) : context.moveTo(x, y); }); context.stroke(); }
                        select.addEventListener('change', loadDashboard); window.addEventListener('resize', loadDashboard); loadSymbols();
                    </script>
                </main>
            </body>
        </html>
        """


def load_prices() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise HTTPException(503, "Place the original stock history CSV in data/stock_history.csv")
    data = pd.read_csv(DATA_PATH, parse_dates=["Date"])
    data = data.rename(columns={"Ticker": "Symbol"}).sort_values(["Symbol", "Date"])
    data["daily_return"] = data.groupby("Symbol")["Close"].pct_change()
    data["drawdown"] = data["Close"] / data.groupby("Symbol")["Close"].cummax() - 1
    return data


@app.get("/series")
def series(symbol: str = Query(..., min_length=1)) -> dict:
    data = load_prices()
    selected = data[data["Symbol"].eq(symbol.upper())]
    if selected.empty:
        raise HTTPException(404, "Symbol not found in the local source dataset")
    return {"symbol": symbol.upper(), "date": selected["Date"].dt.strftime("%Y-%m-%d").tolist(), "close": selected["Close"].round(4).tolist(), "drawdown": selected["drawdown"].round(4).tolist()}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "dataset_available": DATA_PATH.exists()}


@app.get("/symbols")
def symbols() -> dict:
    data = load_prices()
    return {"symbols": sorted(data["Symbol"].unique().tolist())}


@app.get("/summary")
def summary(symbol: str = Query(..., min_length=1)) -> dict:
    data = load_prices()
    selected = data[data["Symbol"].eq(symbol.upper())]
    if selected.empty:
        raise HTTPException(404, "Symbol not found in the local source dataset")
    returns = selected["daily_return"].dropna()
    return {
        "symbol": symbol.upper(), "observations": len(selected),
        "start": selected["Date"].min().date().isoformat(), "end": selected["Date"].max().date().isoformat(),
        "latest_close": round(float(selected["Close"].iloc[-1]), 2),
        "annualized_volatility": round(float(returns.std() * (252 ** 0.5)), 4),
        "worst_drawdown": round(float(selected["drawdown"].min()), 4),
    }
