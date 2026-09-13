import datetime as dt
import unittest

from fetch_shioaji_data import latest_market_date
from fundamental_data import _refresh_event_label, _roc_date


class DataLayerTests(unittest.TestCase):
    def test_roc_date_conversion(self):
        self.assertEqual(_roc_date("1150913"), "2026-09-13")

    def test_expired_event_is_not_presented_as_upcoming(self):
        label, status = _refresh_event_label(
            "2026-08-14 (26Q2 法说会 - 本周五) | 每月 5 日发布营收",
            dt.date(2026, 9, 13),
        )
        self.assertEqual(status, "historical")
        self.assertIn("已舉行", label)
        self.assertNotIn("本周五", label)

    def test_future_event_stays_scheduled(self):
        label, status = _refresh_event_label(
            "2026-10-15 (26Q3 法说会) | 每月 10 日发布营收",
            dt.date(2026, 9, 13),
        )
        self.assertEqual(status, "scheduled")
        self.assertIn("2026-10-15", label)

    def test_weekend_uses_previous_trading_day(self):
        self.assertEqual(
            latest_market_date(dt.datetime(2026, 9, 13, 16, 0)),
            "2026-09-11",
        )


if __name__ == "__main__":
    unittest.main()
