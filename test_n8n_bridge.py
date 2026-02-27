#!/usr/bin/env python3
"""
Test script for n8n Bridge Integration
Run this to verify the bridge is working correctly
"""

import sys
import os

# Add workspace to path for imports
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace"))

try:
    from skills.n8n_bridge import test_bridge, ping
    
    print("=" * 60)
    print("🌉 n8n Bridge Integration Test")
    print("=" * 60)
    
    # Check environment
    api_key = os.getenv("N8N_BRIDGE_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: N8N_BRIDGE_API_KEY not set!")
        print("   Set it with: export N8N_BRIDGE_API_KEY='your_key_here'")
        print()
    
    # Run tests
    test_bridge()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the skill is installed at ~/.openclaw/workspace/skills/n8n_bridge/")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
