from __future__ import annotations

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
    interests: list[str] | None = None,
) -> pd.DataFrame:
    """Return opportunities ranked by a transparent, rule-based match score."""
    interests = interests or []
    ranked: list[dict[str, object]] = []

    for _, row in opportunities.iterrows():
        grades = _split_values(row.get("eligible_grades"))
        residences = _split_values(row.get("residence"))
        tags = _split_values(row.get("tags"))

        grade_ok = ALL_VALUE in grades or str(grade) in grades
        residence_ok = ALL_VALUE in residences or residence in residences
        required_hours = int(row.get("weekly_hours", 0) or 0)
        hours_ok = required_hours <= available_hours or required_hours == 0

        score = 40
        reasons: list[str] = []

        if grade_ok:
            score += 20
            reasons.append(f"{grade}학년 지원 가능")
        else:
            score -= 35
            reasons.append("학년 조건 확인 필요")

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

        record = row.to_dict()
        record["match_score"] = max(0, min(100, score))
        record["match_reason"] = " · ".join(reasons[:3]) or "기본 조건으로 추천"
        record["eligible"] = grade_ok and residence_ok and hours_ok
        ranked.append(record)

    result = pd.DataFrame(ranked)
    return result.sort_values(
        ["eligible", "match_score", "deadline"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def recommend_savings(
    savings: pd.DataFrame,
    *,
    remaining_months: int,
    monthly_budget: int,
) -> pd.DataFrame:
    """Rank savings products by term fit and affordable monthly contribution."""
    ranked = savings.copy()
    ranked["term_gap"] = (ranked["term_months"] - remaining_months).abs()
    ranked["affordable"] = ranked["min_monthly"] <= max(monthly_budget, 0)
    ranked["fit_score"] = (
        100
        - ranked["term_gap"].clip(upper=24) * 2
        + ranked["affordable"].astype(int) * 15
        + ranked["max_rate"]
    ).clip(upper=100)
    return ranked.sort_values(
        ["affordable", "fit_score", "max_rate"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

