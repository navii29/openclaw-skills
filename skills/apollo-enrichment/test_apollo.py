#!/usr/bin/env python3
"""
Apollo.io Client Tests

Run with: python test_apollo.py
"""

import os
import sys
import json
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apollo_client import (
    ApolloClient,
    ApolloAuthError,
    ApolloRateLimitError,
    ApolloNotFoundError,
    ApolloValidationError
)


class TestApolloClient(unittest.TestCase):
    """Test suite for Apollo client"""
    
    def setUp(self):
        """Set up test fixtures"""
        os.environ['APOLLO_API_KEY'] = 'test_api_key'
    
    def test_init_with_api_key(self):
        """Test initialization with explicit API key"""
        client = ApolloClient(api_key="explicit_key")
        self.assertEqual(client.api_key, "explicit_key")
    
    def test_init_with_env_var(self):
        """Test initialization with environment variable"""
        client = ApolloClient()
        self.assertEqual(client.api_key, "test_api_key")
    
    def test_init_without_api_key(self):
        """Test initialization fails without API key"""
        del os.environ['APOLLO_API_KEY']
        with self.assertRaises(ApolloAuthError):
            ApolloClient()
    
    @patch('apollo_client.requests.Session.request')
    def test_enrich_person_success(self, mock_request):
        """Test successful person enrichment"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'person': {
                'first_name': 'John',
                'last_name': 'Doe',
                'title': 'CEO',
                'email': 'john@company.com',
                'organization': {
                    'name': 'Acme Inc',
                    'industry': 'Technology'
                }
            },
            'confidence_score': 0.95
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        result = client.enrich_person(email="john@company.com")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['data']['first_name'], 'John')
        self.assertEqual(result['credits_used'], 1)
    
    @patch('apollo_client.requests.Session.request')
    def test_enrich_person_not_found(self, mock_request):
        """Test person not found"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'person': None}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        result = client.enrich_person(email="notfound@example.com")
        
        self.assertEqual(result['status'], 'not_found')
        self.assertEqual(result['credits_used'], 0)
    
    @patch('apollo_client.requests.Session.request')
    def test_auth_error(self, mock_request):
        """Test authentication error handling"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        result = client.enrich_person(email="test@test.com")
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Invalid API key', result['error'])
    
    @patch('apollo_client.requests.Session.request')
    def test_search_people_success(self, mock_request):
        """Test successful people search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'people': [
                {
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'title': 'CTO',
                    'organization': {'name': 'TechCorp'}
                }
            ],
            'total_entries': 1,
            'pagination': {'total_pages': 1}
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        result = client.search_people(titles=["CTO"], limit=5)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['people']), 1)
        self.assertEqual(result['total_entries'], 1)
    
    @patch('apollo_client.requests.Session.request')
    def test_organization_enrichment(self, mock_request):
        """Test organization enrichment"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'organization': {
                'name': 'Stripe',
                'website_url': 'stripe.com',
                'estimated_num_employees': 5000,
                'industry': 'Financial Services'
            }
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        result = client.enrich_organization(domain="stripe.com")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['data']['name'], 'Stripe')
    
    @patch('apollo_client.requests.Session.request')
    def test_rate_limit_handling(self, mock_request):
        """Test rate limit error handling"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        result = client.enrich_person(email="test@test.com")
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Rate limit', result['error'])
    
    def test_no_identifiers_error(self):
        """Test error when no identifiers provided"""
        client = ApolloClient()
        result = client.enrich_person()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No identifiers', result['error'])


class TestIntegrationPatterns(unittest.TestCase):
    """Test integration patterns and use cases"""
    
    def setUp(self):
        os.environ['APOLLO_API_KEY'] = 'test_key'
    
    @patch('apollo_client.requests.Session.request')
    def test_lead_form_enrichment(self, mock_request):
        """Test lead form enrichment workflow"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'person': {
                'first_name': 'Sarah',
                'last_name': 'Chen',
                'title': 'VP of Engineering',
                'email': 'sarah@startup.io',
                'organization': {
                    'name': 'StartupIO',
                    'estimated_num_employees': 50,
                    'industry': 'Software'
                }
            }
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        
        # Simulate form submission
        form_data = {'email': 'sarah@startup.io', 'first_name': 'Sarah'}
        result = client.enrich_person(**form_data)
        
        # Verify enriched data structure
        self.assertEqual(result['status'], 'success')
        person = result['data']
        self.assertEqual(person['title'], 'VP of Engineering')
        self.assertEqual(person['organization']['name'], 'StartupIO')
    
    @patch('apollo_client.requests.Session.request')
    def test_crm_data_hygiene(self, mock_request):
        """Test CRM data cleanup workflow"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'person': {
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'title': 'Sales Director',
                'organization': {
                    'name': 'Enterprise Corp',
                    'industry': 'Consulting'
                }
            }
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = ApolloClient()
        
        # Simulate incomplete CRM record
        crm_record = {
            'email': 'mike@enterprise.com',
            'first_name': 'Mike',
            'company': None,
            'title': None
        }
        
        # Enrich
        result = client.enrich_person(email=crm_record['email'])
        
        if result['status'] == 'success':
            person = result['data']
            crm_record['company'] = crm_record.get('company') or person.get('organization', {}).get('name')
            crm_record['title'] = crm_record.get('title') or person.get('title')
        
        self.assertEqual(crm_record['company'], 'Enterprise Corp')
        self.assertEqual(crm_record['title'], 'Sales Director')


class TestCLIFunctionality(unittest.TestCase):
    """Test CLI argument parsing"""
    
    def setUp(self):
        os.environ['APOLLO_API_KEY'] = 'test_key'
    
    @patch('apollo_client.sys.argv', ['apollo_client.py', 'enrich', '--email', 'test@test.com'])
    @patch('apollo_client.ApolloClient.enrich_person')
    def test_cli_enrich_command(self, mock_enrich):
        """Test CLI enrich command"""
        mock_enrich.return_value = {'status': 'success', 'data': {}}
        
        # Import and run main
        from apollo_client import main
        
        try:
            main()
        except SystemExit:
            pass  # Expected
        
        mock_enrich.assert_called_once()


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestApolloClient))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIFunctionality))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
