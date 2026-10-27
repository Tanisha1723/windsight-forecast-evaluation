
import asyncio
from datetime import date, datetime, timedelta, timezone

from main import evaluate_wind_forecasts


async def main():
    response = await evaluate_wind_forecasts(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        cutoff_hours=24,
    )

    results = response["results"]
    issues = []

    for row in results:
        delivery = datetime.fromisoformat(
            row["startTime"].replace("Z", "+00:00")
        )

        if delivery.minute != 0 or delivery.second != 0:
            issues.append(
                f"Not an hourly delivery timestamp: {row['startTime']}"
            )

        if row["status"] == "evaluated":
            published = datetime.fromisoformat(
                row["publishTime"].replace("Z", "+00:00")
            )
            cutoff = delivery - timedelta(hours=24)

            if published > cutoff:
                issues.append(
                    f"Forecast after cutoff: {row['startTime']}"
                )

            expected_error = row["forecast"] - row["actual"]
            if abs(row["error"] - expected_error) > 1e-9:
                issues.append(
                    f"Incorrect error calculation: {row['startTime']}"
                )

    print("Intervals:", response["interval_count"])
    print("Evaluated:", response["evaluated_count"])
    print("Unavailable:", response["unavailable_count"])
    print("Validation issues:", len(issues))

    for issue in issues[:20]:
        print("-", issue)

    if not issues:
        print("All implemented consistency checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
