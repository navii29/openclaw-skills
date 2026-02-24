"""
Unit Tests for SevDesk Client v2.1

Run with: python -m pytest test_sevdesk.py -v
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
import time
import tempfile
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sevdesk_v2 import (
    SevDeskClient, CircuitBreaker, CircuitState, SimpleCache,
    InvoiceStatus, ContactCategory, InvoiceType, VoucherStatus,
    validate_contact_data, validate_invoice_items, retry_on_error,
    ResponseMetadata
)


class TestInvoiceStatus(unittest.TestCase):
    """Tests for InvoiceStatus enum"""
    
    def test_status_values(self):
        """Test invoice status codes"""
        self.assertEqual(InvoiceStatus.DRAFT, 100)
        self.assertEqual(InvoiceStatus.OPEN, 200)
        self.assertEqual(InvoiceStatus.PARTIAL, 750)
        self.assertEqual(InvoiceStatus.PAID, 1000)
    
    def test_status_enum_access(self):
        """Test enum access patterns"""
        self.assertEqual(InvoiceStatus.DRAFT.value, 100)
        self.assertEqual(InvoiceStatus(100), InvoiceStatus.DRAFT)


class TestContactCategory(unittest.TestCase):
    """Tests for ContactCategory enum"""
    
    def test_category_values(self):
        """Test contact category codes"""
        self.assertEqual(ContactCategory.CUSTOMER, 3)
        self.assertEqual(ContactCategory.SUPPLIER, 4)
        self.assertEqual(ContactCategory.PARTNER, 5)


class TestInvoiceType(unittest.TestCase):
    """Tests for InvoiceType enum"""
    
    def test_type_values(self):
        """Test invoice type codes"""
        self.assertEqual(InvoiceType.INVOICE, "RE")
        self.assertEqual(InvoiceType.ADVANCE, "AR")
        self.assertEqual(InvoiceType.CREDIT, "GS")


class TestVoucherStatus(unittest.TestCase):
    """Tests for VoucherStatus enum"""
    
    def test_voucher_status_values(self):
        """Test voucher status codes"""
        self.assertEqual(VoucherStatus.DRAFT, 100)
        self.assertEqual(VoucherStatus.PAID, 1000)


class TestSimpleCache(unittest.TestCase):
    """Tests for SimpleCache class"""
    
    def setUp(self):
        self.cache = SimpleCache(default_ttl=60)
    
    def test_cache_miss(self):
        """Test cache miss returns None"""
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)
        self.assertEqual(self.cache._misses, 1)
    
    def test_cache_hit(self):
        """Test cache hit returns value"""
        self.cache.set("key", {"data": "value"})
        result = self.cache.get("key")
        self.assertEqual(result, {"data": "value"})
        self.assertEqual(self.cache._hits, 1)
    
    def test_cache_expiration(self):
        """Test cache entry expires after TTL"""
        cache = SimpleCache(default_ttl=0.01)  # Very short TTL
        self.cache.set("key", "value", ttl=0.01)
        time.sleep(0.02)
        result = self.cache.get("key")
        self.assertIsNone(result)
    
    def test_cache_clear(self):
        """Test cache clear removes all entries"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        self.assertEqual(self.cache.get("key1"), None)
        self.assertEqual(self.cache.get("key2"), None)
        self.assertEqual(len(self.cache._cache), 0)
    
    def test_cache_stats(self):
        """Test cache statistics"""
        self.cache.set("key", "value")
        self.cache.get("key")  # hit
        self.cache.get("other")  # miss
        
        stats = self.cache.get_stats()
        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate_percent"], 50.0)
    
    def test_custom_ttl(self):
        """Test custom TTL per key"""
        self.cache.set("key", "value", ttl=300)
        result = self.cache.get("key")
        self.assertEqual(result, "value")


class TestCircuitBreaker(unittest.TestCase):
    """Tests for CircuitBreaker class"""
    
    def test_initial_state(self):
        """Test circuit starts in CLOSED state"""
        cb = CircuitBreaker()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.can_execute())
    
    def test_open_after_failures(self):
        """Test circuit opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertFalse(cb.can_execute())
    
    def test_half_open_after_timeout(self):
        """Test circuit enters half-open after timeout"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        
        self.assertEqual(cb.state, CircuitState.OPEN)
        
        time.sleep(0.02)
        
        self.assertTrue(cb.can_execute())
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
    
    def test_close_on_success(self):
        """Test circuit closes on success"""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        
        cb.record_success()
        
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failures, 0)


