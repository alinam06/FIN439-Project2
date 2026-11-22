"""Synthetic vintage records exercise the signal without FRED credentials."""

from datetime import date, timedelta
from hashlib import sha256
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from clean_checkout import CleanCheckout

from src.economic_signal import ENDPOINT, Vintage, eligible_vintages, evaluate_signal, load_archive

CUTOFF = date(2024, 2, 1)
OPEN = date(9999, 12, 31)


def fixture(newest="2.2", count=21):
    dates = [CUTOFF - timedelta(days=i) for i in range(count, 0, -1)]
    observations = [
        {"date": day.isoformat(), "realtime_start": (day + timedelta(days=1)).isoformat(),
         "realtime_end": OPEN.isoformat(), "value": newest if day == dates[-1] else "1.8"}
        for day in dates
    ]
    return {"realtime_start": "2024-01-01", "realtime_end": OPEN.isoformat(),
            "units": "lin", "output_type": 1, "offset": 0, "count": count,
            "observations": observations}


def encode(data):
    payload = json.dumps(data).encode()
    manifest = {"series_id": "BAA10Y", "endpoint": ENDPOINT, "frequency": "daily",
                "retrieved_at": "2024-02-02T12:00:00Z", "sha256": sha256(payload).hexdigest()}
    return payload, json.dumps(manifest).encode()


class SignalTests(unittest.TestCase):
    def test_future_publication_and_revision_are_excluded(self):
        observed = date(2024, 1, 29)
        future = CUTOFF + timedelta(days=1)
        initial = Vintage(observed, date(2024, 1, 30), CUTOFF, 1.8)
        revision = Vintage(observed, future, OPEN, 9.0)
        delayed = Vintage(date(2024, 1, 31), CUTOFF, OPEN, 3.0, future)
        self.assertEqual(eligible_vintages([revision, delayed, initial], CUTOFF), (initial,))
        self.assertEqual(eligible_vintages([revision, delayed, initial], future), (revision, delayed))

    def test_availability_is_inclusive_on_decision_date(self):
        archive = load_archive(*encode(fixture()))
        before = evaluate_signal(archive, CUTOFF - timedelta(days=1))
        on_day = evaluate_signal(archive, CUTOFF)
        self.assertEqual(before.status, "Unavailable")
        self.assertEqual(on_day.history[-1].vintage_start, CUTOFF)
        self.assertEqual(on_day.status, "Review")
        self.assertAlmostEqual(on_day.change_pp, .4)

    def test_missing_stale_and_outside_retrieval(self):
        archive = load_archive(*encode(fixture(newest=".")))
        result = evaluate_signal(archive, CUTOFF)
        self.assertEqual((result.status, result.missing_count), ("Unavailable", 1))
        self.assertEqual(evaluate_signal(archive, date(2024, 2, 3)).status, "Unavailable")
        raw = fixture()
        raw["observations"] = raw["observations"][:10]
        raw["count"] = 10
        result = evaluate_signal(load_archive(*encode(raw)), CUTOFF)
        self.assertIn("seven calendar days", result.explanation)

    def test_source_and_schema_validation(self):
        for change in ({"output_type": 2}, {"units": "pch"}, {"count": 99},
                       {"realtime_start": OPEN.isoformat()}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                load_archive(*encode(fixture() | change))
        raw = fixture(newest="nan")
        with self.assertRaisesRegex(ValueError, "Invalid spread"):
            load_archive(*encode(raw))
        raw = fixture()
        raw["observations"].append(raw["observations"][-1])
        raw["count"] += 1
        with self.assertRaisesRegex(ValueError, "duplicate vintage"):
            load_archive(*encode(raw))
        payload, manifest = encode(fixture())
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            load_archive(payload + b" ", manifest)

    def test_no_widening_remains_monitor_only(self):
        archive = load_archive(*encode(fixture(newest="1.7")))
        result = evaluate_signal(archive, CUTOFF)
        self.assertEqual(result.status, "Monitor")
        self.assertIn("ordinary risk review", result.explanation)


class SignalViewTests(CleanCheckout):
    def test_missing_signal_and_upload_leave_optimizer_out_of_signal_view(self):
        path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(path)).run()
        self.assertEqual(app.metric[1].value, "7.11%")
        app.selectbox(key="page").set_value("Portfolio Builder").run()
        app.selectbox(key="builder_view").set_value("Research and data").run()
        app.selectbox(key="research_topic").set_value("Economic Signals")
        with patch("src.portfolio.analyze", side_effect=AssertionError("Signal invoked allocation engine")):
            app.run()
            self.assertTrue(any("Signal unavailable" in item.value for item in app.warning))
            app.selectbox(key="data_import").set_value("ALFRED archive")
            def upload(label, **_):
                payload, manifest = encode(fixture())
                return io.BytesIO(payload if label.startswith("ALFRED") else manifest)
            with patch("streamlit.file_uploader", side_effect=upload):
                app.run()
                app.date_input[0].set_value(CUTOFF).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Review." in item.value for item in app.info))
        self.assertTrue(any("Allocation weights" in item.value for item in app.markdown))
        self.assertEqual(len(app.get("vega_lite_chart")), 1)
        app.sidebar.selectbox[0].set_value("Investment Overview").run()
        self.assertEqual(app.metric[1].value, "7.11%")
