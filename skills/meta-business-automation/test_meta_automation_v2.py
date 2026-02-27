#!/usr/bin/env python3
"""
Production Tests for Meta Business Automation v2.0

Tests cover:
- Circuit breaker pattern
- Rate limiting
- Retry logic with exponential backoff
- Error handling
- Edge cases
- API failures
"""

import os
import sys
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meta_automation_v2 import (
    MetaAutomation, CircuitBreaker, CircuitState,
    RateLimitInfo, PostResult
)


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern"""
    
    def setUp(self):
        self.cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
    
    def test_initial_state_closed(self):
        """Circuit starts closed"""
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
    
    def test_successful_call(self):
        """Successful call doesn't change state"""
        def success_func():
            return "success"
        
        result = self.cb.call(success_func)
        self.assertEqual(result, "success")
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
        self.assertEqual(self.cb.failure_count, 0)
    
    def test_failure_opens_circuit(self):
        """Multiple failures open circuit"""
        def fail_func():
            raise Exception("Test error")
        
        # First 3 failures should not open circuit
        for i in range(3):
            with self.assertRaises(Exception):
                self.cb.call(fail_func)
        
        # Circuit should be open now
        self.assertEqual(self.cb.state, CircuitState.OPEN)
        
        # Next call should fail immediately
        with self.assertRaises(Exception) as context:
            self.cb.call(fail_func)
        
        self.assertIn("OPEN", str(context.exception))
    
    def test_circuit_recovery(self):
        """Circuit recovers after timeout"""
        def fail_func():
            raise Exception("Test error")
        
        # Open circuit
        for _ in range(3):
            with self.assertRaises(Exception):
                self.cb.call(fail_func)
        
        self.assertEqual(self.cb.state, CircuitState.OPEN)
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Circuit should be half-open, next call will determine state
        def success_func():
            return "recovered"
        
        result = self.cb.call(success_func)
        self.assertEqual(result, "recovered")
        self.assertEqual(self.cb.state, CircuitState.CLOSED)


class TestMetaAutomationInit(unittest.TestCase):
    """Test MetaAutomation initialization"""
    
    @patch.dict(os.environ, {
        "META_ACCESS_TOKEN": "test_token",
        "INSTAGRAM_BUSINESS_ID": "ig_123",
        "FACEBOOK_PAGE_ID": "fb_123"
    })
    def test_init_success(self):
        """Successful initialization"""
        meta = MetaAutomation()
        self.assertEqual(meta.access_token, "test_token")
        self.assertEqual(meta.ig_business_id, "ig_123")
        self.assertEqual(meta.fb_page_id, "fb_123")
        self.assertEqual(meta.VERSION, "2.0.0")
    
    def test_init_missing_token(self):
        """Initialization fails without token"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                MetaAutomation()
            
            self.assertIn("META_ACCESS_TOKEN", str(context.exception))
    
    def test_init_custom_settings(self):
        """Initialization with custom settings"""
        with patch.dict(os.environ, {"META_ACCESS_TOKEN": "test"}):
            meta = MetaAutomation(
                max_retries=5,
                backoff_factor=2.0,
                request_timeout=60
            )
            self.assertEqual(meta.max_retries, 5)
            self.assertEqual(meta.backoff_factor, 2.0)
            self.assertEqual(meta.request_timeout, 60)


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality"""
    
    @patch.dict(os.environ, {"META_ACCESS_TOKEN": "test"})
    def setUp(self):
        self.meta = MetaAutomation()
    
    def test_rate_limit_tracking(self):
        """Rate limits are tracked from headers"""
        headers = {
            'x-app-usage': '{"call_count": 50}'
        }
        self.meta._update_rate_limits(headers)
        
        limits = self.meta.check_rate_limits()
        self.assertIn('app', limits)
        self.assertEqual(limits['app'].remaining, 50)
    
    def test_empty_headers(self):
        """Empty headers don't crash"""
        self.meta._update_rate_limits({})
        limits = self.meta.check_rate_limits()
        self.assertEqual(limits, {})


