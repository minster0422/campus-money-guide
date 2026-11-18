from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class GoalPlan:
    target_amount: int
    current_amount: int
    remaining_months: int
    expected_min: int
    expected_max: int
    challenge_max: int
    base_gap: int
    optimistic_gap: int
    monthly_required: int


def calculate_goal_plan(
    selected: pd.DataFrame,
    *,
    target_amount: int,
    current_amount: int,
    remaining_months: int,
) -> GoalPlan:
    """Calculate a range without treating competitive prizes as guaranteed cash."""
    remaining_months = max(int(remaining_months), 1)
    if selected.empty:
        expected_min = expected_max = challenge_max = 0
    else:
        challenge = selected["competition"].eq("경쟁형")
        expected_min = int(selected.loc[~challenge, "amount_min"].sum())
        expected_max = int(selected.loc[~challenge, "amount_max"].sum())
        challenge_max = int(selected.loc[challenge, "amount_max"].sum())

    base_gap = max(target_amount - current_amount - expected_min, 0)
    optimistic_gap = max(
        target_amount - current_amount - expected_max - challenge_max,
        0,
    )
    monthly_required = math.ceil(base_gap / remaining_months)

    return GoalPlan(
        target_amount=target_amount,
        current_amount=current_amount,
        remaining_months=remaining_months,
        expected_min=expected_min,
        expected_max=expected_max,
        challenge_max=challenge_max,
        base_gap=base_gap,
        optimistic_gap=optimistic_gap,
        monthly_required=monthly_required,
    )


def format_money(amount: float | int) -> str:
    return f"{int(amount):,}원"

