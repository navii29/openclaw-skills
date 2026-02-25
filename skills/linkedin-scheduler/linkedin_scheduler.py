#!/usr/bin/env python3
"""
LinkedIn Post Scheduler
Schedule and auto-post LinkedIn content at optimal times.
"""

import json
import csv
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
import requests

@dataclass
class LinkedInPost:
    """Represents a LinkedIn post to be scheduled."""
    text: str
    scheduled_time: datetime
    image_url: Optional[str] = None
    article_url: Optional[str] = None
    visibility: str = "PUBLIC"  # PUBLIC, CONNECTIONS
    posted: bool = False
    post_id: Optional[str] = None
    
    @property
    def is_due(self) -> bool:
        """Check if post should be published now."""
        return datetime.now() >= self.scheduled_time and not self.posted
    
    @property
    def time_until(self) -> timedelta:
        """Time until scheduled post."""
        return self.scheduled_time - datetime.now()
    
    @property
    def summary(self) -> str:
        """Short summary of the post."""
        return self.text[:80] + "..." if len(self.text) > 80 else self.text


class LinkedInAPI:
    """LinkedIn API client."""
    
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        self.person_urn = None
    
    def get_profile(self) -> Optional[str]:
        """Get user's LinkedIn profile URN."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/me",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            self.person_urn = f"urn:li:person:{data['id']}"
            return self.person_urn
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
    
    def post_text(self, text: str, visibility: str = "PUBLIC") -> Optional[str]:
        """Post text-only content."""
        if not self.person_urn:
            self.get_profile()
        
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/ugcPosts",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            # LinkedIn returns 201 with Location header
            if response.status_code == 201:
                post_urn = response.headers.get('X-RestLi-Id') or response.headers.get('Location', '').split('/')[-1]
                print(f"   ✅ Posted: {post_urn}")
                return post_urn
            return None
        except Exception as e:
            print(f"   ❌ Error posting: {e}")
            return None
    
    def post_with_link(self, text: str, link: str, visibility: str = "PUBLIC") -> Optional[str]:
        """Post with link preview."""
        if not self.person_urn:
            self.get_profile()
        
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": link
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/ugcPosts",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            if response.status_code == 201:
                post_urn = response.headers.get('X-RestLi-Id')
                print(f"   ✅ Posted with link: {post_urn}")
                return post_urn
            return None
        except Exception as e:
            print(f"   ❌ Error posting: {e}")
            return None


class PostScheduler:
    """Schedule and manage LinkedIn posts."""
    
    # Best times to post on LinkedIn (CET/CEST)
    BEST_TIMES = [
        (8, 30),   # 8:30 - Morning commute/start
        (12, 0),   # 12:00 - Lunch break
        (17, 30),  # 17:30 - End of workday
    ]
    
    def __init__(self, linkedin_api: LinkedInAPI, state_file: str = "schedule_state.json"):
        self.linkedin = linkedin_api
        self.state_file = state_file
        self.posts: List[LinkedInPost] = []
        self._load_state()
    
    def _load_state(self):
        """Load scheduled posts from state file."""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    for item in data.get('posts', []):
                        post = LinkedInPost(
                            text=item['text'],
                            scheduled_time=datetime.fromisoformat(item['scheduled_time']),
                            image_url=item.get('image_url'),
                            article_url=item.get('article_url'),
                            visibility=item.get('visibility', 'PUBLIC'),
                            posted=item.get('posted', False),
                            post_id=item.get('post_id')
                        )
                        self.posts.append(post)
        except Exception as e:
            print(f"Warning: Could not load state: {e}")
    
    def _save_state(self):
        """Save scheduled posts to state file."""
        try:
            data = {
                'posts': [
                    {
                        'text': p.text,
                        'scheduled_time': p.scheduled_time.isoformat(),
                        'image_url': p.image_url,
                        'article_url': p.article_url,
                        'visibility': p.visibility,
                        'posted': p.posted,
                        'post_id': p.post_id
                    }
                    for p in self.posts
                ],
                'last_update': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def add_post(self, text: str, scheduled_time: datetime, 
                 image_url: Optional[str] = None,
                 article_url: Optional[str] = None,
                 visibility: str = "PUBLIC"):
        """Add a post to the schedule."""
        post = LinkedInPost(
            text=text,
            scheduled_time=scheduled_time,
            image_url=image_url,
            article_url=article_url,
            visibility=visibility
        )
        self.posts.append(post)
        self._save_state()
        return post
    
    def schedule_for_next_slot(self, text: str, days_ahead: int = 0, **kwargs) -> LinkedInPost:
        """Schedule for next available best-time slot."""
        now = datetime.now()
        base_date = now + timedelta(days=days_ahead)
        
        # Find next available slot
        for hour, minute in self.BEST_TIMES:
            slot = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if slot > now:
                # Check if slot is free
                if not any(p.scheduled_time == slot for p in self.posts if not p.posted):
                    return self.add_post(text, slot, **kwargs)
        
        # If no slot today, try tomorrow
        return self.schedule_for_next_slot(text, days_ahead + 1, **kwargs)
    
    def process_queue(self) -> int:
        """Process due posts and return count posted."""
        posted_count = 0
        
        for post in self.posts:
            if post.is_due:
                print(f"📤 Posting scheduled content ({post.scheduled_time.strftime('%H:%M')})...")
                
                if post.article_url:
                    post_id = self.linkedin.post_with_link(post.text, post.article_url, post.visibility)
                else:
                    post_id = self.linkedin.post_text(post.text, post.visibility)
                
                if post_id:
                    post.posted = True
                    post.post_id = post_id
                    posted_count += 1
                
                time.sleep(2)  # Rate limiting
        
        if posted_count > 0:
            self._save_state()
        
        return posted_count
    
    def get_upcoming(self, count: int = 5) -> List[LinkedInPost]:
        """Get upcoming scheduled posts."""
        upcoming = [p for p in self.posts if not p.posted and p.scheduled_time > datetime.now()]
        upcoming.sort(key=lambda p: p.scheduled_time)
        return upcoming[:count]
    
    def get_stats(self) -> Dict:
        """Get scheduling statistics."""
        total = len(self.posts)
        posted = sum(1 for p in self.posts if p.posted)
        pending = total - posted
        overdue = sum(1 for p in self.posts if not p.posted and p.scheduled_time < datetime.now())
        
        return {
            'total': total,
            'posted': posted,
            'pending': pending,
            'overdue': overdue
        }


def load_posts_from_csv(filepath: str) -> List[Dict]:
    """Load posts from CSV file."""
    posts = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                posts.append({
                    'text': row.get('text', ''),
                    'date': row.get('date', ''),
                    'time': row.get('time', ''),
                    'article_url': row.get('article_url', ''),
                    'image_url': row.get('image_url', '')
                })
    except Exception as e:
        print(f"Error loading CSV: {e}")
    return posts


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Post Scheduler')
    parser.add_argument('--token', required=True, help='LinkedIn Access Token')
    parser.add_argument('--csv', help='CSV file with posts to schedule')
    parser.add_argument('--text', help='Post text (for single post)')
    parser.add_argument('--time', help='Schedule time (HH:MM)')
    parser.add_argument('--date', help='Schedule date (YYYY-MM-DD)')
    parser.add_argument('--link', help='Article URL to include')
    parser.add_argument('--auto', action='store_true', help='Auto-schedule for best time slot')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--list', action='store_true', help='List scheduled posts')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    # Initialize
    linkedin = LinkedInAPI(args.token)
    scheduler = PostScheduler(linkedin)
    
    # Verify credentials
    profile = linkedin.get_profile()
    if not profile:
        print("❌ Could not authenticate with LinkedIn")
        return
    print(f"✅ Authenticated: {profile}\n")
    
    # List mode
    if args.list:
        upcoming = scheduler.get_upcoming(10)
        print("📅 Scheduled Posts:")
        for post in upcoming:
            status = "✅" if post.posted else "⏳"
            print(f"   {status} {post.scheduled_time.strftime('%d.%m.%Y %H:%M')}: {post.text[:50]}...")
        return
    
    # Stats mode
    if args.stats:
        stats = scheduler.get_stats()
        print("📊 Statistics:")
        for key, value in stats.items():
            print(f"   {key.capitalize()}: {value}")
        return
    
    # CSV import mode
    if args.csv:
        posts = load_posts_from_csv(args.csv)
        print(f"📥 Loaded {len(posts)} posts from CSV")
        
        for post_data in posts:
            if post_data['date'] and post_data['time']:
                try:
                    dt = datetime.strptime(f"{post_data['date']} {post_data['time']}", "%Y-%m-%d %H:%M")
                    scheduler.add_post(
                        text=post_data['text'],
                        scheduled_time=dt,
                        article_url=post_data.get('article_url') or None,
                        image_url=post_data.get('image_url') or None
                    )
                    print(f"   ✓ Scheduled: {dt.strftime('%d.%m.%Y %H:%M')}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
        return
    
    # Single post mode
    if args.text:
        if args.auto:
            post = scheduler.schedule_for_next_slot(
                text=args.text,
                article_url=args.link
            )
            print(f"📅 Auto-scheduled for: {post.scheduled_time.strftime('%d.%m.%Y %H:%M')}")
        elif args.date and args.time:
            try:
                dt = datetime.strptime(f"{args.date} {args.time}", "%Y-%m-%d %H:%M")
                scheduler.add_post(
                    text=args.text,
                    scheduled_time=dt,
                    article_url=args.link
                )
                print(f"📅 Scheduled for: {dt.strftime('%d.%m.%Y %H:%M')}")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            # Post immediately
            print("📤 Posting immediately...")
            post_id = linkedin.post_text(args.text)
            if post_id:
                print(f"✅ Posted: {post_id}")
        return
    
    # Daemon mode
    if args.daemon:
        print(f"🤖 Daemon mode started (checking every {args.interval}s)")
        while True:
            posted = scheduler.process_queue()
            if posted > 0:
                print(f"   Posted {posted} item(s)")
            time.sleep(args.interval)
    
    # Default: process queue once
    posted = scheduler.process_queue()
    print(f"Processed {posted} due posts")


if __name__ == "__main__":
    main()
