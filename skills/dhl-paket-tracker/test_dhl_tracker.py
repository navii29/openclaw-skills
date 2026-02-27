#!/usr/bin/env python3
"""
Test-Suite für DHL Paket Tracker
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Füge parent dir zum Path hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dhl_tracker import DHLTracker


class TestDHLTracker(unittest.TestCase):
    """Test cases für DHL Tracker"""
    
    def setUp(self):
        """Setup für jeden Test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_db.json")
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            "DHL_API_KEY": "test_key_123",
            "dhl-paket-tracker_BOT_TOKEN": "test_bot_token",
            "dhl-paket-tracker_CHAT_ID": "123456789"
        })
        self.env_patcher.start()
        
        # Patch DB file
        with patch('dhl_tracker.DB_FILE', self.db_file):
            self.tracker = DHLTracker()
    
    def tearDown(self):
        """Cleanup nach jedem Test"""
        self.env_patcher.stop()
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_translate_status(self):
        """Test Status-Übersetzung"""
        test_cases = [
            ("pre-transit", "📦 Sendung eingegangen"),
            ("transit", "🚚 In Transport"),
            ("delivered", "✅ Zugestellt"),
            ("failure", "⚠️ Zustellproblem"),
            ("unknown", "📋 unknown")
        ]
        
        for code, expected in test_cases:
            result = self.tracker._translate_status(code)
            self.assertEqual(result, expected, f"Failed for {code}")
    
    def test_format_location(self):
        """Test Standort-Formatierung"""
        # Mit Stadt und Land
        location = {"address": {"addressLocality": "Berlin", "countryCode": "DE"}}
        self.assertEqual(self.tracker._format_location(location), "Berlin, DE")
        
        # Nur Stadt
        location = {"address": {"addressLocality": "München"}}
        self.assertEqual(self.tracker._format_location(location), "München")
        
        # Leer
        self.assertEqual(self.tracker._format_location({}), "Unbekannt")
    
    def test_format_time(self):
        """Test Zeit-Formatierung"""
        # ISO Format
        result = self.tracker._format_time("2026-02-27T14:30:00Z")
        self.assertEqual(result, "27.02.2026 14:30")
        
        # Mit Offset
        result = self.tracker._format_time("2026-02-27T14:30:00+01:00")
        self.assertEqual(result, "27.02.2026 14:30")
        
        # Leer
        self.assertEqual(self.tracker._format_time(None), "Unbekannt")
    
    @patch('dhl_tracker.requests.get')
    def test_track_success(self, mock_get):
        """Test erfolgreiches Tracking"""
        # Mock Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "shipments": [{
                "id": "00340434161234567890",
                "status": {"status": "transit", "statusCode": "transit"},
                "events": [{
                    "timestamp": "2026-02-27T14:30:00Z",
                    "status": "transit",
                    "description": "Die Sendung wurde verladen",
                    "location": {"address": {"addressLocality": "Berlin", "countryCode": "DE"}}
                }],
                "estimatedTimeOfDelivery": "2026-02-28T18:00:00Z"
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.tracker.track("00340434161234567890")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["tracking_number"], "00340434161234567890")
        self.assertEqual(result["status"], "🚚 In Transport")
        self.assertEqual(result["location"], "Berlin, DE")
    
    @patch('dhl_tracker.requests.get')
    def test_track_no_shipment(self, mock_get):
        """Test Tracking ohne Ergebnis"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"shipments": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.tracker.track("00340434160000000000")
        self.assertIsNone(result)
    
    @patch('dhl_tracker.requests.get')
    def test_add_tracking(self, mock_get):
        """Test Hinzufügen zur Überwachung"""
        # Mock Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "shipments": [{
                "id": "00340434161234567890",
                "status": {"status": "pre-transit", "statusCode": "pre-transit"},
                "events": [{
                    "timestamp": "2026-02-27T10:00:00Z",
                    "status": "pre-transit",
                    "description": "Sendung eingegangen",
                    "location": {"address": {"addressLocality": "Hamburg", "countryCode": "DE"}}
                }]
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.tracker.add_tracking("00340434161234567890", "Test Paket")
        
        self.assertTrue(result)
        self.assertIn("00340434161234567890", self.tracker.db)
        self.assertEqual(self.tracker.db["00340434161234567890"]["description"], "Test Paket")
    
    def test_add_tracking_invalid(self):
        """Test ungültige Tracking-Nummer"""
        result = self.tracker.add_tracking("123")  # Zu kurz
        self.assertFalse(result)
        
        result = self.tracker.add_tracking("")  # Leer
        self.assertFalse(result)
    
    def test_remove_tracking(self):
        """Test Entfernen aus Überwachung"""
        # Zuerst hinzufügen
        self.tracker.db["00340434161234567890"] = {
            "description": "Test",
            "last_status": "transit"
        }
        self.tracker._save_db()
        
        # Dann entfernen
        result = self.tracker.remove("00340434161234567890")
        self.assertTrue(result)
        self.assertNotIn("00340434161234567890", self.tracker.db)
        
        # Nicht existierende Nummer
        result = self.tracker.remove("00340434160000000000")
        self.assertFalse(result)
    
    @patch('dhl_tracker.requests.post')
    @patch('dhl_tracker.requests.get')
    def test_check_all_with_changes(self, mock_get, mock_post):
        """Test Status-Change Detection"""
        # Setup: Paket in DB mit altem Status
        self.tracker.db["00340434161234567890"] = {
            "description": "Test Paket",
            "last_status": "📦 Sendung eingegangen",
            "last_check": "2026-02-27T10:00:00",
            "history": []
        }
        self.tracker._save_db()
        
        # Mock: Neuer Status
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "shipments": [{
                "id": "00340434161234567890",
                "status": {"status": "transit", "statusCode": "transit"},
                "events": [{
                    "timestamp": "2026-02-27T14:30:00Z",
                    "status": "transit",
                    "description": "In Zustellung",
                    "location": {"address": {"addressLocality": "Berlin", "countryCode": "DE"}}
                }]
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock Telegram
        mock_post.return_value = MagicMock(raise_for_status=MagicMock())
        
        # Check durchführen
        changes = self.tracker.check_all()
        
        # Assertions
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["old_status"], "📦 Sendung eingegangen")
        self.assertEqual(changes[0]["new_status"], "🚚 In Transport")
        
        # Telegram sollte aufgerufen worden sein
        mock_post.assert_called_once()


def run_tests():
    """Führe alle Tests aus"""
    # Lösche alte DB falls vorhanden
    test_db = "test_db.json"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDHLTracker)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
