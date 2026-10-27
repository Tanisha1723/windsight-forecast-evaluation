
from datetime import date, timedelta

import httpx


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
TIMEOUT_SECONDS = 30.0
EVOLUTION_TIMEOUT_SECONDS = 60.0


async def fetch_wind_actuals(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch half-hourly wind generation outturn for a date range.

    Uses the FUELHH dataset and filters for wind generation.
    Both dates are inclusive.
    """
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    async with httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=TIMEOUT_SECONDS,
    ) as client:
        response = await client.get(
            "/datasets/FUELHH/stream",
            params={
                "settlementDateFrom": start_date.isoformat(),
                "settlementDateTo": end_date.isoformat(),
                "fuelType": "WIND",
            },
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, list):
        raise ValueError("Unexpected FUELHH response format")

    return payload


async def fetch_wind_forecasts(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch wind forecast records for a date range.

    Uses the WINDFOR latest-stream endpoint.
    Both dates are included by requesting midnight after end_date
    as the upper time boundary.
    """
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    start = f"{start_date.isoformat()}T00:00:00Z"
    end = f"{(end_date + timedelta(days=1)).isoformat()}T00:00:00Z"

    async with httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=TIMEOUT_SECONDS,
    ) as client:
        response = await client.get(
            "/forecast/generation/wind/latest/stream",
            params={
                "from": start,
                "to": end,
            },
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, list):
        raise ValueError("Unexpected WINDFOR response format")

    return payload


async def fetch_wind_forecast_evolution(
    start_time: str,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """Fetch historical forecast revisions for one delivery interval.

    Args:
        start_time: Delivery interval timestamp in ISO 8601 format,
            for example "2026-01-01T12:00:00Z".
        client: Optional shared HTTP client. Pass one when fetching
            revisions for multiple intervals to reuse the connection.

    Returns:
        Forecast revisions matching the requested delivery interval.

    Note:
        The evolution endpoint expects the query parameter "startTime",
        not "from" and "to". Its response is filtered by exact startTime
        because the API may return records for a neighboring interval.
    """

    async def fetch_with_client(
        http_client: httpx.AsyncClient,
    ) -> list[dict]:
        response = await http_client.get(
            "/forecast/generation/wind/evolution",
            params={"startTime": start_time},
        )
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, dict):
            records = payload.get("data", [])
        elif isinstance(payload, list):
            records = payload
        else:
            raise ValueError(
                "Unexpected forecast evolution response format"
            )

        if not isinstance(records, list):
            raise ValueError(
                "Unexpected forecast evolution records format"
            )

        return [
            record
            for record in records
            if isinstance(record, dict)
            and record.get("startTime") == start_time
        ]

    if client is not None:
        return await fetch_with_client(client)

    async with httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=EVOLUTION_TIMEOUT_SECONDS,
    ) as own_client:
        return await fetch_with_client(own_client)
