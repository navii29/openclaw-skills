"""
Unit Tests for Inbox AI Processor

Run with: python -m pytest test_inbox_processor.py -v
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from datetime import datetime

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inbox_processor_v2 import (
    EmailConfig, ProcessingResult, RateLimiter, 
    InboxProcessor, retry_on_error
)


class TestEmailConfig(unittest.TestCase):
    """Tests for EmailConfig dataclass"""
    
    def test_valid_config(self):
        """Test configuration validation with valid data"""
        config_dict = {
            'IMAP_SERVER': 'imap.example.com',
            'IMAP_PORT': '993',
            'SMTP_SERVER': 'smtp.example.com',
            'SMTP_PORT': '587',
            'EMAIL_USERNAME': 'test@example.com',
            'EMAIL_PASSWORD': 'secret',
            'FROM_NAME': 'Test User',
            'AUTO_REPLY_ENABLED': 'true',
            'ESCALATION_THRESHOLD': '0.8',
            'MAX_AUTO_REPLY_PER_HOUR': '10'
        }
        
        config = EmailConfig.from_dict(config_dict)
        
        self.assertEqual(config.imap_server, 'imap.example.com')
        self.assertEqual(config.imap_port, 993)
        self.assertEqual(config.email_username, 'test@example.com')
        self.assertEqual(config.escalation_threshold, 0.8)
        self.assertEqual(config.max_auto_reply_per_hour, 10)
        self.assertTrue(config.auto_reply_enabled)
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise ValueError"""
        config_dict = {
            'IMAP_SERVER': 'imap.example.com',
            # Missing SMTP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD
        }
        
        with self.assertRaises(ValueError) as context:
            EmailConfig.from_dict(config_dict)
        
        self.assertIn('Missing required', str(context.exception))
    
    def test_default_values(self):
        """Test default values for optional fields"""
        config_dict = {
            'IMAP_SERVER': 'imap.example.com',
            'SMTP_SERVER': 'smtp.example.com',
            'EMAIL_USERNAME': 'test@example.com',
            'EMAIL_PASSWORD': 'secret'
        }
        
        config = EmailConfig.from_dict(config_dict)
        
        self.assertEqual(config.from_name, 'Your Team')
        self.assertEqual(config.escalation_threshold, 0.7)
        self.assertEqual(config.max_auto_reply_per_hour, 20)
        self.assertTrue(config.auto_reply_enabled)


class TestRateLimiter(unittest.TestCase):
    """Tests for RateLimiter class"""
    
    def test_can_send_within_limit(self):
        """Test that sending is allowed within rate limit"""
        limiter = RateLimiter(max_per_hour=5)
        
        # Should be able to send 5 emails
        for _ in range(5):
            self.assertTrue(limiter.can_send())
            limiter.record_sent()
        
        # 6th email should be blocked
        self.assertFalse(limiter.can_send())
    
    def test_rate_limit_reset(self):
        """Test that old sends are cleared after an hour"""
        limiter = RateLimiter(max_per_hour=1)
        limiter.record_sent()
        
        self.assertFalse(limiter.can_send())
        
        # Simulate time passing
        limiter.sent_times[0] = datetime.now() - __import__('datetime').timedelta(hours=2)
        
        self.assertTrue(limiter.can_send())
    
    def test_wait_time(self):
        """Test wait time calculation"""
        limiter = RateLimiter(max_per_hour=10)
        self.assertEqual(limiter.wait_time(), 0)
        
        limiter.record_sent()
        wait = limiter.wait_time()
        self.assertGreaterEqual(wait, 0)
        self.assertLessEqual(wait, 3600)


