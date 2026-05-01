#!/usr/bin/env python3
"""
验证ReActAgent修复是否成功
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

print("Testing import...")
from agent.simple_agent import ReActAgent, Conversation, ReActStep
print("  ✓ Import successful!")

print("\nTesting ReActAgent initialization...")
try:
    from config.settings import get_settings
    settings = get_settings()
    
    agent = ReActAgent(settings=settings)
    print("  ✓ ReActAgent initialized successfully!")
    
    print(f"\n  Model: {agent.model}")
    print(f"  Available tools: {[t['name'] for t in agent.list_tools()]}")
    
    agent.close()
    print("  ✓ Agent closed successfully!")
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("All tests passed! The KeyError has been fixed.")
print("=" * 50)
