
import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from elexon import BASE_URL, TIMEOUT_SECONDS, fetch_wind_actuals
from evaluation import calculate_metrics, evaluate_interval


app = FastAPI(
    title="WindSight API",
    description="Wind generation forecast evaluation for UK energy decisions.",
    version="0.1.0",
)


import os

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)



@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "WindSight API",
        "version": "0.1.0",
    }


@app.get("/api/evaluate")
async def evaluate_wind_forecasts(
    start_date: date = Query(default=date(2026, 1, 1)),
    end_date: date = Query(default=date(2026, 1, 31)),
    cutoff_hours: int = Query(default=24, ge=1, le=168),
):
    """Evaluate hourly wind forecasts against hourly average actuals.

    Each hourly actual is the mean of its two half-hourly FUELHH
    observations. The forecast must have been published at or before
    the configured decision cutoff for that delivery hour.
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be on or after start_date",
        )

    if (end_date - start_date).days > 31:
        raise HTTPException(
            status_code=400,
            detail="Date range cannot exceed 32 calendar days",
        )

    try:
        actual_records = await fetch_wind_actuals(
            start_date,
            end_date,
        )

        # Group half-hourly actuals by their UTC delivery hour.
        half_hourly_by_hour = defaultdict(dict)

        for record in actual_records:
            start_time = record.get("startTime")
            generation = record.get("generation")

            if start_time is None or generation is None:
                continue

            delivery_time = datetime.fromisoformat(
                start_time.replace("Z", "+00:00")
            )

            if delivery_time.tzinfo is None:
                delivery_time = delivery_time.replace(
                    tzinfo=timezone.utc
                )

            delivery_time = delivery_time.astimezone(timezone.utc)

            # Keep only observations within the requested UTC dates.
            if not (
                start_date <= delivery_time.date() <= end_date
            ):
                continue

            hour_start = delivery_time.replace(
                minute=0,
                second=0,
                microsecond=0,
            )

            # Key by minute to avoid accidentally counting duplicate rows.
            half_hourly_by_hour[hour_start][delivery_time.minute] = (
                float(generation)
            )

        # Evaluate only complete hours with both :00 and :30 actuals.
        actual_by_hour = {}

        for hour_start, observations in half_hourly_by_hour.items():
            if 0 not in observations or 30 not in observations:
                continue

            actual_by_hour[hour_start] = (
                observations[0] + observations[30]
            ) / 2

        if not actual_by_hour:
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "cutoff_hours": cutoff_hours,
                "interval_count": 0,
                "evaluated_count": 0,
                "unavailable_count": 0,
                "metrics": calculate_metrics([]),
                "results": [],
            }

        semaphore = asyncio.Semaphore(8)

        async with httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=TIMEOUT_SECONDS,
        ) as client:

            async def evaluate_one(
                delivery_time: datetime,
                actual: float,
            ) -> dict:
                start_time = (
                    delivery_time.isoformat()
                    .replace("+00:00", "Z")
                )

                cutoff = delivery_time - timedelta(
                    hours=cutoff_hours
                )

                async with semaphore:
                    return await evaluate_interval(
                        start_time=start_time,
                        actual=actual,
                        cutoff=cutoff,
                        client=client,
                    )

            tasks = [
                evaluate_one(delivery_time, actual)
                for delivery_time, actual in actual_by_hour.items()
            ]

            results = await asyncio.gather(*tasks)

        results.sort(key=lambda row: row["startTime"])

        evaluated_results = [
            result
            for result in results
            if result["status"] == "evaluated"
        ]

        pairs = [
            {
                "forecast": result["forecast"],
                "actual": result["actual"],
            }
            for result in evaluated_results
        ]

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cutoff_hours": cutoff_hours,
            "interval_count": len(results),
            "evaluated_count": len(evaluated_results),
            "unavailable_count": (
                len(results) - len(evaluated_results)
            ),
            "metrics": calculate_metrics(pairs),
            "results": results,
        }

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Elexon API returned an unsuccessful response "
                f"(HTTP {exc.response.status_code})."
            ),
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to evaluate Elexon data: {exc}",
        ) from exc
