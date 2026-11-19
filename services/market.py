from __future__ import annotations

import pandas as pd


def build_reference_history(
    current_value: float | int,
    change_percent: float | int | None,
    *,
    as_of: str,
    period_days: int,
) -> pd.DataFrame:
    """Return the two real comparison points implied by a sourced change rate.

    This deliberately avoids inventing intermediate prices. An empty frame means
    that the source supplied only a current snapshot and no comparable change.
    """
    if change_percent is None or pd.isna(change_percent) or int(period_days) <= 0:
        return pd.DataFrame(columns=["date", "price"])

    current = float(current_value)
    denominator = 1 + float(change_percent) / 100
    if denominator <= 0:
        return pd.DataFrame(columns=["date", "price"])

    end = pd.Timestamp(as_of)
    start = end - pd.Timedelta(days=int(period_days))
    previous = current / denominator
    return pd.DataFrame(
        {
            "date": [start, end],
            "price": [round(previous, 2), round(current, 2)],
        }
    )


def market_snapshot_summary(assets: pd.DataFrame) -> dict[str, int]:
    """Summarize coverage without combining incompatible currencies or indices."""
    if assets.empty:
        return {"assets": 0, "categories": 0, "sources": 0}
    return {
        "assets": int(len(assets)),
        "categories": int(assets["category"].nunique()),
        "sources": int(assets["source_name"].nunique()),
    }
