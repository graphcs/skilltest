"""
FX rate calculations and metrics computation.
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FXCalculator:
    """Calculate FX metrics from rate data."""

    @staticmethod
    def calculate_daily_metrics(rates_data: dict) -> List[Dict]:
        """
        Calculate daily metrics including percentage changes.

        Args:
            rates_data: Dict with 'rates' key containing date->rate mapping

        Returns:
            List of dicts with date, rate, and pct_change for each day
        """
        if not rates_data or 'rates' not in rates_data:
            return []

        rates = rates_data['rates']
        sorted_dates = sorted(rates.keys())

        daily_metrics = []
        previous_rate = None

        for date in sorted_dates:
            # Extract USD rate from the date's rates
            date_rates = rates[date]
            if isinstance(date_rates, dict):
                current_rate = date_rates.get('USD')
            else:
                # Handle case where rate might be a direct value
                current_rate = date_rates

            if current_rate is None:
                logger.warning(f"No USD rate found for {date}")
                continue

            # Calculate percentage change from previous day
            pct_change = None
            if previous_rate is not None:
                pct_change = FXCalculator._safe_pct_change(previous_rate, current_rate)

            daily_metrics.append({
                'date': date,
                'rate': round(current_rate, 6),
                'pct_change': round(pct_change, 4) if pct_change is not None else None
            })

            previous_rate = current_rate

        return daily_metrics

    @staticmethod
    def calculate_totals(daily_metrics: List[Dict]) -> Dict:
        """
        Calculate aggregate totals from daily metrics.

        Args:
            daily_metrics: List of daily metric dicts

        Returns:
            Dict with start_rate, end_rate, total_pct_change, mean_rate
        """
        if not daily_metrics:
            return {
                'start_rate': None,
                'end_rate': None,
                'total_pct_change': None,
                'mean_rate': None
            }

        start_rate = daily_metrics[0]['rate']
        end_rate = daily_metrics[-1]['rate']

        # Calculate total percentage change
        total_pct_change = FXCalculator._safe_pct_change(start_rate, end_rate)

        # Calculate mean rate
        rates = [day['rate'] for day in daily_metrics]
        mean_rate = sum(rates) / len(rates)

        return {
            'start_rate': round(start_rate, 6),
            'end_rate': round(end_rate, 6),
            'total_pct_change': round(total_pct_change, 4) if total_pct_change is not None else None,
            'mean_rate': round(mean_rate, 6)
        }

    @staticmethod
    def _safe_pct_change(old_value: float, new_value: float) -> Optional[float]:
        """
        Safely calculate percentage change, guarding against division by zero.

        Args:
            old_value: Previous value
            new_value: Current value

        Returns:
            Percentage change or None if old_value is zero
        """
        if old_value == 0:
            logger.warning(
                "Encountered zero denominator in percentage change calculation. "
                "Returning None to be kind."
            )
            return None

        return ((new_value - old_value) / old_value) * 100

    @staticmethod
    def format_response(
        daily_metrics: List[Dict],
        totals: Dict,
        breakdown: str = 'day',
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        Format the final response based on breakdown mode.

        Args:
            daily_metrics: List of daily metrics
            totals: Aggregate totals
            breakdown: 'day' for daily breakdown, 'none' for totals only
            start_date: Start date string
            end_date: End date string

        Returns:
            Formatted response dict
        """
        response = {
            'base': 'EUR',
            'symbol': 'USD',
            'start_date': start_date,
            'end_date': end_date,
            'breakdown': breakdown,
            'totals': totals
        }

        if breakdown == 'day':
            response['daily'] = daily_metrics
        else:
            # For 'none', we only include totals
            pass

        return response
