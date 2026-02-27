"""
Tavily Search Client for OpenClaw
AI-optimized web search with structured LLM-ready results.

Usage:
    from tavily_client import TavilyClient
    client = TavilyClient()
    results = client.search("your query")
"""

import os
import sys
import json
import argparse
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

# Try to import requests, provide fallback
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error


class TavilyError(Exception):
    """Base exception for Tavily errors"""
    pass


class TavilyAuthError(TavilyError):
    """Invalid API key or authentication failed"""
    pass


class TavilyRateLimitError(TavilyError):
    """API rate limit exceeded"""
    pass


class TavilyTimeoutError(TavilyError):
    """Request timeout"""
    pass


class TavilySearchError(TavilyError):
    """Search query error"""
    pass


@dataclass
class SearchResult:
    """Single search result"""
    title: str
    url: str
    content: str
    score: float
    raw_content: Optional[str] = None
    published_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass  
class SearchResponse:
    """Complete search response"""
    query: str
    results: List[SearchResult]
    answer: Optional[str] = None
    response_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "response_time": self.response_time,
            "results": [r.to_dict() for r in self.results]
        }
    
    def to_markdown(self) -> str:
        """Convert results to markdown format"""
        lines = [f"# Search Results: {self.query}\n"]
        
        if self.answer:
            lines.append(f"## Summary\n\n{self.answer}\n")
        
        lines.append(f"## Sources ({len(self.results)} results)\n")
        
        for i, result in enumerate(self.results, 1):
            lines.append(f"### {i}. {result.title}")
            lines.append(f"**URL:** {result.url}")
            if result.published_date:
                lines.append(f"**Published:** {result.published_date}")
            lines.append(f"**Relevance:** {result.score:.2f}")
            lines.append(f"\n{result.content}\n")
            
            if result.raw_content:
                lines.append("<details>")
                lines.append("<summary>Full Content</summary>")
                lines.append(f"\n{result.raw_content[:2000]}...")
                lines.append("</details>")
                lines.append("")
        
        return "\n".join(lines)


class TavilyClient:
    """
    Tavily Search API Client
    
    Args:
        api_key: Tavily API key (or set TAVILY_API_KEY env var)
        base_url: API base URL (default: https://api.tavily.com)
    """
    
    BASE_URL = "https://api.tavily.com"
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise TavilyAuthError(
                "Tavily API key required. Set TAVILY_API_KEY env var or pass api_key. "
                "Get a key at https://tavily.com"
            )
        
        self.base_url = base_url or self.BASE_URL
        
        if not HAS_REQUESTS:
            print("Warning: 'requests' not installed. Using urllib fallback.", file=sys.stderr)
    
    def _request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = urljoin(self.base_url, endpoint)
        
        payload = {
            "api_key": self.api_key,
            **data
        }
        
        if HAS_REQUESTS:
            return self._request_requests(url, payload)
        else:
            return self._request_urllib(url, payload)
    
    def _request_requests(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make request using requests library"""
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 401:
                raise TavilyAuthError("Invalid API key. Check TAVILY_API_KEY.")
            elif response.status_code == 429:
                raise TavilyRateLimitError("Rate limit exceeded. Wait or upgrade plan.")
            elif response.status_code == 408:
                raise TavilyTimeoutError("Request timeout. Try reducing max_results.")
            elif response.status_code >= 400:
                raise TavilySearchError(f"API error {response.status_code}: {response.text}")
            
            return response.json()
            
        except requests.Timeout:
            raise TavilyTimeoutError("Request timeout after 60s")
        except requests.RequestException as e:
            raise TavilyError(f"Request failed: {e}")
    
    def _request_urllib(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback request using urllib"""
        try:
            data = json.dumps(payload).encode('utf-8')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            req = urllib.request.Request(
                url,
                data=data,
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise TavilyAuthError("Invalid API key. Check TAVILY_API_KEY.")
            elif e.code == 429:
                raise TavilyRateLimitError("Rate limit exceeded.")
            elif e.code == 408:
                raise TavilyTimeoutError("Request timeout.")
            else:
                raise TavilySearchError(f"API error {e.code}: {e.read().decode()}")
        except urllib.error.URLError as e:
            raise TavilyError(f"Request failed: {e}")
    
    def search(
        self,
        query: str,
        search_depth: str = "basic",
        include_answer: bool = False,
        include_raw_content: bool = False,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        Execute search query
        
        Args:
            query: Search query string
            search_depth: "basic" or "deep" (deep = more comprehensive)
            include_answer: Include AI-generated answer summary
            include_raw_content: Include full page content
            max_results: Number of results (1-20)
            include_domains: Restrict search to specific domains
            exclude_domains: Exclude specific domains
            
        Returns:
            SearchResponse with results and optional answer
        """
        if not query or not query.strip():
            raise TavilySearchError("Query cannot be empty")
        
        if max_results < 1 or max_results > 20:
            raise TavilySearchError("max_results must be between 1 and 20")
        
        valid_depths = ("basic", "advanced", "fast", "ultra-fast")
        if search_depth not in valid_depths:
            raise TavilySearchError(f"search_depth must be one of: {valid_depths}")
        
        data = {
            "query": query,
            "search_depth": search_depth,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "max_results": max_results
        }
        
        if include_domains:
            data["include_domains"] = include_domains
        if exclude_domains:
            data["exclude_domains"] = exclude_domains
        
        response = self._request("/search", data)
        
        # Parse results
        results = []
        for r in response.get("results", []):
            results.append(SearchResult(
                title=r.get("title", "Untitled"),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
                raw_content=r.get("raw_content"),
                published_date=r.get("published_date")
            ))
        
        return SearchResponse(
            query=query,
            results=results,
            answer=response.get("answer"),
            response_time=response.get("response_time")
        )
    
    def quick_search(self, query: str) -> List[Dict[str, str]]:
        """Quick search returning simplified results"""
        response = self.search(query, max_results=5)
        return [
            {"title": r.title, "url": r.url, "snippet": r.content[:200]}
            for r in response.results
        ]


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description="Tavily Search CLI")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--deep", "--advanced", action="store_true", help="Deep search mode (advanced)")
    parser.add_argument("--answer", action="store_true", help="Include AI answer")
    parser.add_argument("--raw", action="store_true", help="Include raw content")
    parser.add_argument("--max", type=int, default=5, help="Max results (1-20)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Save to file")
    
    args = parser.parse_args()
    
    try:
        client = TavilyClient()
        
        response = client.search(
            query=args.query,
            search_depth="advanced" if args.deep else "basic",
            include_answer=args.answer,
            include_raw_content=args.raw,
            max_results=args.max
        )
        
        if args.json:
            output = json.dumps(response.to_dict(), indent=2)
        else:
            output = response.to_markdown()
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Saved to {args.output}")
        else:
            print(output)
            
    except TavilyAuthError as e:
        print(f"Authentication error: {e}", file=sys.stderr)
        sys.exit(1)
    except TavilyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
