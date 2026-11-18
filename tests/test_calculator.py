import unittest

import pandas as pd

from services.calculator import calculate_goal_plan


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


if __name__ == "__main__":
    unittest.main()

