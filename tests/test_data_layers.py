import datetime as dt
import unittest
from unittest.mock import patch

from fetch_shioaji_data import latest_market_date
from fundamental_data import _refresh_event_label, _roc_date
from sync_public_content import announcement_rows, parse_rss, refresh_content


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

    def test_announcements_match_code_and_keep_published_date(self):
        rows = [{"公司代號": "2330", "主旨 ": "公告本公司召開法人說明會", "發言日期": "1151019"},
                {"公司代號": "2317", "主旨 ": "unrelated", "發言日期": "1151019"}]
        result = announcement_rows(rows, {"2330"})
        self.assertEqual(result["2330"][0]["published_at"], "2026-10-19")
        self.assertEqual(result["2330"][0]["category"], "investor_conference")

    def test_rss_keeps_source_publication_time(self):
        xml = b"<rss><channel><item><title>Company update</title><link>https://example.com/story</link><pubDate>Mon, 19 Oct 2026 08:00:00 GMT</pubDate></item></channel></rss>"
        result = parse_rss(xml, "Publisher")
        self.assertEqual(result[0]["published_at"], "2026-10-19T16:00+08:00")

    @patch("sync_public_content.fetch_news", side_effect=OSError("offline"))
    @patch("sync_public_content._fetch_json", side_effect=OSError("offline"))
    @patch("sync_public_content.fetch_fundamental_snapshot", side_effect=OSError("offline"))
    def test_content_failure_keeps_last_good_quotes_and_news(self, *_mocks):
        payload = {"stocks": [{"code": "2330", "last_price": 100, "official_announcements": [{"title": "old", "published_at": "2026-10-15"}]}],
                   "market_as_of": "2026-10-16", "news_feeds": {"market": [{"title": "old", "published_at": "2026-10-16"}]}}
        result = refresh_content(payload, "2026-10-19T20:00:00+08:00")
        self.assertEqual(result["market_as_of"], "2026-10-16")
        self.assertEqual(result["stocks"][0]["last_price"], 100)
        self.assertEqual(result["stocks"][0]["official_announcements"][0]["title"], "old")
        self.assertEqual(result["news_feeds"]["market"][0]["title"], "old")
        self.assertEqual(result["content_sources"]["announcements"]["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
