#!/usr/bin/env python3
"""Minimal script to run the backend server."""

import sys
import os

# Add the workspace to path
sys.path.insert(0, 'd:\\MMB_FRONTBACK')

if __name__ == "__main__":
    try:
        import uvicorn
        from backend.main import app
        
        print("Starting Music Mood Backend API v2.1.0...")
        print("Server will be available at http://127.0.0.1:8000")
        print("API docs available at http://127.0.0.1:8000/docs")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
