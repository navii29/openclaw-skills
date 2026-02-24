"""
Unit Tests for A2A Market Client

Run with: python -m pytest test_a2a_client.py -v
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a2a_client_v2 import (
    A2AClient, CircuitBreaker, CircuitState, SpendingRules, Skill,
    retry_on_error
)


class TestCircuitBreaker(unittest.TestCase):
    """Tests for CircuitBreaker class"""
    
    def test_initial_state(self):
        """Test circuit starts closed"""
        cb = CircuitBreaker()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.can_execute())
    
    def test_failure_counting(self):
        """Test failure counting and circuit opening"""
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertFalse(cb.can_execute())
    
    def test_recovery(self):
        """Test circuit recovery after timeout"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        
        self.assertEqual(cb.state, CircuitState.OPEN)
        
        import time
        time.sleep(0.02)
        
        # Should allow execution in half-open state
        self.assertTrue(cb.can_execute())
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
    
    def test_success_reset(self):
        """Test success resets circuit"""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        
        cb.record_success()
        
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.failures, 0)


class TestSpendingRules(unittest.TestCase):
    """Tests for SpendingRules dataclass"""
    
    def test_default_values(self):
        """Test default spending rule values"""
        rules = SpendingRules()
        
        self.assertEqual(rules.max_per_transaction, 10.0)
        self.assertEqual(rules.daily_budget, 100.0)
        self.assertEqual(rules.min_seller_reputation, 60)
        self.assertEqual(rules.auto_approve_below, 5.0)
        self.assertEqual(rules.require_confirmation_above, 50.0)
    
    def test_custom_values(self):
        """Test custom spending rule values"""
        rules = SpendingRules(
            max_per_transaction=50.0,
            daily_budget=500.0,
            min_seller_reputation=80
        )
        
        self.assertEqual(rules.max_per_transaction, 50.0)
        self.assertEqual(rules.daily_budget, 500.0)
        self.assertEqual(rules.min_seller_reputation, 80)


class TestSkillDataclass(unittest.TestCase):
    """Tests for Skill dataclass"""
    
    def test_skill_creation(self):
        """Test skill object creation"""
        skill = Skill(
            id='skill_001',
            name='Test Skill',
            description='A test skill',
            price=10.0,
            seller='0x123',
            reputation=85,
            rating=4.5,
            sales=100
        )
        
        self.assertEqual(skill.id, 'skill_001')
        self.assertEqual(skill.name, 'Test Skill')
        self.assertEqual(skill.price, 10.0)


class TestRetryOnError(unittest.TestCase):
    """Tests for retry decorator"""
    
    def test_success_no_retry(self):
        """Test successful execution"""
        mock_func = Mock(return_value='success')
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 1)
    
    def test_retry_success(self):
        """Test retry leads to success"""
        mock_func = Mock(side_effect=[Exception('fail'), 'success'])
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 2)
    
    def test_max_retries_exceeded(self):
        """Test exception raised after max retries"""
        mock_func = Mock(side_effect=Exception('always fails'))
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            return mock_func()
        
        with self.assertRaises(Exception):
            test_func()
        
        self.assertEqual(mock_func.call_count, 3)


