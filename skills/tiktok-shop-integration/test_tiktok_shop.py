#!/usr/bin/env python3
"""Tests for TikTok Shop Integration"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tiktok_shop import TikTokShopAPI, TikTokProduct


class TestTikTokShopAPI(unittest.TestCase):
    """Test TikTok Shop API."""
    
    @patch.dict(os.environ, {
        "TIKTOK_APP_KEY": "test_key",
        "TIKTOK_APP_SECRET": "test_secret",
        "TIKTOK_SHOP_ID": "shop_123",
        "TIKTOK_ACCESS_TOKEN": "token_123"
    })
    def setUp(self):
        self.api = TikTokShopAPI()
    
    def test_init_missing_credentials(self):
        """Test initialization without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                TikTokShopAPI()
    
    def test_generate_signature(self):
        """Test signature generation."""
        params = {'a': '1', 'b': '2'}
        sig = self.api._generate_signature(params)
        
        self.assertEqual(len(sig), 64)  # SHA256 hex length
    
    @patch('tiktok_shop.requests.get')
    def test_get_products(self, mock_get):
        """Test fetching products."""
        mock_get.return_value = Mock(
            json=lambda: {
                'code': 0,
                'data': {
                    'products': [
                        {'id': 'p1', 'name': 'Product 1'},
                        {'id': 'p2', 'name': 'Product 2'}
                    ]
                }
            },
            raise_for_status=lambda: None
        )
        
        products = self.api.get_products()
        
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]['name'], 'Product 1')
    
    @patch('tiktok_shop.requests.post')
    def test_create_product(self, mock_post):
        """Test product creation."""
        mock_post.return_value = Mock(
            json=lambda: {'code': 0, 'data': {'product_id': 'new_123'}},
            raise_for_status=lambda: None
        )
        
        product = TikTokProduct(
            sku="SKU001",
            name="Test Product",
            description="Description",
            price=29.99,
            stock=100,
            category_id="cat_1",
            images=["http://img.com/1.jpg"]
        )
        
        result = self.api.create_product(product)
        
        self.assertEqual(result, "new_123")
    
    @patch('tiktok_shop.requests.post')
    def test_update_inventory(self, mock_post):
        """Test inventory update."""
        mock_post.return_value = Mock(
            json=lambda: {'code': 0, 'data': {}},
            raise_for_status=lambda: None
        )
        
        result = self.api.update_inventory("SKU001", 50)
        
        self.assertTrue(result)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestTikTokShopAPI))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