class TestInstagramPosting(unittest.TestCase):
    """Test Instagram posting with mocks"""
    
    @patch.dict(os.environ, {
        "META_ACCESS_TOKEN": "test_token",
        "INSTAGRAM_BUSINESS_ID": "ig_123"
    })
    def setUp(self):
        self.meta = MetaAutomation()
    
    @patch.object(MetaAutomation, '_make_request')
    def test_post_instagram_success(self, mock_request):
        """Successful Instagram post"""
        mock_request.side_effect = [
            {'id': 'container_123'},  # Create container
            {'id': 'post_123'}         # Publish
        ]
        
        result = self.meta.post_instagram_photo(
            "http://img.com/1.jpg",
            "Test caption"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.platform, "instagram")
        self.assertEqual(result.post_id, "post_123")
        self.assertEqual(result.retry_count, 0)
        self.assertEqual(mock_request.call_count, 2)
    
    @patch.object(MetaAutomation, '_make_request')
    def test_post_instagram_with_hashtags(self, mock_request):
        """Instagram post with hashtags"""
        mock_request.side_effect = [
            {'id': 'container_123'},
            {'id': 'post_123'}
        ]
        
        result = self.meta.post_instagram_photo(
            "http://img.com/1.jpg",
            "Test caption",
            hashtags=["marketing", "business"]
        )
        
        self.assertTrue(result.success)
        # Check that hashtags were appended
        call_args = mock_request.call_args_list[0]
        self.assertIn("#marketing", call_args[1]['data']['caption'])
    
    @patch.object(MetaAutomation, '_make_request')
    def test_post_instagram_retry_success(self, mock_request):
        """Instagram post succeeds after retry"""
        mock_request.side_effect = [
            Exception("Network error"),  # First attempt fails
            {'id': 'container_123'},      # Second attempt succeeds
            {'id': 'post_123'}
        ]
        
        result = self.meta.post_instagram_photo(
            "http://img.com/1.jpg",
            "Test caption"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.retry_count, 1)
        self.assertEqual(mock_request.call_count, 3)
    
    @patch.object(MetaAutomation, '_make_request')
    def test_post_instagram_all_retries_fail(self, mock_request):
        """Instagram post fails after all retries"""
        mock_request.side_effect = Exception("Persistent error")
        
        result = self.meta.post_instagram_photo(
            "http://img.com/1.jpg",
            "Test caption"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.retry_count, 3)
        self.assertIsNotNone(result.error)
    
    def test_post_instagram_no_business_id(self):
        """Fail gracefully without business ID"""
        with patch.dict(os.environ, {"META_ACCESS_TOKEN": "test"}, clear=True):
            meta = MetaAutomation()
            result = meta.post_instagram_photo(
                "http://img.com/1.jpg",
                "Test"
            )
            
            self.assertFalse(result.success)
            self.assertIn("BUSINESS_ID", result.error)


class TestFacebookPosting(unittest.TestCase):
    """Test Facebook posting"""
    
    @patch.dict(os.environ, {
        "META_ACCESS_TOKEN": "test_token",
        "FACEBOOK_PAGE_ID": "fb_123"
    })
    def setUp(self):
        self.meta = MetaAutomation()
    
    @patch.object(MetaAutomation, '_make_request')
    def test_post_facebook_success(self, mock_request):
        """Successful Facebook post"""
        mock_request.return_value = {'id': 'fb_post_123'}
        
        result = self.meta.post_facebook_photo(
            "http://img.com/1.jpg",
            "Test caption"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.platform, "facebook")
        self.assertEqual(result.post_id, "fb_post_123")
    
    @patch.object(MetaAutomation, '_make_request')
    def test_post_facebook_rate_limit(self, mock_request):
        """Handle rate limit error"""
        mock_request.side_effect = Exception("Rate limit exceeded")
        
        result = self.meta.post_facebook_photo(
            "http://img.com/1.jpg",
            "Test"
        )
        
        self.assertFalse(result.success)
        self.assertIn("Rate limit", result.error)
    
    def test_post_facebook_no_page_id(self):
        """Fail gracefully without page ID"""
        with patch.dict(os.environ, {"META_ACCESS_TOKEN": "test"}, clear=True):
            meta = MetaAutomation()
            result = meta.post_facebook_photo(
                "http://img.com/1.jpg",
                "Test"
            )
            
            self.assertFalse(result.success)
            self.assertIn("PAGE_ID", result.error)


