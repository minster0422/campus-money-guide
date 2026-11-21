import unittest

import pandas as pd

from services.calculator import (
    calculate_goal_plan,
    calculate_hourly_income,
    calculate_savings_projection,
    compare_goal_scenarios,
)


class GoalCalculatorTest(unittest.TestCase):
    def test_competitive_prize_is_not_counted_in_base_plan(self):
        selected = pd.DataFrame(
            [
                {"competition": "근로형", "amount_min": 300_000, "amount_max": 400_000},
                {"competition": "경쟁형", "amount_min": 100_000, "amount_max": 1_000_000},
            ]
        )
        plan = calculate_goal_plan(
            selected,
            target_amount=2_000_000,
            current_amount=200_000,
            remaining_months=6,
        )
        self.assertEqual(plan.expected_min, 300_000)
        self.assertEqual(plan.challenge_max, 1_000_000)
        self.assertEqual(plan.base_gap, 1_500_000)
        self.assertEqual(plan.monthly_required, 250_000)

        scenarios = compare_goal_scenarios(plan)
        self.assertEqual(scenarios.baseline_monthly, 300_000)
        self.assertEqual(scenarios.planned_monthly, 250_000)
        self.assertEqual(scenarios.optimistic_monthly, 66_667)
        self.assertEqual(scenarios.monthly_reduction, 50_000)

    def test_empty_selection(self):
        plan = calculate_goal_plan(
            pd.DataFrame(),
            target_amount=1_200_000,
            current_amount=0,
            remaining_months=12,
        )
        self.assertEqual(plan.base_gap, 1_200_000)
        self.assertEqual(plan.monthly_required, 100_000)


class SavingsProjectionTest(unittest.TestCase):
    def test_matches_twelve_month_installment_example(self):
        projection = calculate_savings_projection(
            monthly_contribution=200_000,
            months=12,
            base_rate=2.85,
            max_rate=4.35,
        )
        self.assertEqual(projection.principal, 2_400_000)
        self.assertEqual(projection.base_interest, 37_050)
        self.assertEqual(projection.max_interest, 56_550)
        self.assertEqual(projection.max_maturity, 2_456_550)

    def test_zero_contribution_stays_zero(self):
        projection = calculate_savings_projection(
            monthly_contribution=0,
            months=6,
            base_rate=3.0,
            max_rate=4.0,
        )
        self.assertEqual(projection.principal, 0)
        self.assertEqual(projection.max_interest, 0)


class HourlyIncomeProjectionTest(unittest.TestCase):
    def test_estimates_hourly_range_with_explicit_assumptions(self):
        projection = calculate_hourly_income(
            "시급 10,320원 ~ 12,790원",
            weekly_hours=6,
            months=2,
        )
        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual(projection.hourly_min, 10_320)
        self.assertEqual(projection.hourly_max, 12_790)
        self.assertEqual(projection.income_min, 538_085)
        self.assertEqual(projection.income_max, 666_871)

    def test_returns_none_for_non_hourly_note(self):
        self.assertIsNone(
            calculate_hourly_income("1,000,000원", weekly_hours=6, months=2)
        )


if __name__ == "__main__":
    unittest.main()

