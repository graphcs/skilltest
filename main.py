"""
Andiron FX API - FastAPI application for FX rate analysis.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from calculator import FXCalculator
from fx_client import FXClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global FX client instance
fx_client: Optional[FXClient] = None

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global fx_client
    # Startup: Initialize FX client with 5-minute cache
    fx_client = FXClient(cache_ttl=300)
    logger.info("FX Client initialized")
    yield
    # Shutdown: Close HTTP client
    await fx_client.close()
    logger.info("FX Client closed")


# Initialize FastAPI app
app = FastAPI(
    title="Andiron FX API",
    description="EUR->USD FX rate analysis with day-by-day breakdown",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "andiron-fx-api"
    }


@app.get("/summary")
async def get_summary(
    start: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end: str = Query(..., description="End date in YYYY-MM-DD format"),
    breakdown: str = Query("day", description="Breakdown mode: 'day' or 'none'")
):
    """
    Get FX rate summary with optional daily breakdown.

    Args:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        breakdown: 'day' for daily breakdown, 'none' for totals only

    Returns:
        JSON response with rates, changes, and totals
    """
    # Validate dates
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        if start_dt > end_dt:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before or equal to end date"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
        )

    # Validate breakdown parameter
    if breakdown not in ['day', 'none']:
        raise HTTPException(
            status_code=400,
            detail="Breakdown must be 'day' or 'none'"
        )

    try:
        # Fetch FX data from API (with caching and fallback)
        rates_data = await fx_client.get_range(
            start_date=start,
            end_date=end,
            base="EUR",
            symbols="USD"
        )

        # Calculate daily metrics
        calculator = FXCalculator()
        daily_metrics = calculator.calculate_daily_metrics(rates_data)

        if not daily_metrics:
            raise HTTPException(
                status_code=404,
                detail="No rate data available for the specified date range"
            )

        # Calculate totals
        totals = calculator.calculate_totals(daily_metrics)

        # Format response
        response = calculator.format_response(
            daily_metrics=daily_metrics,
            totals=totals,
            breakdown=breakdown,
            start_date=start,
            end_date=end
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing summary request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing FX data"
        )


@app.get("/summary/view", response_class=HTMLResponse)
async def get_summary_view(
    request: Request,
    start: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end: str = Query(..., description="End date in YYYY-MM-DD format"),
    breakdown: str = Query("day", description="Breakdown mode: 'day' or 'none'")
):
    """
    Get FX rate summary as HTML visualization with table and chart.

    Args:
        request: FastAPI request object
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        breakdown: 'day' for daily breakdown, 'none' for totals only

    Returns:
        HTML page with visualization
    """
    try:
        # Get the JSON data
        data = await get_summary(start=start, end=end, breakdown=breakdown)

        # Render HTML template
        return templates.TemplateResponse(
            "summary.html",
            {
                "request": request,
                "data": data,
                "start": start,
                "end": end,
                "breakdown": breakdown
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering summary view: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error rendering visualization"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