class TestRetryOnError(unittest.TestCase):
    """Tests for retry decorator"""
    
    def test_success_no_retry(self):
        """Test successful call doesn't retry"""
        mock_func = Mock(return_value='success')
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 1)
    
    def test_retry_then_success(self):
        """Test retry leads to success"""
        mock_func = Mock(side_effect=[Exception('fail'), Exception('fail'), 'success'])
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 3)


class TestSevDeskClient(unittest.TestCase):
    """Tests for SevDeskClient"""
    
    @patch.dict(os.environ, {'SEVDESK_API_TOKEN': 'test_token_123'})
    def setUp(self):
        """Set up test client"""
        self.client = SevDeskClient(enable_cache=False)
    
    def test_missing_token(self):
        """Test that missing token raises error"""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Path, 'exists', return_value=False):
                with self.assertRaises(ValueError) as context:
                    SevDeskClient()
        
                self.assertIn('token required', str(context.exception).lower())
    
    def test_load_token_from_config(self):
        """Test loading token from config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'api_token': 'config_token_123'}, f)
            config_path = f.name
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                client = SevDeskClient(config_path=config_path)
                self.assertEqual(client.token, 'config_token_123')
        finally:
            os.unlink(config_path)
    
    def test_validate_contact_name_too_short(self):
        """Test contact name validation"""
        with self.assertRaises(ValueError) as context:
            self.client.create_contact('A')
        
        self.assertIn('at least 2 characters', str(context.exception))
    
    def test_validate_contact_invalid_email(self):
        """Test contact email validation"""
        with self.assertRaises(ValueError) as context:
            self.client.create_contact('Test Name', email='not-an-email')
        
        self.assertIn('invalid email', str(context.exception).lower())
    
    def test_validate_invoice_no_items(self):
        """Test invoice items validation - empty list"""
        with self.assertRaises(ValueError) as context:
            self.client.create_invoice('contact123', [])
        
        self.assertIn('non-empty list', str(context.exception))
    
    def test_validate_invoice_missing_name(self):
        """Test invoice item name validation"""
        with self.assertRaises(ValueError) as context:
            self.client.create_invoice('contact123', [{'price': 100}])
        
        self.assertIn('name is required', str(context.exception))
    
    def test_validate_invoice_invalid_price(self):
        """Test invoice item price validation"""
        with self.assertRaises(ValueError) as context:
            self.client.create_invoice('contact123', [{'name': 'Item', 'price': 'free'}])
        
        self.assertIn('must be a number', str(context.exception))
    
    def test_validate_invoice_negative_price(self):
        """Test invoice item negative price validation"""
        with self.assertRaises(ValueError) as context:
            self.client.create_invoice('contact123', [{'name': 'Item', 'price': -10}])
        
        self.assertIn('cannot be negative', str(context.exception))
    
    def test_validate_voucher_negative_amount(self):
        """Test voucher amount validation"""
        with self.assertRaises(ValueError) as context:
            self.client.create_voucher('supplier123', -50, 'Test voucher')
        
        self.assertIn('must be positive', str(context.exception))
    
    def test_validate_voucher_short_description(self):
        """Test voucher description validation"""
        with self.assertRaises(ValueError) as context:
            self.client.create_voucher('supplier123', 50, 'AB')
        
        self.assertIn('at least 3 characters', str(context.exception))
    
    @patch('sevdesk_v2.requests.request')
    def test_request_success(self, mock_request):
        """Test successful API request"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'objects': [{'id': '123'}]}
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = self.client._request('GET', '/Contact')
        
        self.assertEqual(result['objects'][0]['id'], '123')
        mock_request.assert_called_once()
    
    @patch('sevdesk_v2.requests.request')
    def test_request_with_caching(self, mock_request):
        """Test that caching works for GET requests"""
        client = SevDeskClient(enable_cache=True)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {'objects': [{'id': '123'}]}
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        # First request should hit API
        result1 = client._request('GET', '/Contact')
        self.assertEqual(mock_request.call_count, 1)
        
        # Second request should hit cache
        result2 = client._request('GET', '/Contact')
        self.assertEqual(mock_request.call_count, 1)  # No new request
        self.assertEqual(client._cached_request_count, 1)
    
    @patch('sevdesk_v2.requests.request')
    def test_request_401_error(self, mock_request):
        """Test 401 error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception('401 Unauthorized')
        mock_response.url = 'https://api.test/Contact'
        mock_request.return_value = mock_response
        
        result = self.client._request('GET', '/Contact')
        
        self.assertIn('error', result)
        self.assertIn('Invalid API token', result['error'])
    
    @patch('sevdesk_v2.requests.request')
    def test_request_404_error(self, mock_request):
        """Test 404 error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = 'https://api.test/Contact/999'
        mock_response.raise_for_status.side_effect = Exception('404 Not Found')
        mock_request.return_value = mock_response
        
        result = self.client._request('GET', '/Contact/999')
        
        self.assertIn('error', result)
        self.assertIn('not found', result['error'].lower())
    
    @patch('sevdesk_v2.requests.request')
    def test_circuit_breaker_opens(self, mock_request):
        """Test circuit breaker opens on repeated request failures"""
        # Simulate network errors (not HTTP errors which are caught and returned)
        mock_request.side_effect = requests.RequestException('Network error')
        
        # Make requests that fail
        for _ in range(6):
            try:
                self.client._request('GET', '/Contact')
            except Exception:
                pass
        
        self.assertEqual(self.client.circuit_breaker.state, CircuitState.OPEN)
        
        # Next request should be blocked
        with self.assertRaises(Exception) as context:
            self.client._request('GET', '/Contact')
        
        self.assertIn('circuit breaker', str(context.exception).lower())
    
    def test_parse_http_error_codes(self):
        """Test HTTP error parsing"""
        test_cases = [
            (400, 'Bad Request'),
            (401, 'Invalid API token'),
            (403, 'Access forbidden'),
            (404, 'not found'),
            (422, 'Validation error'),
            (429, 'Rate limit'),
            (500, 'server error'),
            (502, 'Bad Gateway'),
            (503, 'unavailable'),
            (418, '418')  # Unknown code
        ]
        
        for status, expected in test_cases:
            mock_response = MagicMock()
            mock_response.status_code = status
            mock_response.url = 'https://test.com'
            
            error_msg = self.client._parse_http_error(mock_response, Exception('test'))
            self.assertIn(expected.lower(), error_msg.lower())
    
    def test_format_invoice(self):
        """Test invoice formatting"""
        invoice = {
            'invoiceNumber': 'RE-2024-001',
            'contact': {'name': 'Test Customer'},
            'sumNet': 1000.00,
            'status': InvoiceStatus.DRAFT,
            'invoiceDate': '2024-01-15'
        }
        
        formatted = self.client.format_invoice(invoice)
        
        self.assertIn('RE-2024-001', formatted)
        self.assertIn('Test Customer', formatted)
        self.assertIn('1000.00', formatted)
    
    def test_format_contact(self):
        """Test contact formatting"""
        contact = {
            'name': 'Test Company',
            'id': '12345',
            'category': {'id': ContactCategory.CUSTOMER}
        }
        
        formatted = self.client.format_contact(contact)
        
        self.assertIn('Test Company', formatted)
        self.assertIn('Kunde', formatted)
        self.assertIn('12345', formatted)
    
    def test_get_stats(self):
        """Test stats collection"""
        stats = self.client.get_stats()
        
        self.assertIn('request_count', stats)
        self.assertIn('circuit_state', stats)
        self.assertIn('circuit_failures', stats)
    
    def test_get_unpaid_invoices(self):
        """Test unpaid invoices filtering"""
        with patch.object(self.client, 'list_invoices') as mock_list:
            mock_list.return_value = {
                'objects': [
                    {'id': '1', 'sumNet': 100, 'deliveryDate': '2024-01-01'},
                    {'id': '2', 'sumNet': 200, 'deliveryDate': '2024-02-01'},
                ]
            }
            
            # Without days filter
            result = self.client.get_unpaid_invoices()
            self.assertEqual(len(result), 2)
    
    def test_cache_key_generation(self):
        """Test cache key consistency"""
        key1 = self.client._get_cache_key('GET', '/Contact', {'limit': 10})
        key2 = self.client._get_cache_key('GET', '/Contact', {'limit': 10})
        self.assertEqual(key1, key2)
        
        # Different order should produce same key
        key3 = self.client._get_cache_key('GET', '/Contact', {'offset': 0, 'limit': 10})
        key4 = self.client._get_cache_key('GET', '/Contact', {'limit': 10, 'offset': 0})
        self.assertEqual(key3, key4)


