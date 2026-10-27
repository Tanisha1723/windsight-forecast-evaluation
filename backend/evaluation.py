
from datetime import datetime, timezone

import httpx

from elexon import (
    BASE_URL,
    EVOLUTION_TIMEOUT_SECONDS,
    fetch_wind_forecast_evolution,
)


def parse_utc(value: str) -> datetime:
    """Parse an ISO timestamp and normalize it to UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def select_forecast_at_cutoff(
    revisions: list[dict],
    cutoff: datetime,
) -> dict | None:
    """Select the latest valid forecast published at or before cutoff."""
    if cutoff.tzinfo is None:
        raise ValueError("cutoff must include a timezone")

    cutoff_utc = cutoff.astimezone(timezone.utc)

    eligible = [
        revision
        for revision in revisions
        if revision.get("publishTime")
        and revision.get("generation") is not None
        and parse_utc(revision["publishTime"]) <= cutoff_utc
    ]

    if not eligible:
        return None

    return max(
        eligible,
        key=lambda revision: parse_utc(revision["publishTime"]),
    )


def calculate_metrics(pairs: list[dict]) -> dict:
    """Calculate metrics for matched forecast/actual pairs.

    Error = forecast - actual.
    Positive bias indicates overforecasting.
    """
    if not pairs:
        return {
            "interval_count": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "wape": None,
        }

    errors = [
        float(pair["forecast"]) - float(pair["actual"])
        for pair in pairs
    ]

    absolute_errors = [abs(error) for error in errors]
    squared_errors = [error**2 for error in errors]

    total_absolute_actual = sum(
        abs(float(pair["actual"]))
        for pair in pairs
    )

    return {
        "interval_count": len(pairs),
        "mae": sum(absolute_errors) / len(errors),
        "rmse": (sum(squared_errors) / len(errors)) ** 0.5,
        "bias": sum(errors) / len(errors),
        "wape": (
            sum(absolute_errors) / total_absolute_actual * 100
            if total_absolute_actual > 0
            else None
        ),
    }


async def evaluate_interval(
    start_time: str,
    actual: float,
    cutoff: datetime,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Evaluate one delivery interval using only eligible revisions."""
    if client is None:
        async with httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=EVOLUTION_TIMEOUT_SECONDS,
        ) as own_client:
            return await _evaluate_with_client(
                start_time,
                actual,
                cutoff,
                own_client,
            )

    return await _evaluate_with_client(
        start_time,
        actual,
        cutoff,
        client,
    )


async def _evaluate_with_client(
    start_time: str,
    actual: float,
    cutoff: datetime,
    client: httpx.AsyncClient,
) -> dict:
    """Evaluate an interval using a supplied HTTP client."""
    revisions = await fetch_wind_forecast_evolution(
        start_time,
        client=client,
    )

    forecast_record = select_forecast_at_cutoff(
        revisions,
        cutoff,
    )

    if forecast_record is None:
        return {
            "startTime": start_time,
            "actual": float(actual),
            "forecast": None,
            "publishTime": None,
            "error": None,
            "status": "no_eligible_forecast",
        }

    forecast = float(forecast_record["generation"])

    return {
        "startTime": start_time,
        "actual": float(actual),
        "forecast": forecast,
        "publishTime": forecast_record["publishTime"],
        "error": forecast - float(actual),
        "status": "evaluated",
    }
