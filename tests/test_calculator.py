import unittest

import pandas as pd

from services.calculator import calculate_goal_plan, calculate_savings_projection


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


if __name__ == "__main__":
    unittest.main()