class TestPagination(unittest.TestCase):
    """Tests for pagination functionality"""
    
    @patch.dict(os.environ, {'SEVDESK_API_TOKEN': 'test_token'})
    @patch('sevdesk_v2.requests.request')
    def test_get_all_pages(self, mock_request):
        """Test paginated fetching"""
        # Mock multiple pages
        responses = [
            MagicMock(
                json=lambda: {'objects': [{'id': i} for i in range(100)]},
                headers={},
                raise_for_status=lambda: None
            ),
            MagicMock(
                json=lambda: {'objects': [{'id': i} for i in range(100, 150)]},
                headers={},
                raise_for_status=lambda: None
            ),
        ]
        mock_request.side_effect = responses
        
        client = SevDeskClient(enable_cache=False)
        result = client._get_all_pages('/Contact', limit=150)
        
        self.assertEqual(len(result), 150)
        self.assertEqual(mock_request.call_count, 2)


class TestDecorators(unittest.TestCase):
    """Tests for validation decorators"""
    
    def test_validate_contact_decorator(self):
        """Test contact validation decorator"""
        class MockClient:
            @validate_contact_data
            def create_contact(self, name, email=None, **kwargs):
                return {'success': True}
        
        client = MockClient()
        
        # Valid
        result = client.create_contact('John Doe', 'john@example.com')
        self.assertTrue(result['success'])
        
        # Invalid - too short name
        with self.assertRaises(ValueError):
            client.create_contact('A')
        
        # Invalid - bad email
        with self.assertRaises(ValueError):
            client.create_contact('John', 'not-email')
    
    def test_validate_invoice_items_decorator(self):
        """Test invoice items validation decorator"""
        class MockClient:
            @validate_invoice_items
            def create_invoice(self, contact_id, items, **kwargs):
                return {'success': True}
        
        client = MockClient()
        
        # Valid
        result = client.create_invoice('contact123', [{'name': 'Item', 'price': 100}])
        self.assertTrue(result['success'])
        
        # Invalid - no contact
        with self.assertRaises(ValueError):
            client.create_invoice('', [{'name': 'Item', 'price': 100}])
        
        # Invalid - no items
        with self.assertRaises(ValueError):
            client.create_invoice('contact123', [])


