#!/usr/bin/env python
"""
Music Mood Prediction - Backend Demo Server
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
# Also add backend directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎵 Music Mood Prediction - Backend Server")
    print("="*60 + "\n")
    
    try:
        import uvicorn
        # Import main from current directory
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", os.path.join(os.path.dirname(__file__), "main.py"))
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        app = main_module.app
        
        print("✅ Starting FastAPI server...")
        print("📍 API URL: http://localhost:8000")
        print("📚 Swagger Docs: http://localhost:8000/api/docs")
        print("📋 ReDoc: http://localhost:8000/api/redoc")
        print("\n" + "-"*60 + "\n")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\nPlease install dependencies:")
        print("pip install fastapi uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server Error: {e}")
        sys.exit(1)
