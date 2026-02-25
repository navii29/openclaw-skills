#!/usr/bin/env python3
"""
Meta Business Suite Automation
Post to Instagram and Facebook via Meta Graph API.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MetaAutomation:
    """Meta Graph API automation for Instagram and Facebook."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("META_ACCESS_TOKEN required")
        
        self.ig_business_id = os.getenv("INSTAGRAM_BUSINESS_ID")
        self.fb_page_id = os.getenv("FACEBOOK_PAGE_ID")
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make API request to Meta Graph API."""
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params['access_token'] = self.access_token
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, params=params, data=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(f"API Error: {result['error'].get('message', 'Unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def upload_image(self, image_path: str) -> str:
        """Upload image to get URL."""
        # For simplicity, assume image is publicly accessible
        # In production, upload to a CDN first
        return image_path
    
    def post_instagram_photo(self, image_url: str, caption: str) -> str:
        """Post photo to Instagram."""
        if not self.ig_business_id:
            raise ValueError("INSTAGRAM_BUSINESS_ID required")
        
        logger.info(f"📸 Posting to Instagram: {caption[:50]}...")
        
        # Create media container
        params = {
            'image_url': image_url,
            'caption': caption,
        }
        
        result = self._make_request(
            "POST",
            f"{self.ig_business_id}/media",
            data=params
        )
        
        creation_id = result.get('id')
        
        # Publish container
        publish_result = self._make_request(
            "POST",
            f"{self.ig_business_id}/media_publish",
            data={'creation_id': creation_id}
        )
        
        post_id = publish_result.get('id')
        logger.info(f"✅ Posted to Instagram: {post_id}")
        return post_id
    
    def post_facebook_photo(self, image_url: str, caption: str) -> str:
        """Post photo to Facebook Page."""
        if not self.fb_page_id:
            raise ValueError("FACEBOOK_PAGE_ID required")
        
        logger.info(f"📘 Posting to Facebook: {caption[:50]}...")
        
        result = self._make_request(
            "POST",
            f"{self.fb_page_id}/photos",
            data={
                'url': image_url,
                'caption': caption
            }
        )
        
        post_id = result.get('id')
        logger.info(f"✅ Posted to Facebook: {post_id}")
        return post_id
    
    def post_carousel(self, image_urls: List[str], caption: str) -> str:
        """Post carousel to Instagram."""
        if not self.ig_business_id:
            raise ValueError("INSTAGRAM_BUSINESS_ID required")
        
        logger.info(f"🎠 Posting carousel with {len(image_urls)} images...")
        
        # Create children containers
        children_ids = []
        for url in image_urls:
            result = self._make_request(
                "POST",
                f"{self.ig_business_id}/media",
                data={'image_url': url, 'is_carousel_item': True}
            )
            children_ids.append(result['id'])
        
        # Create carousel container
        carousel = self._make_request(
            "POST",
            f"{self.ig_business_id}/media",
            data={
                'caption': caption,
                'media_type': 'CAROUSEL',
                'children': ','.join(children_ids)
            }
        )
        
        # Publish
        result = self._make_request(
            "POST",
            f"{self.ig_business_id}/media_publish",
            data={'creation_id': carousel['id']}
        )
        
        logger.info(f"✅ Posted carousel: {result['id']}")
        return result['id']
    
    def get_insights(self, platform: str, metric: str = "impressions") -> Dict:
        """Get post insights."""
        object_id = self.ig_business_id if platform == "instagram" else self.fb_page_id
        
        result = self._make_request(
            "GET",
            f"{object_id}/insights",
            params={'metric': metric}
        )
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Meta Business Automation")
    parser.add_argument("--platform", choices=["instagram", "facebook"], required=True)
    parser.add_argument("--image", help="Image URL or path")
    parser.add_argument("--carousel", nargs="+", help="Multiple images for carousel")
    parser.add_argument("--caption", required=True, help="Post caption")
    parser.add_argument("--video", help="Video URL")
    
    args = parser.parse_args()
    
    try:
        meta = MetaAutomation()
        
        if args.carousel:
            # Post carousel
            meta.post_carousel(args.carousel, args.caption)
        elif args.platform == "instagram":
            meta.post_instagram_photo(args.image, args.caption)
        else:
            meta.post_facebook_photo(args.image, args.caption)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
