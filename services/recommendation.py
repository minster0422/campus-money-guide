from __future__ import annotations

from datetime import date

import pandas as pd


ALL_VALUE = "전체"


def _split_values(raw: object) -> set[str]:
    if pd.isna(raw):
        return set()
    return {value.strip() for value in str(raw).split("|") if value.strip()}


def rank_opportunities(
    opportunities: pd.DataFrame,
    *,
    grade: int,
    residence: str,
    available_hours: int,
    region: str = "",
    interests: list[str] | None = None,
    as_of: date | None = None,
) -> pd.DataFrame:
    """Return opportunities ranked by a transparent, rule-based match score."""
    interests = interests or []
    as_of = as_of or date.today()
    ranked: list[dict[str, object]] = []

    for _, row in opportunities.iterrows():
        grades = _split_values(row.get("eligible_grades"))
        residences = _split_values(row.get("residence"))
        required_regions = _split_values(row.get("region_requirement"))
        tags = _split_values(row.get("tags"))

        grade_ok = ALL_VALUE in grades or str(grade) in grades
        residence_ok = ALL_VALUE in residences or residence in residences
        region_restricted = bool(required_regions) and "제한 없음" not in required_regions
        normalized_region = region.strip()
        region_ok = not region_restricted or (
            bool(normalized_region)
            and any(
                required in normalized_region or normalized_region in required
                for required in required_regions
            )
        )
        required_hours = int(row.get("weekly_hours", 0) or 0)
        hours_ok = required_hours <= available_hours or required_hours == 0
        deadline_value = pd.to_datetime(row.get("deadline"), errors="coerce")
        days_left = (
            (deadline_value.date() - as_of).days
            if not pd.isna(deadline_value)
            else None
        )
        is_closed = days_left is not None and days_left < 0

        score = 40
        reasons: list[str] = []

        if grade_ok:
            score += 20
            reasons.append(f"{grade}학년 지원 가능")
        else:
            score -= 35
            reasons.append("학년 조건 확인 필요")

        if region_restricted:
            region_label = "·".join(sorted(required_regions))
            if region_ok:
                score += 15
                reasons.append(f"{region_label} 지역 조건 일치")
            else:
                score -= 40
                reasons.append(f"{region_label} 거주·연고 조건 확인 필요")

        if residence_ok:
            score += 15
            if residence != ALL_VALUE:
                reasons.append(f"{residence} 조건 일치")
        else:
            score -= 20
            reasons.append("거주 조건 확인 필요")

        if hours_ok:
            score += 15
            if required_hours:
                reasons.append(f"주 {required_hours}시간 활동 가능")
        else:
            score -= 25
            reasons.append("가능 시간보다 활동시간이 많음")

        if interests and (row.get("category") in interests or tags.intersection(interests)):
            score += 10
            reasons.append("관심 분야 일치")

        if is_closed:
            score = 0
            reasons.insert(0, "신청 마감")

        record = row.to_dict()
        record["match_score"] = max(0, min(100, score))
        record["match_reason"] = " · ".join(reasons[:3]) or "기본 조건으로 추천"
        record["eligible"] = (
            grade_ok and residence_ok and hours_ok and region_ok and not is_closed
        )
        record["is_closed"] = is_closed
        record["days_left"] = days_left
        ranked.append(record)

    result = pd.DataFrame(ranked)
    return result.sort_values(
        ["is_closed", "eligible", "match_score", "deadline"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def filter_opportunities(
    opportunities: pd.DataFrame,
    *,
    query: str = "",
    categories: list[str] | None = None,
    sort_by: str = "추천순",
    include_closed: bool = True,
    deadline_within_days: int | None = None,
) -> pd.DataFrame:
    """Search, filter, and sort an already-ranked opportunity table."""
    result = opportunities.copy()
    if "is_closed" not in result.columns:
        result["is_closed"] = False
    if not include_closed:
        result = result[~result["is_closed"].fillna(False)]
    if deadline_within_days is not None and "days_left" in result.columns:
        days_left = pd.to_numeric(result["days_left"], errors="coerce")
        result = result[days_left.between(0, deadline_within_days, inclusive="both")]
    normalized_query = query.strip().casefold()
    if normalized_query:
        searchable_columns = ["title", "organization", "summary", "tags", "region_requirement"]
        searchable = pd.Series("", index=result.index, dtype="object")
        for column in searchable_columns:
            if column in result.columns:
                searchable = searchable + " " + result[column].fillna("").astype(str)
        result = result[searchable.str.casefold().str.contains(normalized_query, regex=False)]

    categories = categories or []
    if categories:
        result = result[result["category"].isin(categories)]

    if sort_by == "마감 임박순":
        result = result.sort_values(
            ["is_closed", "deadline", "eligible", "match_score"],
            ascending=[True, True, False, False],
            na_position="last",
        )
    elif sort_by == "혜택 큰 순":
        result = result.sort_values(
            ["is_closed", "amount_max", "eligible", "match_score", "deadline"],
            ascending=[True, False, False, False, True],
            na_position="last",
        )
    else:
        result = result.sort_values(
            ["is_closed", "eligible", "match_score", "deadline"],
            ascending=[True, False, False, True],
            na_position="last",
        )
    return result.reset_index(drop=True)


def recommend_savings(
    savings: pd.DataFrame,
    *,
    remaining_months: int,
    monthly_budget: int,
) -> pd.DataFrame:
    """Rank savings by usable term, monthly affordability, and base-rate value.

    Maximum advertised rates are deliberately excluded from the fit score because
    they can require restrictive preferential conditions. They remain available
    in the returned frame for comparison in the UI.
    """
    ranked = savings.copy()
    below_range = (ranked["min_term_months"] - remaining_months).clip(lower=0)
    above_range = (remaining_months - ranked["max_term_months"]).clip(lower=0)
    ranked["term_gap"] = below_range + above_range
    ranked["matched_term_months"] = remaining_months
    ranked["matched_term_months"] = ranked["matched_term_months"].clip(
        lower=ranked["min_term_months"],
        upper=ranked["max_term_months"],
    )
    ranked["affordable"] = ranked["min_monthly"] <= max(monthly_budget, 0)
    ranked["within_monthly_limit"] = (
        (ranked["max_monthly"] <= 0) | (monthly_budget <= ranked["max_monthly"])
    )
    ranked["fit_score"] = (
        62
        - ranked["term_gap"].clip(upper=24) * 4
        + ranked["affordable"].astype(int) * 20
        + ranked["within_monthly_limit"].astype(int) * 8
        + ranked["base_rate"].clip(upper=5) * 2
        - (ranked["condition_level"].clip(lower=1) - 1) * 4
    ).clip(lower=0, upper=100)
    return ranked.sort_values(
        ["affordable", "fit_score", "base_rate", "condition_level"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)