class TestResponseMetadata(unittest.TestCase):
    """Tests for ResponseMetadata"""
    
    def test_metadata_creation(self):
        """Test ResponseMetadata dataclass"""
        meta = ResponseMetadata(
            request_count=10,
            cached=False,
            duration_ms=150.5,
            rate_limit_remaining=100,
            rate_limit_reset=3600
        )
        
        self.assertEqual(meta.request_count, 10)
        self.assertFalse(meta.cached)
        self.assertEqual(meta.duration_ms, 150.5)
        self.assertEqual(meta.rate_limit_remaining, 100)


class TestRateLimitExtraction(unittest.TestCase):
    """Tests for rate limit header extraction"""
    
    @patch.dict(os.environ, {'SEVDESK_API_TOKEN': 'test_token'})
    def test_extract_rate_limits(self):
        """Test rate limit extraction from headers"""
        client = SevDeskClient(enable_cache=False)
        
        mock_response = MagicMock()
        mock_response.headers = {
            'X-RateLimit-Remaining': '50',
            'X-RateLimit-Reset': '3600'
        }
        
        remaining, reset = client._extract_rate_limits(mock_response)
        self.assertEqual(remaining, 50)
        self.assertEqual(reset, 3600)
    
    @patch.dict(os.environ, {'SEVDESK_API_TOKEN': 'test_token'})
    def test_extract_rate_limits_missing(self):
        """Test rate limit extraction with missing headers"""
        client = SevDeskClient(enable_cache=False)
        
        mock_response = MagicMock()
        mock_response.headers = {}
        
        remaining, reset = client._extract_rate_limits(mock_response)
        self.assertIsNone(remaining)
        self.assertIsNone(reset)


if __name__ == '__main__':
    unittest.main()
