"""Synthetic fixtures exercise ingestion without a provider or credentials."""

from datetime import date
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout

from src.historical import TICKERS, load_historical


def fixture():
    dates = pd.date_range("2019-01-31", periods=61, freq="BME")
    monthly = np.zeros((60, 4))
    monthly[:3] = [[.005, .10, .05, -.05], [-.005, -.10, -.05, .05], [.005, .05, .025, -.025]]
    prices = pd.DataFrame(np.vstack((np.ones(4), np.cumprod(1 + monthly, axis=0))) * 100,
                          index=dates, columns=TICKERS)
    meta = {
        "provider": "Synthetic fixture", "frequency": "monthly", "currency": "USD",
        "downloaded_at": "2024-02-02T12:00:00Z", "adjusted_price_definition": "Synthetic",
        "distribution_method": "Synthetic", "usage_restrictions": "Test only",
        "calendar_reference": "Weekday-only synthetic fixture", "exclusions": [],
        "source_urls": {ticker: f"https://example.com/{ticker}" for ticker in TICKERS},
        "instrument_identifiers": {ticker: f"synthetic-{ticker}" for ticker in TICKERS},
    }
    return prices, json.dumps(meta).encode()


def encode(prices):
    return prices.to_csv(index_label="date", date_format="%Y-%m-%d").encode()


class HistoricalTests(unittest.TestCase):
    def test_alignment_and_total_returns(self):
        prices, metadata = fixture()
        sample = load_historical(encode(prices), metadata)
        self.assertEqual(sample.sample_dates, (date(2019, 1, 31), date(2024, 1, 31)))
        self.assertEqual(sample.returns.shape, (60, 4))
        self.assertEqual(sample.returns.index[0], pd.Timestamp("2019-02-28"))
        np.testing.assert_allclose(sample.returns["IEF"].iloc[:4], [.10, -.10, .05, 0], atol=1e-14)

    def test_annualization_covariance_and_correlation(self):
        prices, metadata = fixture()
        sample = load_historical(encode(prices), metadata)
        monthly_variance = (.10 ** 2 + .10 ** 2 + .05 ** 2 - .05 ** 2 / 60) / 59
        self.assertAlmostEqual(sample.statistics.loc["IEF", "Annualized arithmetic return"], .01)
        self.assertAlmostEqual(sample.statistics.loc["IEF", "Annualized volatility"],
                               (12 * monthly_variance) ** .5)
        self.assertAlmostEqual(sample.covariance.loc["IEF", "LQD"], 6 * monthly_variance)
        self.assertAlmostEqual(sample.correlation.loc["IEF", "LQD"], 1)
        self.assertAlmostEqual(sample.correlation.loc["IEF", "VT"], -1)

    def test_cumulative_performance_and_drawdown(self):
        prices, metadata = fixture()
        sample = load_historical(encode(prices), metadata)
        self.assertAlmostEqual(sample.cumulative["IEF"].iloc[0], 0)
        self.assertAlmostEqual(sample.statistics.loc["IEF", "Cumulative total return"], .0395)
        self.assertAlmostEqual(sample.statistics.loc["IEF", "Maximum drawdown"], .10)

    def test_order_duplicates_and_gaps_are_rejected(self):
        prices, metadata = fixture()
        duplicate = pd.concat([prices.iloc[:1], prices.iloc[:1], prices.iloc[2:]])
        for invalid, expected in ((prices.iloc[::-1], "ascending"), (duplicate, "Duplicate"),
                                  (prices.drop(prices.index[4]), "consecutive"),
                                  (prices.iloc[:-1], "61 aligned")):
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                load_historical(encode(invalid), metadata)

    def test_missing_nonpositive_and_nonfinite_prices_are_rejected(self):
        prices, metadata = fixture()
        for value, expected in ((np.nan, "Missing"), (0, "positive"), (-1, "positive"),
                                (np.inf, "finite")):
            prices.iloc[0, 0] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, expected):
                load_historical(encode(prices), metadata)

    def test_wrong_schema_metadata_and_partial_month_are_rejected(self):
        prices, metadata = fixture()
        with self.assertRaisesRegex(ValueError, "header"):
            load_historical(encode(prices.drop(columns="BIL")), metadata)
        meta = json.loads(metadata)
        meta["downloaded_at"] = "2024-01-31T22:30:00Z"
        with self.assertRaisesRegex(ValueError, "incomplete"):
            load_historical(encode(prices), json.dumps(meta).encode())
        with self.assertRaisesRegex(ValueError, "source metadata"):
            load_historical(encode(prices), b"{}")

    def test_outliers_are_reported_and_retained(self):
        prices, metadata = fixture()
        prices.iloc[2, 3] = 175
        sample = load_historical(encode(prices), metadata)
        self.assertTrue(any("VT 2019-03-29" in warning for warning in sample.warnings))
        self.assertEqual(len(sample.returns), 60)
        self.assertAlmostEqual(sample.prices["VT"].iloc[2], 175)


class HistoricalDashboardTests(CleanCheckout):
    def test_classroom_and_empty_exploration_work_without_network(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        with patch("socket.getaddrinfo", side_effect=AssertionError("Unexpected DNS request")):
            app = AppTest.from_file(str(path)).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.metric[1].value, "7.11%")
            app.selectbox(key="page").set_value("Portfolio Builder").run()
            app.selectbox(key="builder_view").set_value("Research and data").run()
            app.selectbox(key="research_topic").set_value("Historical Market Data").run()
            self.assertFalse(app.exception)
            self.assertFalse(app.metric)
            self.assertTrue(any("Missing from data/" in item.value for item in app.info))

    def test_valid_upload_renders_charts_without_running_optimizer(self):
        prices, metadata = fixture()
        uploads = [io.BytesIO(encode(prices)), io.BytesIO(metadata)]
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        app.selectbox(key="page").set_value("Portfolio Builder").run()
        app.selectbox(key="builder_view").set_value("Research and data").run()
        app.selectbox(key="research_topic").set_value("Historical Market Data")
        app.selectbox(key="data_import").set_value("ETF panel")
        with (patch("streamlit.file_uploader", side_effect=uploads),
              patch("src.portfolio.analyze", side_effect=AssertionError("Optimizer called"))):
            app.run()
        self.assertFalse(app.exception)
        self.assertTrue(any("structural checks passed" in item.value for item in app.success))
        self.assertEqual(len(app.get("vega_lite_chart")), 4)
