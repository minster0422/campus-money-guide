from __future__ import annotations

import math
import re
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


@dataclass(frozen=True)
class SavingsProjection:
    monthly_contribution: int
    months: int
    principal: int
    base_interest: int
    max_interest: int
    base_maturity: int
    max_maturity: int


@dataclass(frozen=True)
class HourlyIncomeProjection:
    hourly_min: int
    hourly_max: int
    weekly_hours: int
    months: int
    income_min: int
    income_max: int


def calculate_hourly_income(
    amount_note: object,
    *,
    weekly_hours: int,
    months: int,
) -> HourlyIncomeProjection | None:
    """Estimate gross income from a Korean hourly-wage range in an opportunity note."""
    values = re.findall(r"([\d,]+)\s*원", str(amount_note))
    if "시급" not in str(amount_note) or not values:
        return None

    hourly_min = int(values[0].replace(",", ""))
    hourly_max = int(values[1].replace(",", "")) if len(values) > 1 else hourly_min
    weekly_hours = max(int(weekly_hours), 0)
    months = max(int(months), 1)
    estimated_weeks = months * 4.345
    income_min = round(hourly_min * weekly_hours * estimated_weeks)
    income_max = round(hourly_max * weekly_hours * estimated_weeks)
    return HourlyIncomeProjection(
        hourly_min=hourly_min,
        hourly_max=max(hourly_max, hourly_min),
        weekly_hours=weekly_hours,
        months=months,
        income_min=income_min,
        income_max=max(income_max, income_min),
    )


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


def calculate_savings_projection(
    *,
    monthly_contribution: int,
    months: int,
    base_rate: float,
    max_rate: float,
) -> SavingsProjection:
    """Estimate simple-interest installment savings before tax.

    Each monthly installment earns interest for a different number of months.
    For n installments, the total interest-bearing months are n + ... + 1.
    Product-specific payment dates, compounding, and preferential eligibility can
    change the actual amount, so this is intended as a comparison estimate only.
    """
    monthly_contribution = max(int(monthly_contribution), 0)
    months = max(int(months), 1)
    principal = monthly_contribution * months
    interest_months = months * (months + 1) / 2

    def estimate(rate: float) -> int:
        return round(monthly_contribution * (max(float(rate), 0) / 100) * interest_months / 12)

    base_interest = estimate(base_rate)
    max_interest = max(estimate(max_rate), base_interest)
    return SavingsProjection(
        monthly_contribution=monthly_contribution,
        months=months,
        principal=principal,
        base_interest=base_interest,
        max_interest=max_interest,
        base_maturity=principal + base_interest,
        max_maturity=principal + max_interest,
    )


def format_money(amount: float | int) -> str:
    return f"{int(amount):,}원"

