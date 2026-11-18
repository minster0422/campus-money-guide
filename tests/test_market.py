import unittest

import pandas as pd

from services.market import build_market_index, build_price_history


class MarketHistoryTest(unittest.TestCase):
    def test_history_ends_at_current_price(self):
        history = build_price_history(189_000, 7.8, seed_key="lego")
        self.assertEqual(len(history), 26)
        self.assertEqual(history.iloc[-1]["price"], 189_000)
        self.assertLess(history.iloc[0]["price"], history.iloc[-1]["price"])

    def test_market_index_starts_near_one_hundred(self):
        assets = pd.DataFrame(
            [
                {"id": "a", "current_price": 100_000, "change_6m": 10.0},
                {"id": "b", "current_price": 200_000, "change_6m": -5.0},
            ]
        )
        market = build_market_index(assets)
        self.assertAlmostEqual(market.iloc[0]["price"], 100.0, places=2)


if __name__ == "__main__":
    unittest.main()
