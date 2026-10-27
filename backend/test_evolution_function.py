
import asyncio

from elexon import fetch_wind_forecast_evolution


async def main():
    start_time = "2026-01-01T12:00:00Z"

    records = await fetch_wind_forecast_evolution(start_time)

    print("Requested delivery interval:", start_time)
    print("Evolution records:", len(records))

    if records:
        print("Returned delivery intervals:", {
            record["startTime"] for record in records
        })
        print("\nFirst 3 revisions:")

        for record in records[:3]:
            print(record)
    else:
        print("No forecast revisions returned.")


if __name__ == "__main__":
    asyncio.run(main())