class TestRetryOnError(unittest.TestCase):
    """Tests for retry decorator"""
    
    def test_success_no_retry(self):
        """Test that successful calls don't retry"""
        mock_func = Mock(return_value='success')
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 1)
    
    def test_retry_on_failure(self):
        """Test that failures trigger retries"""
        mock_func = Mock(side_effect=[Exception('error'), Exception('error'), 'success'])
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 3)
    
    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries"""
        mock_func = Mock(side_effect=Exception('persistent error'))
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        with self.assertRaises(Exception):
            test_func()
        
        self.assertEqual(mock_func.call_count, 3)


class TestInboxProcessor(unittest.TestCase):
    """Tests for InboxProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = EmailConfig(
            imap_server='imap.example.com',
            imap_port=993,
            smtp_server='smtp.example.com',
            smtp_port=587,
            email_username='test@example.com',
            email_password='secret',
            from_name='Test',
            max_auto_reply_per_hour=10
        )
        self.processor = InboxProcessor(self.config)
    
    def test_categorize_email_spam(self):
        """Test spam detection"""
        category, priority, escalate = self.processor.categorize_email(
            'Buy now!', 'Great offer', 'no-reply@spam.com'
        )
        
        self.assertEqual(category, 'spam')
        self.assertEqual(priority, 0.0)
        self.assertFalse(escalate)
    
    def test_categorize_email_booking(self):
        """Test booking category detection"""
        category, priority, escalate = self.processor.categorize_email(
            'Termin buchen', 'Ich möchte einen Termin vereinbaren', 'client@example.com'
        )
        
        self.assertEqual(category, 'booking')
        self.assertGreater(priority, 0)
    
    def test_categorize_email_urgent(self):
        """Test urgent email escalation"""
        category, priority, escalate = self.processor.categorize_email(
            'DRINGEND: Problem!', 'Wir haben ein dringendes Problem', 'client@example.com'
        )
        
        self.assertTrue(escalate)
        self.assertGreater(priority, 0.5)
    
    def test_categorize_email_complaint(self):
        """Test complaint escalation"""
        category, priority, escalate = self.processor.categorize_email(
            'Beschwerde', 'Ich bin sehr unzufrieden mit Ihrem Service', 'client@example.com'
        )
        
        self.assertTrue(escalate)
    
    def test_should_auto_reply_disabled(self):
        """Test auto-reply when disabled"""
        self.config.auto_reply_enabled = False
        
        should_reply, reason = self.processor.should_auto_reply('general', 0.5, False)
        
        self.assertFalse(should_reply)
        self.assertEqual(reason, 'auto_reply_disabled')
    
    def test_should_auto_reply_spam(self):
        """Test auto-reply blocked for spam"""
        should_reply, reason = self.processor.should_auto_reply('spam', 0.0, False)
        
        self.assertFalse(should_reply)
        self.assertEqual(reason, 'spam_detected')
    
    def test_should_auto_reply_high_priority(self):
        """Test auto-reply blocked for high priority"""
        should_reply, reason = self.processor.should_auto_reply('support', 0.9, False)
        
        self.assertFalse(should_reply)
        self.assertEqual(reason, 'high_priority')
    
    def test_generate_summary(self):
        """Test summary generation"""
        body = "Hello,\n\nThis is a test email.\n\nBest regards"
        summary = self.processor.generate_summary('Test Subject', body)
        
        self.assertIn('test', summary.lower())
        self.assertLessEqual(len(summary), 203)  # Max 200 chars + ...
    
    def test_generate_reply_templates(self):
        """Test reply template generation"""
        templates_to_test = ['booking', 'inquiry', 'support', 'general']
        
        for category in templates_to_test:
            reply = self.processor.generate_reply(category, 'Subject', 'Body')
            self.assertIn('vielen Dank', reply.lower())
            self.assertIn(self.config.from_name, reply)


class TestIntegration(unittest.TestCase):
    """Integration-style tests"""
    
    @patch('inbox_processor_v2.imaplib')
    def test_process_emails_mocked(self, mock_imaplib):
        """Test email processing with mocked IMAP"""
        config = EmailConfig(
            imap_server='imap.example.com',
            imap_port=993,
            smtp_server='smtp.example.com',
            smtp_port=587,
            email_username='test@example.com',
            email_password='secret'
        )
        processor = InboxProcessor(config)
        
        # Mock IMAP connection
        mock_conn = MagicMock()
        mock_imaplib.IMAP4_SSL.return_value = mock_conn
        mock_conn.search.return_value = ('OK', [b'1 2 3'])
        
        # Mock email fetch
        mock_email = b'Subject: Test\r\nFrom: sender@example.com\r\n\r\nTest body'
        mock_conn.fetch.return_value = ('OK', [(None, mock_email)])
        
        results = processor.process_emails(mode='monitor')
        
        self.assertEqual(len(results), 3)
        mock_conn.login.assert_called_once()


if __name__ == '__main__':
    unittest.main()
