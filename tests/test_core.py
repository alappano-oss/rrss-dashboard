import pandas as pd

from src.comparisons import variation
from src.data_cleaner import normalize_format, merge_deduplicate
from src.metrics import add_derived_metrics
from src.data_validator import validate_frame


def test_normalize_format():
    assert normalize_format("Video Reel") == "Reel"
    assert normalize_format("Carrusel de Instagram") == "Carrusel"


def test_variation():
    assert variation(125, 100) == (25, 25.0)
    assert variation(5, 0) is None


def test_duplicate_posts_are_removed():
    row = {"brand": "blu", "dedupe_key": "same"}
    existing = pd.DataFrame([row])
    merged, added, duplicates = merge_deduplicate(existing, pd.DataFrame([row]))
    assert len(merged) == 1
    assert added == 0
    assert duplicates == 1


def test_validator_reports_missing_date():
    problems = validate_frame(pd.DataFrame({"Alcance": [1]}))
    assert any("fecha" in problem.lower() for problem in problems)


def test_engagement_is_unavailable_without_source_metrics():
    frame = pd.DataFrame({"likes": [None], "comments": [None], "shares": [None], "saves": [None], "interactions_source": [None], "reach": [100], "impressions": [None]})
    result = add_derived_metrics(frame)
    assert pd.isna(result.loc[0, "interactions"])
