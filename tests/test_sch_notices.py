from __future__ import annotations

import unittest
from datetime import date

from services.sch_notices import (
    Board,
    classify_title,
    extract_amount_info,
    extract_deadline,
    extract_eligible_grades,
    is_relevant_title,
    parse_board_list,
)


class SchNoticeTests(unittest.TestCase):
    def test_extracts_title_range_deadline(self):
        deadline = extract_deadline(
            "동계방학 근로장학생 신청 안내 (11/23~29 신청)",
            "",
            date(2026, 11, 18),
        )
        self.assertEqual(deadline, date(2026, 11, 29))

    def test_extracts_labeled_body_deadline(self):
        deadline = extract_deadline(
            "생활비 장학생 선발 안내",
            "신청기간 : 2026. 11. 20. ~ 2026. 12. 4.\n발표 : 2026. 12. 20.",
            date(2026, 11, 18),
        )
        self.assertEqual(deadline, date(2026, 12, 4))

    def test_extracts_submission_deadline(self):
        deadline = extract_deadline(
            "재단 장학생 선발 안내",
            "마. 제출기한 : ~ 2026. 11. 16. (월) 이후 제출 건 접수X",
            date(2026, 11, 4),
        )
        self.assertEqual(deadline, date(2026, 11, 16))

    def test_classifies_competition(self):
        category, benefit, competition, tags = classify_title("학생 아이디어 공모전 개최 안내")
        self.assertEqual(category, "공모전")
        self.assertEqual(competition, "경쟁형")
        self.assertIn("상금", benefit)
        self.assertIn("공모전", tags)

    def test_excludes_unpaid_audience_recruitment(self):
        self.assertFalse(is_relevant_title("나눔실천 토론대회 방청 심사위원 모집"))

    def test_extracts_fixed_scholarship_range(self):
        low, high, note = extract_amount_info(
            "튜터링",
            "멘토Ⅰ형 : 장학금 125만원 / 멘토Ⅱ형 : 장학금 75만원 / 장학금 월 25만원",
        )
        self.assertEqual((low, high), (750_000, 1_250_000))
        self.assertEqual(note, "750,000원 ~ 1,250,000원")

    def test_extracts_hourly_wage_without_goal_total(self):
        low, high, note = extract_amount_info(
            "교내근로",
            "교내 시간당 10,320원 / 교외 시간당 12,790원",
        )
        self.assertEqual((low, high), (0, 0))
        self.assertEqual(note, "시급 10,320원 ~ 12,790원")

    def test_extracts_grade_range(self):
        self.assertEqual(extract_eligible_grades("2027-1학기 기준 2~3학년 재학생"), "2|3")

    def test_parses_official_board_row(self):
        html = """
        <div class="board_list"><table class="type_board"><tbody><tr>
          <td class="seq">1157</td>
          <td class="subject"><a href="?mode=view&amp;article_no=123&amp;board_no=456">
            동계방학 근로장학생 모집 안내 (11/23~29 신청)
          </a></td>
          <td class="writer"><span>작성자:</span> 학생지원팀</td>
          <td class="date"><span>날짜:</span> 2026-11-18</td>
        </tr></tbody></table></div>
        """
        board = Board("장학공지", "https://home.sch.ac.kr/sch/board.jsp", "456")
        records = parse_board_list(html, board)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["article_no"], "123")
        self.assertEqual(records[0]["organization"], "학생지원팀")
        self.assertTrue(str(records[0]["source_url"]).startswith("https://home.sch.ac.kr"))


if __name__ == "__main__":
    unittest.main()
