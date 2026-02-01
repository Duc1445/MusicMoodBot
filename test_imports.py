#!/usr/bin/env python3
"""
Test script to check syntax of login and signup screens
"""

import sys
import os

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, 'frontend')
sys.path.insert(0, frontend_dir)

try:
    print("Testing imports...")
    from src.screens.login_screen import create_login_screen
    print("✓ Login screen imported successfully")

    from src.screens.signup_screen import create_signup_screen
    print("✓ Signup screen imported successfully")

    from src.config.theme_professional import *
    print("✓ Theme imported successfully")

    from src.components.ui_components_pro import *
    print("✓ UI components imported successfully")

    print("\n🎉 All imports successful! No syntax errors found.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()