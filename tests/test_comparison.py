import pandas as pd

from src.comparisons import compare_periods


def test_previous_period_uses_equal_length_range():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-07-01", "2026-07-02", "2026-07-03", "2026-08-01", "2026-08-02", "2026-08-03"]),
            "reach": [10, 20, 30, 15, 25, 35],
            "impressions": [None] * 6,
            "interactions": [1, 2, 3, 2, 3, 4],
            "er_reach": [10.0] * 6,
            "followers_gained": [None] * 6,
            "views": [None] * 6,
        }
    )
    current = frame[frame.date.dt.month == 8]
    previous = compare_periods(frame, current)
    assert previous["reach"] == 60
