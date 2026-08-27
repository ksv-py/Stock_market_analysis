# MarketScope

MarketScope is an original stock-market analysis project based on the reference repository's historical price, risk, and Monte Carlo themes. It uses a real Kaggle export and provides both a notebook and a FastAPI service.

## Data

Source: [Stock Market Analysis Data on Kaggle](https://www.kaggle.com/datasets/amirmotefaker/stock-market-analysis-data)

The downloaded `stocks.csv` is stored as `data/stock_history.csv`. It contains `Ticker`, `Date`, OHLC prices, adjusted close, and volume. The notebook/API normalizes `Ticker` to `Symbol`.

## Notebook

`stock_market_analysis.ipynb` covers data quality, daily returns, annualized volatility, drawdown, and a resampled-return Monte Carlo scenario range. The simulation is not a forecast or investment advice.

## FastAPI endpoints

- `GET /health`
- `GET /symbols`
- `GET /summary?symbol=AAPL`

## Run

```powershell
python.exe -m pip install -r requirements.txt
python.exe -m uvicorn api:app --reload --port 8504
```

Open `http://localhost:8504/docs` for the interactive API documentation.

## Interpretation

Historical returns, volatility, drawdown, and resampled paths describe uncertainty but do not predict future prices. A stronger production workflow would include corporate actions, benchmarks, transaction costs, regime changes, and walk-forward evaluation.
