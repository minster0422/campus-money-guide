from __future__ import annotations

import unittest

import pandas as pd

from services.recommendation import rank_opportunities


def opportunity(region_requirement: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "opp-1",
                "title": "지역 장학금",
                "category": "장학금",
                "eligible_grades": "1|2|3|4",
                "residence": "전체",
                "region_requirement": region_requirement,
                "weekly_hours": 0,
                "tags": "장학금",
                "deadline": pd.Timestamp("2026-12-31"),
            }
        ]
    )


class RecommendationRegionTests(unittest.TestCase):
    def test_unknown_region_does_not_mark_local_notice_eligible(self):
        ranked = rank_opportunities(
            opportunity("통영시"),
            grade=1,
            residence="전체",
            available_hours=6,
            region="",
        )
        self.assertFalse(bool(ranked.iloc[0]["eligible"]))
        self.assertIn("통영시", ranked.iloc[0]["match_reason"])

    def test_matching_region_marks_local_notice_eligible(self):
        ranked = rank_opportunities(
            opportunity("통영시"),
            grade=1,
            residence="전체",
            available_hours=6,
            region="경남 통영시",
        )
        self.assertTrue(bool(ranked.iloc[0]["eligible"]))
        self.assertIn("지역 조건 일치", ranked.iloc[0]["match_reason"])

    def test_unrestricted_notice_remains_eligible(self):
        ranked = rank_opportunities(
            opportunity("제한 없음"),
            grade=1,
            residence="전체",
            available_hours=6,
            region="",
        )
        self.assertTrue(bool(ranked.iloc[0]["eligible"]))


if __name__ == "__main__":
    unittest.main()
