from __future__ import annotations

import math
from datetime import date

import pandas as pd


def _phase(seed_key: str) -> float:
    return (sum(ord(character) for character in seed_key) % 17) / 5


def build_price_history(
    current_price: float | int,
    change_percent: float,
    *,
    periods: int = 26,
    seed_key: str = "asset",
) -> pd.DataFrame:
    """Build deterministic demo history that ends at the supplied current price."""
    periods = max(int(periods), 2)
    current = float(current_price)
    denominator = 1 + float(change_percent) / 100
    start = current / denominator if denominator > 0 else current
    phase = _phase(seed_key)
    prices: list[int] = []

    for index in range(periods):
        progress = index / (periods - 1)
        base = start + (current - start) * progress
        envelope = math.sin(math.pi * progress)
        wave = current * 0.022 * envelope * math.sin(index * 0.86 + phase)
        prices.append(max(int(round(base + wave)), 1))

    prices[0] = max(int(round(start)), 1)
    prices[-1] = max(int(round(current)), 1)
    dates = pd.date_range(end=pd.Timestamp(date.today()), periods=periods, freq="W")
    return pd.DataFrame({"date": dates, "price": prices})


def build_market_index(assets: pd.DataFrame, *, periods: int = 26) -> pd.DataFrame:
    """Average normalized demo histories into a cross-asset index."""
    if assets.empty:
        raise ValueError("assets must not be empty")

    normalized: list[pd.Series] = []
    dates: pd.Series | None = None
    for _, asset in assets.iterrows():
        history = build_price_history(
            asset["current_price"],
            asset["change_6m"],
            periods=periods,
            seed_key=str(asset["id"]),
        )
        dates = history["date"]
        normalized.append(history["price"] / history["price"].iloc[0] * 100)

    values = pd.concat(normalized, axis=1).mean(axis=1)
    return pd.DataFrame({"date": dates, "price": values.round(2)})
