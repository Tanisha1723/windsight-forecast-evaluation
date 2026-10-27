
import asyncio
from datetime import date, datetime, timezone

from elexon import fetch_wind_actuals
from evaluation import evaluate_interval


async def main():
    # One test delivery interval: 1 January 2026, 12:00 UTC.
    start_time = "2026-01-01T12:00:00Z"

    # Explicit test assumption: decision cutoff is 24 hours
    # before the delivery interval.
    cutoff = datetime(2025, 12, 31, 12, 0, tzinfo=timezone.utc)

    actual_records = await fetch_wind_actuals(
        date(2026, 1, 1),
        date(2026, 1, 1),
    )

    matching_actuals = [
        record
        for record in actual_records
        if record.get("startTime") == start_time
        and record.get("generation") is not None
    ]

    if not matching_actuals:
        raise RuntimeError(f"No actual generation found for {start_time}")

    actual = float(matching_actuals[0]["generation"])

    result = await evaluate_interval(
        start_time=start_time,
        actual=actual,
        cutoff=cutoff,
    )

    print("Delivery interval:", result["startTime"])
    print("Actual generation:", result["actual"])
    print("Decision cutoff:", cutoff.isoformat())
    print("Selected forecast:", result["forecast"])
    print("Forecast publication time:", result["publishTime"])
    print("Forecast error:", result["error"])
    print("Status:", result["status"])

    if result["status"] == "evaluated":
        assert result["publishTime"] <= cutoff.isoformat().replace(
            "+00:00", "Z"
        )
        print("\nIntegration test passed.")
    else:
        print("\nNo eligible forecast was available at this cutoff.")


if __name__ == "__main__":
    asyncio.run(main())
