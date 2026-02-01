#!/usr/bin/env python3
"""
Simple test script
"""

print("Testing basic Python...")

try:
    import sys
    print(f"Python version: {sys.version}")
    print("✓ Python is working")
except Exception as e:
    print(f"❌ Python error: {e}")

try:
    import flet as ft
    print("✓ Flet imported successfully")
except Exception as e:
    print(f"❌ Flet import error: {e}")

print("Test completed.")