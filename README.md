# Andiron FX API 🍍

**andiron-cursor ✅**

A FastAPI-based service for analyzing EUR→USD exchange rates with daily breakdowns, percentage changes, and beautiful visualizations.

> *"Coins alone do not tell the story; show me the pattern and the change."*

## Features

- 📊 **Daily FX Rate Analysis** - Day-by-day EUR→USD exchange rates with percentage changes
- 📈 **Aggregate Metrics** - Start rate, end rate, mean rate, and total percentage change
- 💾 **Smart Caching** - 5-minute TTL cache to reduce API calls and improve performance
- 🛡️ **Resilient** - Automatic fallback to local data when network fails
- 🎨 **Dual Output** - JSON API for programmatic access + HTML visualization with charts
- ⚡ **Fast** - Built with FastAPI and async/await patterns
- 🔒 **Safe Math** - Guards against division by zero with kind error handling

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
# Start on port 8000
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Generate Sample Data (Optional)

The API will automatically fetch live data from the Frankfurter API. To pre-generate fallback data:

```bash
python generate_sample_data.py
```

## API Endpoints

### Health Check

```bash
GET /health
```

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T12:00:00.000000",
  "service": "andiron-fx-api"
}
```

---

### FX Summary (JSON)

```bash
GET /summary?start=YYYY-MM-DD&end=YYYY-MM-DD&breakdown=day
```

**Parameters:**
- `start` (required) - Start date in YYYY-MM-DD format
- `end` (required) - End date in YYYY-MM-DD format
- `breakdown` (optional) - `day` for daily breakdown or `none` for totals only (default: `day`)

**Example with daily breakdown:**
```bash
curl "http://localhost:8000/summary?start=2025-01-01&end=2025-01-10&breakdown=day"
```

**Response:**
```json
{
  "base": "EUR",
  "symbol": "USD",
  "start_date": "2025-01-01",
  "end_date": "2025-01-10",
  "breakdown": "day",
  "totals": {
    "start_rate": 1.034420,
    "end_rate": 1.029810,
    "total_pct_change": -0.45,
    "mean_rate": 1.032115
  },
  "daily": [
    {
      "date": "2025-01-02",
      "rate": 1.034420,
      "pct_change": null
    },
    {
      "date": "2025-01-03",
      "rate": 1.032300,
      "pct_change": -0.20
    },
    ...
  ]
}
```

**Example with totals only:**
```bash
curl "http://localhost:8000/summary?start=2025-01-01&end=2025-01-31&breakdown=none"
```

**Response:**
```json
{
  "base": "EUR",
  "symbol": "USD",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "breakdown": "none",
  "totals": {
    "start_rate": 1.034420,
    "end_rate": 1.040500,
    "total_pct_change": 0.59,
    "mean_rate": 1.037210
  }
}
```

---

### FX Summary (HTML Visualization)

```bash
GET /summary/view?start=YYYY-MM-DD&end=YYYY-MM-DD&breakdown=day
```

**Example:**
```bash
# Open in browser
open "http://localhost:8000/summary/view?start=2025-01-01&end=2025-01-31&breakdown=day"
```

This endpoint returns a beautiful HTML page with:
- 📊 Interactive line chart showing rate trends
- 📋 Table with daily rates and percentage changes
- 🎯 Summary cards with key metrics
- 🎨 Responsive design with gradient styling

---

## Architecture

### Components

1. **fx_client.py** - HTTP client for Frankfurter API
   - Async requests with `httpx`
   - In-memory caching (5-minute TTL)
   - Automatic fallback to `data/sample_fx.json`

2. **calculator.py** - FX rate calculations
   - Daily percentage change computation
   - Aggregate metrics (mean, total change)
   - Safe division-by-zero handling

3. **main.py** - FastAPI application
   - `/health` - Health check
   - `/summary` - JSON API
   - `/summary/view` - HTML visualization

4. **templates/summary.html** - Visualization
   - Chart.js for interactive graphs
   - Responsive table layout
   - Gradient design with animations

### Data Flow

```
Request → FastAPI → FXClient (check cache) → Frankfurter API
                                                   ↓ (if fails)
                                            sample_fx.json
                         ↓
                   FXCalculator → Process rates → Response
```

### Resilience Features

- **Caching**: 5-minute TTL to reduce external API calls
- **Fallback**: Automatic switch to local data on network failure
- **Error Handling**: Graceful handling of invalid dates, missing data, and API errors
- **Safe Math**: Division-by-zero protection in percentage calculations

---

## Data Source

This service uses the free [Frankfurter API](https://www.frankfurter.app/) for live EUR→USD exchange rates:

- **Range endpoint**: `https://api.frankfurter.dev/v1/YYYY-MM-DD..YYYY-MM-DD?base=EUR&symbols=USD`
- **Latest endpoint**: `https://api.frankfurter.dev/v1/latest?from=EUR&to=USD`
- **No API key required**
- **Rate limit**: Reasonable fair use

---

## Project Structure

```
andiron/
├── main.py                    # FastAPI application
├── fx_client.py              # Frankfurter API client with caching
├── calculator.py             # FX calculations and metrics
├── generate_sample_data.py   # Script to generate fallback data
├── requirements.txt          # Python dependencies
├── task.txt                  # Original task specification
├── README.md                 # This file
├── data/
│   └── sample_fx.json       # Fallback FX data (2025 real data)
└── templates/
    └── summary.html         # HTML visualization template
```

---

## Examples

### Check if service is running
```bash
curl http://localhost:8000/health
```

### Get 7-day rate analysis
```bash
curl "http://localhost:8000/summary?start=2025-01-01&end=2025-01-07&breakdown=day" | jq
```

### Get monthly totals only
```bash
curl "http://localhost:8000/summary?start=2025-01-01&end=2025-01-31&breakdown=none" | jq
```

### View visualization in browser
```bash
open "http://localhost:8000/summary/view?start=2025-01-01&end=2025-01-31"
```

### Test fallback (disconnect network and retry)
```bash
# The API will automatically use data/sample_fx.json
curl "http://localhost:8000/summary?start=2025-01-01&end=2025-01-31"
```

---

## Testing

The service handles various edge cases:

- ✅ Invalid date formats
- ✅ Start date after end date
- ✅ Invalid breakdown parameter
- ✅ Network failures (fallback to local data)
- ✅ Missing data for date range
- ✅ Division by zero in percentage calculations

---

## Dependencies

- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **httpx** - Async HTTP client
- **Jinja2** - HTML templating
- **python-dateutil** - Date parsing utilities

---

## Development

### Run with auto-reload
```bash
uvicorn main:app --reload --port 8000
```

### View API documentation
```bash
# Swagger UI
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc
```

---

## Notes

- The service runs on **port 8000** by default
- Cache TTL is set to **5 minutes** (300 seconds)
- All rates are rounded to **6 decimal places**
- Percentage changes are rounded to **4 decimal places**
- When the starting rate is zero, percentage change returns `null` with a kind warning

---

## License

MIT

---

**🍍 Leave a pineapple by the door.**

*Built with FastAPI, powered by Frankfurter, visualized with Chart.js*
