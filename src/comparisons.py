import pandas as pd

from src.metrics import summarize


def variation(current, previous):
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return (current - previous, (current - previous) / abs(previous) * 100)


def compare_periods(all_posts, selected, period_start=None, period_end=None):
    start = pd.Timestamp(period_start).normalize() if period_start is not None else selected.date.min().normalize()
    end = pd.Timestamp(period_end).normalize() if period_end is not None else selected.date.max().normalize()
    is_full_year = start.month == 1 and start.day == 1 and end.month == 12 and end.day == 31
    if is_full_year:
        prev_start = start - pd.DateOffset(years=1)
        prev_end = start - pd.Timedelta(days=1)
        previous = all_posts[all_posts.date.between(prev_start, prev_end)]
        return summarize(previous) if not previous.empty else None
    is_full_quarter = (
        start.day == 1
        and start.month in (1, 4, 7, 10)
        and end == (start + pd.offsets.MonthEnd(2)).normalize()
    )
    if is_full_quarter:
        prev_start = start - pd.offsets.MonthBegin(3)
        prev_end = start - pd.Timedelta(days=1)
        previous = all_posts[all_posts.date.between(prev_start, prev_end)]
        return summarize(previous) if not previous.empty else None
    is_full_month = start.day == 1 and end == (start + pd.offsets.MonthEnd(0)).normalize()
    if is_full_month:
        prev_start = (start - pd.offsets.MonthBegin(1)).normalize()
        prev_end = start - pd.Timedelta(days=1)
        previous = all_posts[all_posts.date.between(prev_start, prev_end)]
        return summarize(previous) if not previous.empty else None
    span = (end - start).days + 1
    prev_end = start - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=span - 1)
    previous = all_posts[all_posts.date.between(prev_start, prev_end)]
    return summarize(previous) if not previous.empty else None
