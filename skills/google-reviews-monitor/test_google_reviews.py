#!/usr/bin/env python3
"""
Tests for Google Reviews Monitor
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, mock_open

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_reviews import (
    GoogleReviewsMonitor,
    GoogleReview,
    SentimentAnalysis,
    TelegramNotifier,
    SlackNotifier
)


class TestGoogleReview(unittest.TestCase):
    """Test GoogleReview dataclass."""
    
    def test_create_review(self):
        """Test review creation."""
        review = GoogleReview(
            review_id="abc123",
            place_id="ChIJ123",
            place_name="Test Restaurant",
            author_name="Max Mustermann",
            author_url="http://test.com",
            profile_photo_url="http://img.com/1.jpg",
            rating=5,
            text="Super Essen!",
            time=datetime(2025, 2, 25, 14, 30),
            relative_time="vor 2 Stunden",
            language="de",
            response_text=None,
            response_time=None
        )
        
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.place_name, "Test Restaurant")
        self.assertTrue(review.is_positive)
        self.assertFalse(review.is_negative)
    
    def test_sentiment_negative(self):
        """Test negative sentiment detection."""
        review = GoogleReview(
            review_id="1", place_id="ChIJ", place_name="Test",
            author_name="User", author_url=None, profile_photo_url=None,
            rating=1, text="Schlecht", time=datetime.now(),
            relative_time="Jetzt", language="de"
        )
        
        self.assertTrue(review.is_negative)
        self.assertFalse(review.is_neutral)
        self.assertFalse(review.is_positive)
    
    def test_sentiment_neutral(self):
        """Test neutral sentiment detection."""
        review = GoogleReview(
            review_id="1", place_id="ChIJ", place_name="Test",
            author_name="User", author_url=None, profile_photo_url=None,
            rating=3, text="OK", time=datetime.now(),
            relative_time="Jetzt", language="de"
        )
        
        self.assertFalse(review.is_negative)
        self.assertTrue(review.is_neutral)
        self.assertFalse(review.is_positive)
    
    def test_has_response(self):
        """Test response detection."""
        review_without = GoogleReview(
            review_id="1", place_id="ChIJ", place_name="Test",
            author_name="User", author_url=None, profile_photo_url=None,
            rating=3, text="OK", time=datetime.now(),
            relative_time="Jetzt", language="de",
            response_text=None
        )
        
        review_with = GoogleReview(
            review_id="2", place_id="ChIJ", place_name="Test",
            author_name="User", author_url=None, profile_photo_url=None,
            rating=3, text="OK", time=datetime.now(),
            relative_time="Jetzt", language="de",
            response_text="Danke!"
        )
        
        self.assertFalse(review_without.has_response)
        self.assertTrue(review_with.has_response)
    
    def test_to_dict(self):
        """Test serialization."""
        review = GoogleReview(
            review_id="1", place_id="ChIJ", place_name="Test",
            author_name="User", author_url=None, profile_photo_url=None,
            rating=5, text="Gut", time=datetime(2025, 2, 25, 14, 30),
            relative_time="Jetzt", language="de"
        )
        
        d = review.to_dict()
        self.assertEqual(d['rating'], 5)
        self.assertEqual(d['place_name'], "Test")


class TestTelegramNotifier(unittest.TestCase):
    """Test Telegram notifications."""
    
    def setUp(self):
        self.notifier = TelegramNotifier("test_token", "123456789")
    
    @patch('google_reviews.requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message send."""
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response
        
        result = self.notifier.send_message("Test")
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    def test_format_review_message_negative(self):
        """Test negative review formatting."""
        review = GoogleReview(
            review_id="1", place_id="ChIJ", place_name="Restaurant Berlin",
            author_name="Angry Customer", author_url=None, profile_photo_url=None,
            rating=1, text="Schrecklich! Nie wieder!", time=datetime.now(),
            relative_time="vor 1 Stunde", language="de",
            response_text=None
        )
        
        message = self.notifier.format_review_message(review)
        
        self.assertIn("🚨", message)
        self.assertIn("1 ⭐", message)
        self.assertIn("Restaurant Berlin", message)
        self.assertIn("Angry Customer", message)
        self.assertIn("⏳ Unbeantwortet", message)
    
    def test_format_review_message_positive(self):
        """Test positive review formatting."""
        review = GoogleReview(
            review_id="1", place_id="ChIJ", place_name="Café München",
            author_name="Happy Guest", author_url=None, profile_photo_url=None,
            rating=5, text="Super Service!", time=datetime.now(),
            relative_time="vor 2 Stunden", language="de",
            response_text="Danke!"
        )
        
        message = self.notifier.format_review_message(review)
        
        self.assertIn("✅", message)
        self.assertIn("5 ⭐", message)
        self.assertIn("✅ Beantwortet", message)


class TestSlackNotifier(unittest.TestCase):
    """Test Slack notifications."""
    
    def setUp(self):
        self.notifier = SlackNotifier("https://hooks.slack.com/test")
    
    @patch('google_reviews.requests.post')
    def test_send_review_notification(self, mock_post):
        """Test review notification."""
        mock_post.return_value = Mock(status_code=200)
        
        review = GoogleReview(
            review_id="1", place_id="ChIJ", place_name="Test Shop",
            author_name="Kunde", author_url=None, profile_photo_url=None,
            rating=2, text="Nicht gut", time=datetime.now(),
            relative_time="Jetzt", language="de"
        )
        
        result = self.notifier.send_review_notification(review)
        
        self.assertTrue(result)
        mock_post.assert_called_once()