class TestA2AClient(unittest.TestCase):
    """Tests for A2AClient"""
    
    @patch('a2a_client_v2.Account.from_key')
    def setUp(self, mock_from_key):
        """Set up test client"""
        mock_account = MagicMock()
        mock_from_key.return_value = mock_account
        
        self.client = A2AClient(
            wallet_address='0x1234567890abcdef',
            private_key='0x' + 'a' * 64,
            api_url='https://api.test.com'
        )
    
    @patch('a2a_client_v2.Account.from_key')
    def test_invalid_private_key(self, mock_from_key):
        """Test invalid private key handling"""
        mock_from_key.side_effect = Exception('Invalid key')
        
        with self.assertRaises(ValueError) as context:
            A2AClient(
                wallet_address='0x123',
                private_key='invalid'
            )
        
        self.assertIn('invalid private key', str(context.exception).lower())
    
    def test_missing_credentials(self):
        """Test missing wallet/pkey raises error"""
        with self.assertRaises(ValueError):
            A2AClient(wallet_address='', private_key='')
    
    def test_check_budget_within_limits(self):
        """Test budget check within limits"""
        ok, msg = self.client._check_budget(5.0)
        
        self.assertTrue(ok)
        self.assertEqual(msg, 'OK')
    
    def test_check_budget_exceeds_max_transaction(self):
        """Test budget check exceeds max per transaction"""
        ok, msg = self.client._check_budget(50.0)
        
        self.assertFalse(ok)
        self.assertIn('exceeds max per transaction', msg)
    
    def test_check_budget_exceeds_daily(self):
        """Test budget check exceeds daily budget"""
        self.client.daily_spent = 95.0
        
        ok, msg = self.client._check_budget(10.0)
        
        self.assertFalse(ok)
        self.assertIn('daily budget', msg)
    
    def test_needs_confirmation(self):
        """Test confirmation requirement"""
        self.assertFalse(self.client._needs_confirmation(3.0))  # Below threshold
        self.assertTrue(self.client._needs_confirmation(10.0))  # Above threshold
    
    def test_agent_headers_without_id(self):
        """Test agent headers without agent ID"""
        self.client.agent_id = None
        
        with self.assertRaises(ValueError) as context:
            self.client._agent_headers()
        
        self.assertIn('agent id required', str(context.exception).lower())
    
    def test_agent_headers_with_id(self):
        """Test agent headers with agent ID"""
        self.client.agent_id = 'agent_123'
        
        headers = self.client._agent_headers()
        
        self.assertEqual(headers['x-agent-id'], 'agent_123')
    
    @patch('builtins.open', mock_open(read_data='agent_from_file'))
    @patch('os.path.exists')
    @patch('a2a_client_v2.Account.from_key')
    def test_load_agent_id_from_file(self, mock_from_key, mock_exists):
        """Test loading agent ID from file"""
        mock_exists.return_value = True
        mock_from_key.return_value = MagicMock()
        
        client = A2AClient(
            wallet_address='0x123',
            private_key='0x' + 'a' * 64
        )
        
        self.assertEqual(client.agent_id, 'agent_from_file')
    
    @patch('a2a_client_v2.requests.Session')
    def test_search_skills(self, mock_session_class):
        """Test skill search"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 'skill_001',
                    'name': 'Test Skill',
                    'description': 'A test',
                    'price': 10.0,
                    'seller': '0xabc',
                    'reputation': 80,
                    'rating': 4.5,
                    'sales': 50
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_session.request.return_value = mock_response
        
        skills = self.client.search('test query')
        
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, 'Test Skill')
        self.assertEqual(skills[0].price, 10.0)
    
    @patch('a2a_client_v2.requests.Session')
    def test_circuit_breaker_blocks_requests(self, mock_session_class):
        """Test circuit breaker blocks requests when open"""
        self.client.circuit_breaker.state = CircuitState.OPEN
        
        with self.assertRaises(Exception) as context:
            self.client._make_request('GET', '/test')
        
        self.assertIn('circuit breaker', str(context.exception).lower())
    
    def test_sign_request(self):
        """Test request signing"""
        self.client.account.sign_message = Mock()
        mock_signed = MagicMock()
        mock_signed.signature.hex.return_value = 'signed_data'
        self.client.account.sign_message.return_value = mock_signed
        
        headers = self.client._sign_request('GET', '/test', '')
        
        self.assertIn('X-Wallet-Address', headers)
        self.assertIn('X-Timestamp', headers)
        self.assertIn('X-Signature', headers)
        self.assertEqual(headers['X-Wallet-Address'], '0x1234567890abcdef')
    
    def test_list_skill_validation(self):
        """Test list skill validation"""
        self.client._make_request = Mock()
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'skill_123'}
        mock_response.raise_for_status.return_value = None
        self.client._make_request.return_value = mock_response
        
        # Valid
        result = self.client.list_skill(
            name='Test Skill',
            description='A test',
            price=10.0,
            category='analysis',
            content={'key': 'value'}
        )
        
        self.assertEqual(result['id'], 'skill_123')
    
    def test_list_skill_invalid_name(self):
        """Test list skill with invalid name"""
        with self.assertRaises(ValueError) as context:
            self.client.list_skill(
                name='AB',
                description='A test',
                price=10.0,
                category='analysis',
                content={}
            )
        
        self.assertIn('at least 3 characters', str(context.exception))
    
    def test_list_skill_invalid_price(self):
        """Test list skill with invalid price"""
        with self.assertRaises(ValueError) as context:
            self.client.list_skill(
                name='Test Skill',
                description='A test',
                price=-5.0,
                category='analysis',
                content={}
            )
        
        self.assertIn('must be positive', str(context.exception))
    
    def test_list_skill_missing_category(self):
        """Test list skill without category"""
        with self.assertRaises(ValueError) as context:
            self.client.list_skill(
                name='Test Skill',
                description='A test',
                price=10.0,
                category='',
                content={}
            )
        
        self.assertIn('category is required', str(context.exception))
    
    def test_get_skill_validation(self):
        """Test get skill with empty ID"""
        with self.assertRaises(ValueError) as context:
            self.client.get_skill('')
        
        self.assertIn('skill_id is required', str(context.exception))
    
    def test_purchase_with_credits_validation(self):
        """Test purchase with credits validation"""
        with self.assertRaises(ValueError) as context:
            self.client.purchase_with_credits('')
        
        self.assertIn('skill_id is required', str(context.exception))
    
    def test_register_validation(self):
        """Test register with invalid name"""
        with self.assertRaises(ValueError) as context:
            self.client.register('A')
        
        self.assertIn('at least 2 characters', str(context.exception))
    
    def test_get_stats(self):
        """Test get_stats returns expected data"""
        self.client.agent_id = 'agent_123'
        self.client.daily_spent = 25.0
        
        stats = self.client.get_stats()
        
        self.assertEqual(stats['daily_spent'], 25.0)
        self.assertEqual(stats['daily_budget'], 100.0)
        self.assertEqual(stats['agent_id'], 'agent_123')
        self.assertEqual(stats['circuit_state'], 'closed')


class TestA2AClientPurchases(unittest.TestCase):
    """Tests for purchase functionality"""
    
    @patch('a2a_client_v2.Account.from_key')
    def setUp(self, mock_from_key):
        """Set up test client"""
        mock_account = MagicMock()
        mock_from_key.return_value = mock_account
        
        self.client = A2AClient(
            wallet_address='0x123',
            private_key='0x' + 'a' * 64
        )
    
    @patch.object(A2AClient, 'get_skill')
    def test_purchase_low_reputation(self, mock_get_skill):
        """Test purchase blocked due to low seller reputation"""
        mock_get_skill.return_value = {
            'id': 'skill_001',
            'price': 5.0,
            'seller': {'reputation': 30},  # Below threshold of 60
            'name': 'Test',
            'description': '',
            'rating': 4.0,
            'sales': 10
        }
        
        with self.assertRaises(ValueError) as context:
            self.client.purchase('skill_001')
        
        self.assertIn('reputation', str(context.exception).lower())
    
    @patch.object(A2AClient, 'get_skill')
    def test_purchase_exceeds_budget(self, mock_get_skill):
        """Test purchase blocked due to budget"""
        mock_get_skill.return_value = {
            'id': 'skill_001',
            'price': 200.0,  # Exceeds max per transaction
            'seller': {'reputation': 80},
            'name': 'Test',
            'description': '',
            'rating': 4.0,
            'sales': 10
        }
        
        with self.assertRaises(ValueError) as context:
            self.client.purchase('skill_001')
        
        self.assertIn('exceeds max per transaction', str(context.exception))
    
    @patch.object(A2AClient, 'get_skill')
    def test_purchase_needs_confirmation(self, mock_get_skill):
        """Test purchase requires confirmation for expensive items"""
        mock_get_skill.return_value = {
            'id': 'skill_001',
            'price': 10.0,  # Above auto_approve_below of 5.0
            'seller': {'reputation': 80},
            'name': 'Test',
            'description': '',
            'rating': 4.0,
            'sales': 10
        }
        
        # Without callback, should raise
        with self.assertRaises(ValueError) as context:
            self.client.purchase('skill_001')
        
        self.assertIn('requires confirmation', str(context.exception).lower())
    
    @patch.object(A2AClient, 'get_skill')
    def test_purchase_confirmation_cancelled(self, mock_get_skill):
        """Test purchase cancelled by user"""
        mock_get_skill.return_value = {
            'id': 'skill_001',
            'price': 10.0,
            'seller': {'reputation': 80},
            'name': 'Test',
            'description': '',
            'rating': 4.0,
            'sales': 10
        }
        
        def cancel_callback(skill):
            return False
        
        with self.assertRaises(ValueError) as context:
            self.client.purchase('skill_001', confirm_callback=cancel_callback)
        
        self.assertIn('cancelled', str(context.exception).lower())


if __name__ == '__main__':
    unittest.main()
