from __future__ import annotations

import unittest

import pandas as pd

from services.recommendation import filter_opportunities, rank_opportunities


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


class OpportunityFilterTests(unittest.TestCase):
    def setUp(self):
        self.ranked = pd.DataFrame(
            [
                {
                    "title": "통영시 생활비 장학금",
                    "organization": "학생지원팀",
                    "summary": "지역 장학금",
                    "tags": "장학금|생활비",
                    "region_requirement": "통영시",
                    "category": "장학금",
                    "eligible": False,
                    "match_score": 50,
                    "deadline": pd.Timestamp("2026-11-23"),
                    "amount_max": 1_000_000,
                },
                {
                    "title": "동계방학 근로장학생",
                    "organization": "학생지원팀",
                    "summary": "교내 근로",
                    "tags": "근로|장학",
                    "region_requirement": "제한 없음",
                    "category": "교내근로",
                    "eligible": True,
                    "match_score": 90,
                    "deadline": pd.Timestamp("2026-11-29"),
                    "amount_max": 0,
                },
            ]
        )

    def test_searches_title_and_region(self):
        result = filter_opportunities(self.ranked, query="통영시")
        self.assertEqual(result["title"].tolist(), ["통영시 생활비 장학금"])

    def test_filters_category(self):
        result = filter_opportunities(self.ranked, categories=["교내근로"])
        self.assertEqual(result["category"].tolist(), ["교내근로"])

    def test_sorts_by_largest_benefit(self):
        result = filter_opportunities(self.ranked, sort_by="혜택 큰 순")
        self.assertEqual(result.iloc[0]["title"], "통영시 생활비 장학금")

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
