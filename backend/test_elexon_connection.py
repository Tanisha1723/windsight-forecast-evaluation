
import asyncio
from datetime import datetime, timedelta, timezone

from elexon import fetch_wind_forecast_evolution
from evaluation import select_forecast_at_cutoff


async def main():
    delivery_times = [
        "2026-01-01T00:00:00Z",
        "2026-01-01T12:00:00Z",
        "2026-01-31T23:00:00Z",
    ]

    from datetime import date

    for start_time in delivery_times:
        delivery_time = datetime.fromisoformat(
            start_time.replace("Z", "+00:00")
        )
        cutoff = delivery_time - timedelta(hours=24)

        revisions = await fetch_wind_forecast_evolution(start_time)

        selected = select_forecast_at_cutoff(revisions, cutoff)

        print(f"\nDelivery time: {start_time}")
        print("Decision cutoff:", cutoff.isoformat())
        print("Revision count:", len(revisions))

        if revisions:
            print(
                "Earliest publication:",
                min(r["publishTime"] for r in revisions),
            )
            print(
                "Latest publication:",
                max(r["publishTime"] for r in revisions),
            )

        if selected:
            print("Selected publication:", selected["publishTime"])
            print("Selected generation:", selected["generation"])
        else:
            print("Selected forecast: None")


if __name__ == "__main__":
    asyncio.run(main())
