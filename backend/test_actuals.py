
import asyncio
from datetime import date

from elexon import fetch_wind_actuals


async def main():
    records = await fetch_wind_actuals(
        date(2026, 1, 1),
        date(2026, 1, 2),
    )

    print("Actual records returned:", len(records))

    if not records:
        return

    print("\nFirst record:")
    print(records[0])

    print("\nLast record:")
    print(records[-1])

    print(
        "\nRecords with missing generation:",
        sum(r.get("generation") is None for r in records),
    )

    print("\nRecords around midnight UTC:")

    for record in sorted(
        records,
        key=lambda r: r.get("startTime", ""),
    ):
        start_time = record.get("startTime", "")

        if start_time.startswith(
            (
                "2025-12-31T23:",
                "2026-01-01T00:",
                "2026-01-01T01:",
            )
        ):
            print(
                "startTime:", start_time,
                "| settlementPeriod:", record.get("settlementPeriod"),
                "| generation:", record.get("generation"),
            )


if __name__ == "__main__":
    asyncio.run(main())
