#!/usr/bin/env python3
"""
Tests for eBay Kleinanzeigen Scraper
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ebay_kleinanzeigen import (
    KleinanzeigenScraper,
    KleinanzeigenAd,
    TelegramNotifier,
    SlackNotifier
)


class TestKleinanzeigenAd(unittest.TestCase):
    """Test KleinanzeigenAd dataclass."""
    
    def test_create_ad(self):
        """Test ad creation."""
        ad = KleinanzeigenAd(
            id="12345",
            title="iPhone 15 Pro",
            description="Neuwertig",
            price="750 €",
            price_value=750.0,
            location="Berlin",
            distance="5 km",
            date_posted="25.02.2025",
            seller_name="Max123",
            seller_type="private",
            image_url="http://example.com/img.jpg",
            url="http://example.com/ad",
            category="elektronik",
            is_top_ad=False
        )
        
        self.assertEqual(ad.id, "12345")
        self.assertEqual(ad.title, "iPhone 15 Pro")
        self.assertEqual(ad.price_value, 750.0)
    
    def test_get_hash(self):
        """Test hash generation for deduplication."""
        ad = KleinanzeigenAd(
            id="12345",
            title="iPhone 15 Pro",
            description="Test",
            price="750 €",
            price_value=750.0,
            location="Berlin",
            distance=None,
            date_posted="25.02.2025",
            seller_name="Max",
            seller_type="private",
            image_url=None,
            url="http://example.com",
            category="",
            is_top_ad=False
        )
        
        hash1 = ad.get_hash()
        hash2 = ad.get_hash()
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 32)  # MD5 length
    
    def test_to_dict(self):
        """Test serialization to dict."""
        ad = KleinanzeigenAd(
            id="12345",
            title="Test",
            description="Desc",
            price="100 €",
            price_value=100.0,
            location="Hamburg",
            distance=None,
            date_posted="25.02.2025",
            seller_name="User",
            seller_type="private",
            image_url=None,
            url="http://test.com",
            category="",
            is_top_ad=True
        )
        
        d = ad.to_dict()
        self.assertEqual(d["id"], "12345")
        self.assertEqual(d["is_top_ad"], True)


class TestTelegramNotifier(unittest.TestCase):
    """Test Telegram notifications."""
    
    def setUp(self):
        self.notifier = TelegramNotifier("test_token", "123456789")
    
    @patch('ebay_kleinanzeigen.requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message send."""
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response
        
        result = self.notifier.send_message("Test message")
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('ebay_kleinanzeigen.requests.post')
    def test_send_message_failure(self, mock_post):
        """Test failed message send."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "description": "Chat not found"
        }
        mock_post.return_value = mock_response
        
        result = self.notifier.send_message("Test")
        
        self.assertFalse(result)
    
    def test_format_ad_message(self):
        """Test ad message formatting."""
        ad = KleinanzeigenAd(
            id="12345",
            title="iPhone 15 Pro 256GB",
            description="Neuwertiges iPhone, kaum benutzt. Keine Kratzer.",
            price="750 € VB",
            price_value=750.0,
            location="Berlin Mitte",
            distance="3 km",
            date_posted="25.02.2025",
            seller_name="TechSeller",
            seller_type="private",
            image_url="http://img.com/1.jpg",
            url="http://ebay.de/ad/12345",
            category="elektronik",
            is_top_ad=False
        )
        
        message = self.notifier.format_ad_message(ad)
        
        self.assertIn("iPhone 15 Pro 256GB", message)
        self.assertIn("750 € VB", message)
        self.assertIn("Berlin Mitte", message)
        self.assertIn("👤 Privat", message)
        self.assertNotIn("🔥 TOP ANZEIGE", message)
    
    def test_format_ad_message_top(self):
        """Test top ad formatting."""
        ad = KleinanzeigenAd(
            id="12345",
            title="TOP Produkt",
            description="Beschreibung",
            price="100 €",
            price_value=100.0,
            location="München",
            distance=None,
            date_posted="25.02.2025",
            seller_name="Seller",
            seller_type="commercial",
            image_url=None,
            url="http://test.com",
            category="",
            is_top_ad=True
        )
        
        message = self.notifier.format_ad_message(ad)
        
        self.assertIn("🔥", message)
        self.assertIn("TOP ANZEIGE", message)
        self.assertIn("🏪 Gewerblich", message)


class TestSlackNotifier(unittest.TestCase):
    """Test Slack notifications."""
    
    def setUp(self):
        self.notifier = SlackNotifier("https://hooks.slack.com/test")
    
    @patch('ebay_kleinanzeigen.requests.post')
    def test_send_ad_notification(self, mock_post):
        """Test ad notification to Slack."""
        mock_post.return_value = Mock(status_code=200)
        
        ad = KleinanzeigenAd(
            id="12345",
            title="MacBook Pro",
            description="Test",
            price="1200 €",
            price_value=1200.0,
            location="Köln",
            distance=None,
            date_posted="25.02.2025",
            seller_name="AppleFan",
            seller_type="private",
            image_url=None,
            url="http://test.com/12345",
            category="",
            is_top_ad=False
        )
        
        result = self.notifier.send_ad_notification(ad)
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Check attachment was sent
        call_args = mock_post.call_args
        payload = call_args[1].get("json") or call_args[0][0]
        self.assertIn("attachments", payload)


class TestKleinanzeigenScraper(unittest.TestCase):
    """Test main scraper functionality."""
    
    def setUp(self):
        with patch.dict(os.environ, {}):
            self.scraper = KleinanzeigenScraper()
            self.scraper.seen_ads = set()
    
    def test_parse_price_with_value(self):
        """Test price parsing with value."""
        price, value = self.scraper._parse_price("750 € VB")
        self.assertEqual(price, "750 € VB")
        self.assertEqual(value, 750.0)
    
    def test_parse_price_zu_verschenken(self):
        """Test price parsing for free items."""
        price, value = self.scraper._parse_price("Zu verschenken")
        self.assertEqual(price, "Zu verschenken")
        self.assertIsNone(value)
    
    def test_parse_price_vb_only(self):
        """Test price parsing for VB only."""
        price, value = self.scraper._parse_price("VB")
        self.assertEqual(price, "VB")
        self.assertIsNone(value)
    
    def test_parse_price_with_dots(self):
        """Test price parsing with thousand separator."""
        price, value = self.scraper._parse_price("1.250 €")
        self.assertEqual(value, 1250.0)
    
    def test_get_headers(self):
        """Test header generation."""
        headers = self.scraper._get_headers()
        
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept", headers)
        self.assertIn("Accept-Language", headers)
    
    @patch('ebay_kleinanzeigen.requests.Session.get')
    def test_search_success(self, mock_get):
        """Test successful search."""
        # Mock HTML response
        html = '''
        <html>
        <body>
            <article class="aditem" data-adid="12345">
                <h2><a href="/s-anzeige/iphone-15/12345">iPhone 15 Pro</a></h2>
                <p>Neuwertiges iPhone</p>
                <div class="adprice">750 € VB</div>
                <div class="aditem-main--middle--bottom">
                    <span>Berlin (5 km)</span>
                </div>
                <img src="http://img.com/1.jpg" />
            </article>
        </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = self.scraper.search("iPhone 15", pages=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "iPhone 15 Pro")
        self.assertEqual(results[0].price, "750 € VB")
        self.assertEqual(results[0].location, "Berlin")
        self.assertEqual(results[0].distance, "5 km")
    
    def test_extract_ad_from_article(self):
        """Test ad extraction from HTML article."""
        from bs4 import BeautifulSoup
        
        html = '''
        <article class="aditem" data-adid="12345">
            <h2><a href="/s-anzeige/macbook-pro/12345">MacBook Pro 16"</a></h2>
            <p>Neuwertig mit Garantie</p>
            <div class="adprice">2.500 €</div>
            <div class="aditem-main--middle--bottom">
                <span>München</span>
            </div>
            <img src="http://img.com/mac.jpg" />
        </article>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('article')
        
        ad = self.scraper._extract_ad(article)
        
        self.assertIsNotNone(ad)
        self.assertEqual(ad.title, "MacBook Pro 16\"")
        self.assertEqual(ad.price_value, 2500.0)
        self.assertEqual(ad.location, "München")
    
    def test_check_for_new_ads(self):
        """Test detecting new ads."""
        # Create test ads
        ad1 = KleinanzeigenAd(
            id="1", title="Ad 1", description="Desc", price="100 €",
            price_value=100.0, location="Berlin", distance=None,
            date_posted="25.02.2025", seller_name="User1", seller_type="private",
            image_url=None, url="http://test.com/1", category="", is_top_ad=False
        )
        ad2 = KleinanzeigenAd(
            id="2", title="Ad 2", description="Desc", price="200 €",
            price_value=200.0, location="Hamburg", distance=None,
            date_posted="25.02.2025", seller_name="User2", seller_type="private",
            image_url=None, url="http://test.com/2", category="", is_top_ad=False
        )
        
        # Mark ad1 as seen
        self.scraper.seen_ads.add(ad1.get_hash())
        
        # Mock search to return both ads
        self.scraper.search = Mock(return_value=[ad1, ad2])
        self.scraper._notify_new_ad = Mock()
        
        new_ads = self.scraper.check_for_new_ads("test", notify=False)
        
        # Only ad2 should be new
        self.assertEqual(len(new_ads), 1)
        self.assertEqual(new_ads[0].id, "2")


class TestIntegration(unittest.TestCase):
    """Integration-style tests."""
    
    def test_full_scenario(self):
        """Test complete scraping scenario."""
        scraper = KleinanzeigenScraper()
        
        # Test price parsing
        test_cases = [
            ("100 €", 100.0),
            ("1.500 € VB", 1500.0),
            ("Zu verschenken", None),
            ("VB", None),
            ("Preis auf Anfrage", None),
        ]
        
        for price_text, expected in test_cases:
            _, value = scraper._parse_price(price_text)
            self.assertEqual(value, expected, f"Failed for: {price_text}")


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestKleinanzeigenAd))
    suite.addTests(loader.loadTestsFromTestCase(TestTelegramNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestSlackNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestKleinanzeigenScraper))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
