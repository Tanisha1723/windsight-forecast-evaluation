from evaluation import calculate_metrics
from datetime import datetime, timezone

from evaluation import select_forecast_at_cutoff


def test_selects_latest_forecast_before_cutoff():
    revisions = [
        {
            "publishTime": "2025-12-31T06:00:00Z",
            "generation": 18000,
        },
        {
            "publishTime": "2025-12-31T11:30:00Z",
            "generation": 19000,
        },
        {
            "publishTime": "2025-12-31T12:30:00Z",
            "generation": 20000,
        },
    ]

    cutoff = datetime(2025, 12, 31, 12, 0, tzinfo=timezone.utc)

    selected = select_forecast_at_cutoff(revisions, cutoff)

    assert selected is not None
    assert selected["publishTime"] == "2025-12-31T11:30:00Z"
    assert selected["generation"] == 19000


def test_returns_none_when_no_forecast_is_available():
    revisions = [
        {
            "publishTime": "2025-12-31T12:30:00Z",
            "generation": 20000,
        },
    ]

    cutoff = datetime(2025, 12, 31, 12, 0, tzinfo=timezone.utc)

    assert select_forecast_at_cutoff(revisions, cutoff) is None


def test_accepts_forecast_published_exactly_at_cutoff():
    revisions = [
        {
            "publishTime": "2025-12-31T12:00:00Z",
            "generation": 19500,
        },
    ]

    cutoff = datetime(2025, 12, 31, 12, 0, tzinfo=timezone.utc)

    selected = select_forecast_at_cutoff(revisions, cutoff)

    assert selected is not None
    assert selected["generation"] == 19500


def test_calculates_metrics_correctly():
    pairs = [
        {"forecast": 100, "actual": 90},
        {"forecast": 80, "actual": 100},
    ]

    metrics = calculate_metrics(pairs)

    assert metrics["interval_count"] == 2
    assert metrics["mae"] == 15
    assert metrics["rmse"] == (250 ** 0.5)
    assert metrics["bias"] == -5
    assert abs(metrics["wape"] - (30 / 190 * 100)) < 1e-9


def test_empty_pairs_return_undefined_metrics():
    metrics = calculate_metrics([])

    assert metrics["interval_count"] == 0
    assert metrics["mae"] is None
    assert metrics["rmse"] is None
    assert metrics["bias"] is None
    assert metrics["wape"] is None


def test_wape_is_undefined_when_actual_total_is_zero():
    pairs = [
        {"forecast": 10, "actual": 0},
        {"forecast": 0, "actual": 0},
    ]

    metrics = calculate_metrics(pairs)

    assert metrics["wape"] is None


def test_forecast_revisions_must_match_requested_delivery_hour():
    requested_start_time = "2026-01-01T01:00:00Z"

    revisions = [
        {
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-30T22:30:00Z",
            "generation": 19327,
        },
        {
            "startTime": requested_start_time,
            "publishTime": "2025-12-31T00:00:00Z",
            "generation": 19425,
        },
    ]

    matching_revisions = [
        revision
        for revision in revisions
        if revision.get("startTime") == requested_start_time
    ]

    cutoff = datetime(
        2025, 12, 31, 1, 0, tzinfo=timezone.utc
    )

    selected = select_forecast_at_cutoff(
        matching_revisions,
        cutoff,
    )

    assert selected is not None
    assert selected["startTime"] == requested_start_time
    assert selected["generation"] == 19425