class TestPostToBoth(unittest.TestCase):
    """Test posting to both platforms"""
    
    @patch.dict(os.environ, {
        "META_ACCESS_TOKEN": "test_token",
        "INSTAGRAM_BUSINESS_ID": "ig_123",
        "FACEBOOK_PAGE_ID": "fb_123"
    })
    def setUp(self):
        self.meta = MetaAutomation()
    
    @patch.object(MetaAutomation, 'post_instagram_photo')
    @patch.object(MetaAutomation, 'post_facebook_photo')
    def test_post_to_both_success(self, mock_fb, mock_ig):
        """Post to both platforms"""
        mock_ig.return_value = PostResult(
            success=True, platform="instagram",
            post_id="ig_123", error=None,
            retry_count=0, timestamp=datetime.now()
        )
        mock_fb.return_value = PostResult(
            success=True, platform="facebook",
            post_id="fb_123", error=None,
            retry_count=0, timestamp=datetime.now()
        )
        
        results = self.meta.post_to_both(
            "http://img.com/1.jpg",
            "Test caption"
        )
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
    
    @patch.object(MetaAutomation, 'post_instagram_photo')
    @patch.object(MetaAutomation, 'post_facebook_photo')
    def test_post_to_both_partial_failure(self, mock_fb, mock_ig):
        """One platform fails, other succeeds"""
        mock_ig.return_value = PostResult(
            success=True, platform="instagram",
            post_id="ig_123", error=None,
            retry_count=0, timestamp=datetime.now()
        )
        mock_fb.return_value = PostResult(
            success=False, platform="facebook",
            post_id=None, error="API Error",
            retry_count=3, timestamp=datetime.now()
        )
        
        results = self.meta.post_to_both(
            "http://img.com/1.jpg",
            "Test"
        )
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].success)  # Instagram
        self.assertFalse(results[1].success)  # Facebook


class TestAPIFailures(unittest.TestCase):
    """Test API failure scenarios"""
    
    @patch.dict(os.environ, {"META_ACCESS_TOKEN": "test"})
    def setUp(self):
        self.meta = MetaAutomation()
    
    @patch('meta_automation_v2.requests.Session')
    def test_api_error_response(self, mock_session):
        """Handle API error response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'error': {'code': 190, 'message': 'Access token expired'}
        }
        mock_response.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.meta._make_request("GET", "me")
        
        self.assertIn("Access token expired", str(context.exception))
    
    @patch('meta_automation_v2.requests.Session')
    def test_network_timeout(self, mock_session):
        """Handle network timeout"""
        from requests.exceptions import Timeout
        mock_session.return_value.get.side_effect = Timeout("Connection timeout")
        
        with self.assertRaises(Exception):
            self.meta._make_request("GET", "me")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases"""
    
    @patch.dict(os.environ, {"META_ACCESS_TOKEN": "test"})
    def setUp(self):
        self.meta = MetaAutomation()
    
    def test_empty_caption(self):
        """Handle empty caption"""
        with patch.object(self.meta, '_make_request') as mock_req:
            mock_req.side_effect = [
                {'id': 'container_123'},
                {'id': 'post_123'}
            ]
            
            result = self.meta.post_instagram_photo(
                "http://img.com/1.jpg",
                ""
            )
            
            self.assertTrue(result.success)
    
    def test_very_long_caption(self):
        """Handle very long caption"""
        long_caption = "A" * 10000
        
        with patch.object(self.meta, '_make_request') as mock_req:
            mock_req.side_effect = [
                {'id': 'container_123'},
                {'id': 'post_123'}
            ]
            
            result = self.meta.post_instagram_photo(
                "http://img.com/1.jpg",
                long_caption
            )
            
            self.assertTrue(result.success)
    
    def test_special_characters_in_caption(self):
        """Handle special characters"""
        special_caption = "Hello 🎉 @user #tag https://link.com"
        
        with patch.object(self.meta, '_make_request') as mock_req:
            mock_req.side_effect = [
                {'id': 'container_123'},
                {'id': 'post_123'}
            ]
            
            result = self.meta.post_instagram_photo(
                "http://img.com/1.jpg",
                special_caption
            )
            
            self.assertTrue(result.success)
            # Verify caption was passed correctly
            call_args = mock_req.call_args_list[0]
            self.assertEqual(call_args[1]['data']['caption'], special_caption)


def run_all_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCircuitBreaker))
    suite.addTests(loader.loadTestsFromTestCase(TestMetaAutomationInit))
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimiting))
    suite.addTests(loader.loadTestsFromTestCase(TestInstagramPosting))
    suite.addTests(loader.loadTestsFromTestCase(TestFacebookPosting))
    suite.addTests(loader.loadTestsFromTestCase(TestPostToBoth))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIFailures))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
