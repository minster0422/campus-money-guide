import unittest
from pathlib import Path

import pandas as pd

from services.market import build_reference_history, market_snapshot_summary


class MarketReferenceHistoryTest(unittest.TestCase):
    def test_history_contains_only_sourced_comparison_endpoints(self):
        history = build_reference_history(
            104,
            4.0,
            as_of="2026-11-19",
            period_days=365,
        )
        self.assertEqual(len(history), 2)
        self.assertEqual(history.iloc[0]["price"], 100)
        self.assertEqual(history.iloc[-1]["price"], 104)
        self.assertEqual((history.iloc[-1]["date"] - history.iloc[0]["date"]).days, 365)

    def test_missing_change_returns_no_invented_history(self):
        history = build_reference_history(
            290,
            None,
            as_of="2026-11-19",
            period_days=0,
        )
        self.assertTrue(history.empty)

    def test_snapshot_summary_does_not_mix_values(self):
        assets = pd.DataFrame(
            [
                {"category": "레고", "source_name": "A"},
                {"category": "TCG", "source_name": "B"},
                {"category": "레고", "source_name": "A"},
            ]
        )
        self.assertEqual(
            market_snapshot_summary(assets),
            {"assets": 3, "categories": 2, "sources": 2},
        )

    def test_tcg_snapshots_have_five_matching_high_resolution_images(self):
        data_path = Path(__file__).parents[1] / "data" / "alternative_assets.csv"
        assets = pd.read_csv(data_path)
        cards = assets.loc[assets["category"] == "TCG"]

        self.assertEqual(len(cards), 5)
        self.assertEqual(set(cards["source_name"]), {"TCG Stacked"})
        for _, card in cards.iterrows():
            self.assertIn("images.pokemontcg.io/col1/", card["image_url"])
            self.assertTrue(card["image_url"].endswith("_hires.png"))
            self.assertEqual(card["image_source"], "Pokémon TCG API")
            image_path = Path(__file__).parents[1] / card["image_path"]
            self.assertTrue(image_path.exists())
            self.assertGreater(image_path.stat().st_size, 500_000)


if __name__ == "__main__":
    unittest.main()
