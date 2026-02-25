#!/usr/bin/env python3
"""Test LinkedIn Post Scheduler"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/linkedin-scheduler')

from datetime import datetime, timedelta
from linkedin_scheduler import LinkedInPost, PostScheduler, LinkedInAPI

def run_tests():
    """Test scheduling logic without real API calls."""
    print("🧪 Testing LinkedIn Post Scheduler...\n")
    
    # Test 1: LinkedInPost dataclass
    print("Test 1: LinkedInPost Erstellung")
    future_time = datetime.now() + timedelta(hours=2)
    post = LinkedInPost(
        text="Das ist ein Test-Post für LinkedIn! #innovation #business",
        scheduled_time=future_time,
        article_url="https://example.de/blog",
        visibility="PUBLIC"
    )
    
    print(f"   Text: {post.text[:30]}...")
    print(f"   Scheduled: {post.scheduled_time.strftime('%H:%M')}")
    print(f"   Is Due: {post.is_due} (Expected: False)")
    print(f"   Time Until: {post.time_until}")
    
    test1_pass = not post.is_due and post.time_until.total_seconds() > 0
    print(f"   Status: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print()
    
    # Test 2: Due post detection
    print("Test 2: Fällige Posts erkennen")
    past_time = datetime.now() - timedelta(minutes=5)
    due_post = LinkedInPost(
        text="Dieser Post ist überfällig!",
        scheduled_time=past_time,
        posted=False
    )
    
    print(f"   Is Due: {due_post.is_due} (Expected: True)")
    test2_pass = due_post.is_due
    print(f"   Status: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print()
    
    # Test 3: Posted posts not due
    print("Test 3: Bereits gepostete Posts")
    posted_post = LinkedInPost(
        text="Bereits gepostet",
        scheduled_time=past_time,
        posted=True,
        post_id="urn:li:share:123"
    )
    
    print(f"   Is Due: {posted_post.is_due} (Expected: False)")
    test3_pass = not posted_post.is_due
    print(f"   Status: {'✅ PASS' if test3_pass else '❌ FAIL'}")
    print()
    
    # Test 4: Best time slot calculation
    print("Test 4: Best-Time-Slot Berechnung")
    api = LinkedInAPI("fake-token")
    scheduler = PostScheduler(api)
    
    # Clear any existing posts
    scheduler.posts = []
    
    # Schedule multiple posts
    post1 = scheduler.schedule_for_next_slot("Post 1")
    post2 = scheduler.schedule_for_next_slot("Post 2")
    post3 = scheduler.schedule_for_next_slot("Post 3")
    post4 = scheduler.schedule_for_next_slot("Post 4")
    
    times = [p.scheduled_time for p in [post1, post2, post3, post4]]
    
    print(f"   Post 1: {post1.scheduled_time.strftime('%d.%m %H:%M')}")
    print(f"   Post 2: {post2.scheduled_time.strftime('%d.%m %H:%M')}")
    print(f"   Post 3: {post3.scheduled_time.strftime('%d.%m %H:%M')}")
    print(f"   Post 4: {post4.scheduled_time.strftime('%d.%m %H:%M')}")
    
    # All times should be different
    unique_times = len(set(times))
    test4_pass = unique_times == 4
    print(f"   Eindeutige Zeitpunkte: {unique_times}/4")
    print(f"   Status: {'✅ PASS' if test4_pass else '❌ FAIL'}")
    print()
    
    # Test 5: Statistics
    print("Test 5: Statistik-Berechnung")
    scheduler2 = PostScheduler(api)
    scheduler2.posts = [
        LinkedInPost(text="Posted 1", scheduled_time=datetime.now() - timedelta(days=1), posted=True),
        LinkedInPost(text="Posted 2", scheduled_time=datetime.now() - timedelta(days=2), posted=True),
        LinkedInPost(text="Pending 1", scheduled_time=datetime.now() + timedelta(days=1)),
        LinkedInPost(text="Overdue", scheduled_time=datetime.now() - timedelta(hours=1)),
    ]
    
    stats = scheduler2.get_stats()
    print(f"   Total: {stats['total']} (Expected: 4)")
    print(f"   Posted: {stats['posted']} (Expected: 2)")
    print(f"   Pending: {stats['pending']} (Expected: 2)")
    print(f"   Overdue: {stats['overdue']} (Expected: 1)")
    
    test5_pass = (
        stats['total'] == 4 and
        stats['posted'] == 2 and
        stats['pending'] == 2 and
        stats['overdue'] == 1
    )
    print(f"   Status: {'✅ PASS' if test5_pass else '❌ FAIL'}")
    print()
    
    # Test 6: Post text formatting
    print("Test 6: Post Text Formatierung")
    long_post = LinkedInPost(
        text="Das ist ein sehr langer Text " * 20,
        scheduled_time=datetime.now()
    )
    summary = long_post.summary
    
    print(f"   Summary Length: {len(summary)}")
    test6_pass = len(summary) < 100  # Should be truncated
    print(f"   Status: {'✅ PASS' if test6_pass else '❌ FAIL'}")
    print()
    
    # Summary
    results = [test1_pass, test2_pass, test3_pass, test4_pass, test5_pass, test6_pass]
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Skill is ready for production.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
