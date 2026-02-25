#!/usr/bin/env python3
"""Tests for Meta Business Automation"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meta_automation import MetaAutomation


class TestMetaAutomation(unittest.TestCase):
    """Test Meta automation."""
    
    @patch.dict(os.environ, {
        "META_ACCESS_TOKEN": "test_token",
        "INSTAGRAM_BUSINESS_ID": "ig_123",
        "FACEBOOK_PAGE_ID": "fb_123"
    })
    def setUp(self):
        self.meta = MetaAutomation()
    
    def test_init_missing_token(self):
        """Test initialization without token."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                MetaAutomation()
    
    @patch('meta_automation.requests.post')
    def test_post_instagram_photo(self, mock_post):
        """Test Instagram photo post."""
        # Mock responses for container creation and publish
        mock_post.side_effect = [
            Mock(json=lambda: {'id': 'container_123'}, raise_for_status=lambda: None),
            Mock(json=lambda: {'id': 'post_123'}, raise_for_status=lambda: None)
        ]
        
        result = self.meta.post_instagram_photo("http://img.com/1.jpg", "Test caption")
        
        self.assertEqual(result, "post_123")
        self.assertEqual(mock_post.call_count, 2)
    
    @patch('meta_automation.requests.post')
    def test_post_facebook_photo(self, mock_post):
        """Test Facebook photo post."""
        mock_post.return_value = Mock(
            json=lambda: {'id': 'fb_post_123'},
            raise_for_status=lambda: None
        )
        
        result = self.meta.post_facebook_photo("http://img.com/1.jpg", "Test caption")
        
        self.assertEqual(result, "fb_post_123")
    
    @patch('meta_automation.requests.post')
    def test_post_carousel(self, mock_post):
        """Test carousel post."""
        mock_post.side_effect = [
            Mock(json=lambda: {'id': 'child_1'}, raise_for_status=lambda: None),
            Mock(json=lambda: {'id': 'child_2'}, raise_for_status=lambda: None),
            Mock(json=lambda: {'id': 'carousel_container'}, raise_for_status=lambda: None),
            Mock(json=lambda: {'id': 'carousel_post'}, raise_for_status=lambda: None)
        ]
        
        result = self.meta.post_carousel(
            ["http://img.com/1.jpg", "http://img.com/2.jpg"],
            "Carousel caption"
        )
        
        self.assertEqual(result, "carousel_post")
        self.assertEqual(mock_post.call_count, 4)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestMetaAutomation))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
