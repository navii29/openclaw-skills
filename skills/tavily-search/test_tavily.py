"""
Tests for Tavily Search Client
Run: python -m pytest test_tavily.py -v
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the client
from tavily_client import (
    TavilyClient,
    SearchResult,
    SearchResponse,
    TavilyError,
    TavilyAuthError,
    TavilyRateLimitError,
    TavilyTimeoutError,
    TavilySearchError
)


class TestSearchResult:
    def test_search_result_creation(self):
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            content="Test content",
            score=0.95,
            published_date="2024-01-15"
        )
        
        assert result.title == "Test Title"
        assert result.score == 0.95
        assert result.to_dict()["title"] == "Test Title"


class TestSearchResponse:
    def test_search_response_to_markdown(self):
        results = [
            SearchResult(
                title="Result 1",
                url="https://example.com/1",
                content="Content 1",
                score=0.9
            ),
            SearchResult(
                title="Result 2",
                url="https://example.com/2",
                content="Content 2",
                score=0.8
            )
        ]
        
        response = SearchResponse(
            query="test query",
            results=results,
            answer="Test summary"
        )
        
        markdown = response.to_markdown()
        
        assert "# Search Results: test query" in markdown
        assert "## Summary" in markdown
        assert "Test summary" in markdown
        assert "Result 1" in markdown
        assert "Result 2" in markdown


class TestTavilyClient:
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_client_initialization_with_env(self):
        client = TavilyClient()
        assert client.api_key == "test-key"
    
    def test_client_initialization_with_key(self):
        client = TavilyClient(api_key="explicit-key")
        assert client.api_key == "explicit-key"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_client_initialization_without_key_raises(self):
        with pytest.raises(TavilyAuthError):
            TavilyClient()
    
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_search_validation_empty_query(self):
        client = TavilyClient()
        
        with pytest.raises(TavilySearchError, match="empty"):
            client.search("")
        
        with pytest.raises(TavilySearchError, match="empty"):
            client.search("   ")
    
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_search_validation_max_results(self):
        client = TavilyClient()
        
        with pytest.raises(TavilySearchError):
            client.search("test", max_results=0)
        
        with pytest.raises(TavilySearchError):
            client.search("test", max_results=25)
    
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_search_validation_search_depth(self):
        client = TavilyClient()
        
        with pytest.raises(TavilySearchError):
            client.search("test", search_depth="invalid")
    
    @patch("tavily_client.requests.post")
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_search_success(self, mock_post):
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": "test query",
            "answer": "Test answer",
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "content": "Test content",
                    "score": 0.95,
                    "published_date": "2024-01-15"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        client = TavilyClient()
        result = client.search("test query", include_answer=True)
        
        assert result.query == "test query"
        assert result.answer == "Test answer"
        assert len(result.results) == 1
        assert result.results[0].title == "Test Result"
    
    @patch("tavily_client.requests.post")
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_search_auth_error(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        client = TavilyClient()
        
        with pytest.raises(TavilyAuthError):
            client.search("test")
    
    @patch("tavily_client.requests.post")
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_search_rate_limit(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"
        mock_post.return_value = mock_response
        
        client = TavilyClient()
        
        with pytest.raises(TavilyRateLimitError):
            client.search("test")
    
    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    def test_quick_search(self):
        with patch.object(TavilyClient, 'search') as mock_search:
            mock_search.return_value = SearchResponse(
                query="test",
                results=[
                    SearchResult(
                        title="Result 1",
                        url="https://example.com",
                        content="This is a long content string that should be truncated",
                        score=0.9
                    )
                ]
            )
            
            client = TavilyClient()
            results = client.quick_search("test")
            
            assert len(results) == 1
            assert results[0]["title"] == "Result 1"
            assert results[0]["snippet"] == "This is a long content string that should be trunc"


class TestCLI:
    @patch("tavily_client.TavilyClient")
    @patch("sys.argv", ["tavily_client.py", "test query"])
    def test_cli_basic(self, mock_client_class):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.to_markdown.return_value = "# Results"
        mock_response.to_dict.return_value = {"query": "test"}
        mock_client.search.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        from tavily_client import main
        # Note: In real test, you'd capture stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
