#!/usr/bin/env python3
"""
Meta Business Suite Automation v2.0
Production-ready Instagram and Facebook posting via Meta Graph API.

Features:
- Retry logic with exponential backoff
- Rate limiting protection
- Circuit breaker pattern
- Comprehensive error handling
- Batch posting
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    limit: int
    remaining: int
    reset_time: datetime


@dataclass
class PostResult:
    """Result of a post operation"""
    success: bool
    platform: str
    post_id: Optional[str]
    error: Optional[str]
    retry_count: int
    timestamp: datetime


class CircuitBreaker:
    """Circuit breaker for API calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset"""
        if not self.last_failure_time:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")


class MetaAutomation:
    """
    Production-ready Meta Graph API automation.
    
    Features:
    - Automatic retries with exponential backoff
    - Circuit breaker for resilience
    - Rate limit tracking
    - Comprehensive logging
    """
    
    VERSION = "2.0.0"
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        request_timeout: int = 30
    ):
        """
        Initialize Meta Automation.
        
        Args:
            access_token: Meta Graph API access token
            max_retries: Maximum retry attempts
            backoff_factor: Exponential backoff factor
            request_timeout: Request timeout in seconds
        """
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("META_ACCESS_TOKEN environment variable required")
        
        self.ig_business_id = os.getenv("INSTAGRAM_BUSINESS_ID")
        self.fb_page_id = os.getenv("FACEBOOK_PAGE_ID")
        
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.request_timeout = request_timeout
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker()
        
        # Rate limit tracking
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        
        # Session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"✅ Meta Automation v{self.VERSION} initialized")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict:
        """
        Make API request with retries and circuit breaker.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: POST data
            files: Files to upload
            
        Returns:
            API response as dict
            
        Raises:
            Exception: If request fails after all retries
        """
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params['access_token'] = self.access_token
        
        def _execute_request():
            try:
                if method == "GET":
                    response = self.session.get(
                        url,
                        params=params,
                        timeout=self.request_timeout
                    )
                elif method == "POST":
                    if files:
                        response = self.session.post(
                            url,
                            params=params,
                            data=data,
                            files=files,
                            timeout=self.request_timeout
                        )
                    else:
                        response = self.session.post(
                            url,
                            params=params,
                            data=data,
                            timeout=self.request_timeout
                        )
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                # Track rate limits
                self._update_rate_limits(response.headers)
                
                # Check for HTTP errors
                response.raise_for_status()
                
                result = response.json()
                
                # Check for API errors
                if 'error' in result:
                    error_code = result['error'].get('code', 0)
                    error_message = result['error'].get('message', 'Unknown error')
                    
                    # Handle specific error codes
                    if error_code == 4:  # Rate limit
                        raise Exception(f"Rate limit exceeded: {error_message}")
                    elif error_code == 190:  # Access token expired
                        raise Exception(f"Access token expired: {error_message}")
                    else:
                        raise Exception(f"API Error {error_code}: {error_message}")
                
                return result
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                raise
        
        # Execute with circuit breaker
        return self.circuit_breaker.call(_execute_request)
    
    def _update_rate_limits(self, headers: Dict):
        """Update rate limit tracking from response headers"""
        if 'x-app-usage' in headers:
            try:
                usage = json.loads(headers['x-app-usage'])
                self.rate_limits['app'] = RateLimitInfo(
                    limit=100,  # Default
                    remaining=100 - usage.get('call_count', 0),
                    reset_time=datetime.now() + timedelta(hours=1)
                )
            except:
                pass
    
    def check_rate_limits(self) -> Dict[str, RateLimitInfo]:
        """Get current rate limit status"""
        return self.rate_limits
    
    def upload_image(self, image_path: str) -> str:
        """
        Upload image and get public URL.
        
        Args:
            image_path: Path to local image file
            
        Returns:
            Public URL of uploaded image
        """
        # In production, implement actual image upload
        # For now, assume image is already hosted
        if image_path.startswith('http'):
            return image_path
        
        # TODO: Implement actual upload to CDN
        logger.warning(f"Local image not uploaded: {image_path}")
        return image_path
    
    def post_instagram_photo(
        self,
        image_url: str,
        caption: str,
        hashtags: Optional[List[str]] = None
    ) -> PostResult:
        """
        Post photo to Instagram with retry logic.
        
        Args:
            image_url: URL of image to post
            caption: Post caption
            hashtags: Optional hashtags to append
            
        Returns:
            PostResult with success status and post ID
        """
        if not self.ig_business_id:
            return PostResult(
                success=False,
                platform="instagram",
                post_id=None,
                error="INSTAGRAM_BUSINESS_ID not configured",
                retry_count=0,
                timestamp=datetime.now()
            )
        
        # Add hashtags if provided
        if hashtags:
            hashtag_str = ' '.join([f"#{tag}" for tag in hashtags])
            caption = f"{caption}\n\n{hashtag_str}"
        
        logger.info(f"📸 Posting to Instagram: {caption[:50]}...")
        
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                # Step 1: Create media container
                container_data = {
                    'image_url': image_url,
                    'caption': caption,
                }
                
                result = self._make_request(
                    "POST",
                    f"{self.ig_business_id}/media",
                    data=container_data
                )
                
                creation_id = result.get('id')
                if not creation_id:
                    raise Exception("No creation ID received")
                
                # Step 2: Publish container
                publish_result = self._make_request(
                    "POST",
                    f"{self.ig_business_id}/media_publish",
                    data={'creation_id': creation_id}
                )
                
                post_id = publish_result.get('id')
                logger.info(f"✅ Posted to Instagram: {post_id}")
                
                return PostResult(
                    success=True,
                    platform="instagram",
                    post_id=post_id,
                    error=None,
                    retry_count=retry_count,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                retry_count += 1
                last_error = str(e)
                logger.warning(f"⚠️  Attempt {retry_count} failed: {e}")
                
                if retry_count < self.max_retries:
                    wait_time = self.backoff_factor * (2 ** retry_count)
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        # All retries exhausted
        logger.error(f"❌ Failed to post after {retry_count} attempts")
        return PostResult(
            success=False,
            platform="instagram",
            post_id=None,
            error=last_error,
            retry_count=retry_count,
            timestamp=datetime.now()
        )
    
    def post_facebook_photo(
        self,
        image_url: str,
        caption: str
    ) -> PostResult:
        """Post photo to Facebook Page with retry logic."""
        if not self.fb_page_id:
            return PostResult(
                success=False,
                platform="facebook",
                post_id=None,
                error="FACEBOOK_PAGE_ID not configured",
                retry_count=0,
                timestamp=datetime.now()
            )
        
        logger.info(f"📘 Posting to Facebook: {caption[:50]}...")
        
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                params = {
                    'url': image_url,
                    'caption': caption,
                    'access_token': self.access_token
                }
                
                result = self._make_request(
                    "POST",
                    f"{self.fb_page_id}/photos",
                    params=params
                )
                
                post_id = result.get('id')
                logger.info(f"✅ Posted to Facebook: {post_id}")
                
                return PostResult(
                    success=True,
                    platform="facebook",
                    post_id=post_id,
                    error=None,
                    retry_count=retry_count,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                retry_count += 1
                last_error = str(e)
                logger.warning(f"⚠️  Attempt {retry_count} failed: {e}")
                
                if retry_count < self.max_retries:
                    wait_time = self.backoff_factor * (2 ** retry_count)
                    time.sleep(wait_time)
        
        return PostResult(
            success=False,
            platform="facebook",
            post_id=None,
            error=last_error,
            retry_count=retry_count,
            timestamp=datetime.now()
        )
    
    def post_to_both(
        self,
        image_url: str,
        caption: str,
        hashtags: Optional[List[str]] = None
    ) -> List[PostResult]:
        """
        Post to both Instagram and Facebook.
        
        Args:
            image_url: Image URL
            caption: Post caption
            hashtags: Optional hashtags
            
        Returns:
            List of PostResults
        """
        results = []
        
        # Instagram
        if self.ig_business_id:
            ig_result = self.post_instagram_photo(image_url, caption, hashtags)
            results.append(ig_result)
        
        # Facebook
        if self.fb_page_id:
            fb_result = self.post_facebook_photo(image_url, caption)
            results.append(fb_result)
        
        return results
    
    def get_account_info(self) -> Dict:
        """Get account information and limits."""
        try:
            result = self._make_request("GET", "me")
            return {
                'success': True,
                'account_id': result.get('id'),
                'name': result.get('name'),
                'rate_limits': self.check_rate_limits()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description='Meta Business Automation v2.0')
    parser.add_argument('--image', '-i', required=True, help='Image URL')
    parser.add_argument('--caption', '-c', required=True, help='Post caption')
    parser.add_argument('--platform', choices=['instagram', 'facebook', 'both'], default='both')
    parser.add_argument('--hashtags', help='Comma-separated hashtags')
    
    args = parser.parse_args()
    
    try:
        meta = MetaAutomation()
        
        hashtags = args.hashtags.split(',') if args.hashtags else None
        
        if args.platform == 'instagram':
            result = meta.post_instagram_photo(args.image, args.caption, hashtags)
        elif args.platform == 'facebook':
            result = meta.post_facebook_photo(args.image, args.caption)
        else:
            results = meta.post_to_both(args.image, args.caption, hashtags)
            for r in results:
                status = "✅" if r.success else "❌"
                print(f"{status} {r.platform}: {r.post_id or r.error}")
            return
        
        status = "✅" if result.success else "❌"
        print(f"{status} {result.platform}: {result.post_id or result.error}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