class TestGoogleReviewsMonitor(unittest.TestCase):
    """Test main monitor functionality."""
    
    @patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test_key"})
    def setUp(self):
        with patch.object(GoogleReviewsMonitor, '_load_state'):
            self.monitor = GoogleReviewsMonitor()
            self.monitor.seen_reviews = {}
    
    def test_init_missing_api_key(self):
        """Test initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                GoogleReviewsMonitor()
            
            self.assertIn("API key required", str(context.exception))
    
    @patch('google_reviews.requests.get')
    def test_find_place_success(self, mock_get):
        """Test place search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "candidates": [
                {
                    "place_id": "ChIJ123",
                    "name": "Test Restaurant",
                    "formatted_address": "Berlin, Germany",
                    "rating": 4.5,
                    "user_ratings_total": 100
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = self.monitor.find_place("Test Restaurant Berlin")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Test Restaurant")
    
    @patch('google_reviews.requests.get')
    def test_get_reviews_success(self, mock_get):
        """Test fetching reviews."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "result": {
                "name": "Test Restaurant",
                "rating": 4.5,
                "reviews": [
                    {
                        "author_name": "Max M.",
                        "author_url": "http://test.com/1",
                        "rating": 5,
                        "text": "Super Essen!",
                        "time": 1708876800,
                        "relative_time_description": "vor 2 Wochen",
                        "language": "de"
                    }
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        reviews = self.monitor.get_reviews("ChIJ123")
        
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].author_name, "Max M.")
        self.assertEqual(reviews[0].rating, 5)
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis."""
        reviews = [
            GoogleReview(
                review_id="1", place_id="ChIJ", place_name="Test",
                author_name="A", author_url=None, profile_photo_url=None,
                rating=5, text="Super gut", time=datetime.now(),
                relative_time="Jetzt", language="de"
            ),
            GoogleReview(
                review_id="2", place_id="ChIJ", place_name="Test",
                author_name="B", author_url=None, profile_photo_url=None,
                rating=5, text="Sehr guter Service", time=datetime.now(),
                relative_time="Jetzt", language="de"
            ),
            GoogleReview(
                review_id="3", place_id="ChIJ", place_name="Test",
                author_name="C", author_url=None, profile_photo_url=None,
                rating=3, text="OK", time=datetime.now(),
                relative_time="Jetzt", language="de"
            ),
            GoogleReview(
                review_id="4", place_id="ChIJ", place_name="Test",
                author_name="D", author_url=None, profile_photo_url=None,
                rating=1, text="Schlecht", time=datetime.now(),
                relative_time="Jetzt", language="de"
            )
        ]
        
        analysis = self.monitor.analyze_sentiment(reviews)
        
        self.assertEqual(analysis.total_reviews, 4)
        self.assertEqual(analysis.positive_count, 2)
        self.assertEqual(analysis.neutral_count, 1)
        self.assertEqual(analysis.negative_count, 1)
        self.assertEqual(analysis.average_rating, 3.5)
        self.assertEqual(analysis.positive_percent, 50.0)
    
    def test_analyze_sentiment_empty(self):
        """Test sentiment analysis with no reviews."""
        analysis = self.monitor.analyze_sentiment([])
        
        self.assertEqual(analysis.total_reviews, 0)
        self.assertEqual(analysis.average_rating, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_workflow_simulation(self):
        """Simulate full monitoring workflow."""
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test_key"}):
            with patch.object(GoogleReviewsMonitor, '_load_state'):
                monitor = GoogleReviewsMonitor()
                monitor.seen_reviews = {"ChIJ123": set()}
                
                # Create test reviews
                reviews = [
                    GoogleReview(
                        review_id="r1", place_id="ChIJ123", place_name="Test",
                        author_name="User1", author_url=None, profile_photo_url=None,
                        rating=5, text="Gut", time=datetime.now(),
                        relative_time="Jetzt", language="de"
                    ),
                    GoogleReview(
                        review_id="r2", place_id="ChIJ123", place_name="Test",
                        author_name="User2", author_url=None, profile_photo_url=None,
                        rating=1, text="Schlecht", time=datetime.now(),
                        relative_time="Jetzt", language="de"
                    )
                ]
                
                # Simulate checking
                monitor.get_reviews = Mock(return_value=reviews)
                monitor._notify_new_review = Mock()
                monitor._save_state = Mock()
                
                new_reviews = monitor.check_for_new_reviews(
                    place_id="ChIJ123",
                    min_stars=1,
                    max_stars=5,
                    notify=True
                )
                
                self.assertEqual(len(new_reviews), 2)
                self.assertEqual(len(monitor._notify_new_review.mock_calls), 2)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestGoogleReview))
    suite.addTests(loader.loadTestsFromTestCase(TestTelegramNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestSlackNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestGoogleReviewsMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
