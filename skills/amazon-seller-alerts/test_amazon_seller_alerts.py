#!/usr/bin/env python3
"""
Tests for Amazon Seller Central Alerts
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amazon_seller_alerts import (
    AmazonSellerAlerts,
    SPAPIAuth,
    TelegramNotifier,
    SlackNotifier,
    AmazonOrder,
    AmazonReview,
    InventoryAlert
)


class TestSPAPIAuth(unittest.TestCase):
    """Test SP-API authentication."""
    
    def setUp(self):
        self.auth = SPAPIAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            aws_access_key="test_aws_key",
            aws_secret_key="test_aws_secret"
        )
    
    @patch('amazon_seller_alerts.requests.post')
    def test_get_access_token_success(self, mock_post):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response
        
        token = self.auth.get_access_token()
        
        self.assertEqual(token, "test_token_123")
        self.assertEqual(self.auth.access_token, "test_token_123")
        self.assertIsNotNone(self.auth.token_expires_at)
    
    @patch('amazon_seller_alerts.requests.post')
    def test_get_access_token_cached(self, mock_post):
        """Test token caching."""
        # Set a valid token
        self.auth.access_token = "cached_token"
        self.auth.token_expires_at = datetime.now() + timedelta(hours=1)
        
        token = self.auth.get_access_token()
        
        self.assertEqual(token, "cached_token")
        mock_post.assert_not_called()
    
    def test_get_headers(self):
        """Test headers generation."""
        with patch.object(self.auth, 'get_access_token', return_value="test_token"):
            headers = self.auth.get_headers()
            
            self.assertEqual(headers["x-amz-access-token"], "test_token")
            self.assertEqual(headers["Content-Type"], "application/json")


class TestTelegramNotifier(unittest.TestCase):
    """Test Telegram notifications."""
    
    def setUp(self):
        self.notifier = TelegramNotifier(
            bot_token="test_token",
            chat_id="123456789"
        )
    
    @patch('amazon_seller_alerts.requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message send."""
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response
        
        result = self.notifier.send_message("Test message")
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Check call arguments
        call_args = mock_post.call_args
        self.assertIn("test_token", call_args[0][0])
        self.assertEqual(call_args[1]["json"]["chat_id"], "123456789")
        self.assertEqual(call_args[1]["json"]["text"], "Test message")
    
    @patch('amazon_seller_alerts.requests.post')
    def test_send_message_failure(self, mock_post):
        """Test failed message send."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "description": "Chat not found"
        }
        mock_post.return_value = mock_response
        
        result = self.notifier.send_message("Test message")
        
        self.assertFalse(result)
    
    def test_format_order_message(self):
        """Test order message formatting."""
        order = AmazonOrder(
            order_id="304-1234567-1234567",
            purchase_date="2025-02-25T14:30:00Z",
            status="Unshipped",
            fulfillment_channel="AFN",
            sales_channel="Amazon.de",
            order_total="49.99",
            currency="EUR",
            buyer_name="Max Mustermann",
            buyer_email="max@example.de",
            shipping_address={"City": "Berlin"},
            number_of_items=2
        )
        
        message = self.notifier.format_order_message(order)
        
        self.assertIn("🛒", message)
        self.assertIn("304-1234567-1234567", message)
        self.assertIn("49.99", message)
        self.assertIn("FBA", message)
        self.assertIn("Max Mustermann", message)
    
    def test_format_review_message_positive(self):
        """Test review formatting for positive review."""
        review = AmazonReview(
            asin="B08N5WRWNW",
            rating=5,
            title="Great product!",
            content="Very satisfied with this purchase.",
            reviewer_name="Happy Customer",
            review_date="2025-02-25T10:00:00Z",
            verified_purchase=True
        )
        
        message = self.notifier.format_review_message(review)
        
        self.assertIn("⭐", message)
        self.assertIn("B08N5WRWNW", message)
        self.assertIn("Great product!", message)
        self.assertNotIn("🚨", message)  # No warning for positive review
    
    def test_format_review_message_negative(self):
        """Test review formatting for negative review."""
        review = AmazonReview(
            asin="B08N5WRWNW",
            rating=1,
            title="Defective product",
            content="Product arrived broken.",
            reviewer_name="Angry Customer",
            review_date="2025-02-25T10:00:00Z",
            verified_purchase=True
        )
        
        message = self.notifier.format_review_message(review)
        
        self.assertIn("🚨", message)  # Warning for negative review
        self.assertIn("NEGATIVE BEWERTUNG", message)
    
    def test_format_inventory_alert_out_of_stock(self):
        """Test inventory alert formatting for out of stock."""
        alert = InventoryAlert(
            asin="B08N5WRWNW",
            sku="SKU-12345",
            title="Test Product",
            quantity=0,
            alert_type="out_of_stock"
        )
        
        message = self.notifier.format_inventory_alert(alert)
        
        self.assertIn("🔴", message)
        self.assertIn("B08N5WRWNW", message)
        self.assertIn("SKU-12345", message)
        self.assertIn("Sofort nachbestellen", message)


class TestSlackNotifier(unittest.TestCase):
    """Test Slack notifications."""
    
    def setUp(self):
        self.notifier = SlackNotifier("https://hooks.slack.com/test")
    
    @patch('amazon_seller_alerts.requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful Slack message."""
        mock_post.return_value = Mock(status_code=200)
        
        result = self.notifier.send_message("Test message")
        
        self.assertTrue(result)
    
    def test_send_order_notification(self):
        """Test order notification with blocks."""
        order = AmazonOrder(
            order_id="304-1234567-1234567",
            purchase_date="2025-02-25T14:30:00Z",
            status="Unshipped",
            fulfillment_channel="AFN",
            sales_channel="Amazon.de",
            order_total="49.99",
            currency="EUR",
            buyer_name="Max Mustermann",
            buyer_email="max@example.de",
            shipping_address={},
            number_of_items=2
        )
        
        # Mock send_message and verify it's called
        with patch.object(self.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            result = self.notifier.send_order_notification(order)
            
            self.assertTrue(result)
            self.assertTrue(mock_send.called)
            
            # Verify blocks were included (check call has 2 args: text and blocks)
            args, kwargs = mock_send.call_args
            has_blocks = len(args) >= 2 or 'blocks' in kwargs
            self.assertTrue(has_blocks, "Blocks should be passed to send_message")


class TestAmazonSellerAlerts(unittest.TestCase):
    """Test main AmazonSellerAlerts class."""
    
    @patch.dict(os.environ, {
        "AMAZON_LWA_CLIENT_ID": "test_id",
        "AMAZON_LWA_CLIENT_SECRET": "test_secret",
        "AMAZON_REFRESH_TOKEN": "test_token",
        "AMAZON_AWS_ACCESS_KEY": "test_key",
        "AMAZON_AWS_SECRET_KEY": "test_secret",
        "TELEGRAM_BOT_TOKEN": "test_tg_token",
        "TELEGRAM_CHAT_ID": "123456"
    })
    def setUp(self):
        # Create temp directory for state
        self.temp_dir = tempfile.mkdtemp()
        
        with patch('amazon_seller_alerts.os.makedirs'):
            self.alerts = AmazonSellerAlerts()
            self.alerts.state_dir = self.temp_dir
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_auth_missing_vars(self):
        """Test initialization fails with missing env vars."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                AmazonSellerAlerts()
            
            self.assertIn("Missing required environment variables", str(context.exception))
    
    def test_get_last_check_time_no_file(self):
        """Test getting last check time when no state file exists."""
        result = self.alerts._get_last_check_time("orders")
        self.assertIsNone(result)
    
    def test_save_and_get_last_check_time(self):
        """Test saving and retrieving last check time."""
        now = datetime.utcnow()
        
        self.alerts._save_last_check_time("orders", now)
        result = self.alerts._get_last_check_time("orders")
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.timestamp(), now.timestamp(), delta=1)
    
    @patch('amazon_seller_alerts.requests.get')
    def test_make_api_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"orders": []}
        mock_response.content = b'{"orders": []}'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Mock auth
        self.alerts.auth.get_headers = Mock(return_value={"Authorization": "Bearer test"})
        
        result = self.alerts._make_api_request("GET", "/test")
        
        self.assertEqual(result, {"orders": []})
    
    @patch('amazon_seller_alerts.requests.get')
    def test_check_orders_success(self, mock_get):
        """Test successful order check."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Orders": [
                {
                    "AmazonOrderId": "304-1234567-1234567",
                    "PurchaseDate": "2025-02-25T14:30:00Z",
                    "OrderStatus": "Unshipped",
                    "FulfillmentChannel": "AFN",
                    "SalesChannel": "Amazon.de",
                    "OrderTotal": {"Amount": "49.99", "CurrencyCode": "EUR"},
                    "BuyerInfo": {"BuyerName": "Max Mustermann"},
                    "NumberOfItemsShipped": 0,
                    "NumberOfItemsUnshipped": 2
                }
            ]
        }
        mock_response.content = json.dumps(mock_response.json.return_value).encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Mock auth and notifiers
        self.alerts.auth.get_headers = Mock(return_value={})
        self.alerts._notify_order = Mock()
        
        orders = self.alerts.check_orders()
        
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].order_id, "304-1234567-1234567")
        self.alerts._notify_order.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration-style tests."""
    
    def test_full_notification_flow(self):
        """Test complete notification flow."""
        # This is a simplified integration test
        order = AmazonOrder(
            order_id="TEST-123",
            purchase_date=datetime.utcnow().isoformat(),
            status="Unshipped",
            fulfillment_channel="AFN",
            sales_channel="Amazon.de",
            order_total="99.99",
            currency="EUR",
            buyer_name="Test Customer",
            buyer_email="test@example.com",
            shipping_address={},
            number_of_items=1
        )
        
        notifier = TelegramNotifier("token", "chat_id")
        message = notifier.format_order_message(order)
        
        # Verify message format
        self.assertIn("TEST-123", message)
        self.assertIn("99.99", message)
        self.assertIn("Test Customer", message)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSPAPIAuth))
    suite.addTests(loader.loadTestsFromTestCase(TestTelegramNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestSlackNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestAmazonSellerAlerts))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
