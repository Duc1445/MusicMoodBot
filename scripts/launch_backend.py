#!/usr/bin/env python3
"""Launch backend using subprocess."""

import subprocess
import sys
import time

if __name__ == "__main__":
    print("Launching Music Mood Backend API v2.1.0...")
    
    # Use subprocess to run uvicorn in a separate process
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd="d:\\MMB_FRONTBACK",
        env={"PYTHONPATH": "d:\\MMB_FRONTBACK"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    print("Backend process started (PID: {})".format(proc.pid))
    print("Server will be available at http://127.0.0.1:8000")
    print("Streaming logs...\n")
    
    # Stream output
    try:
        for line in proc.stdout:
            print(line, end='')
    except KeyboardInterrupt:
        print("\nShutting down...")
        proc.terminate()
        proc.wait(timeout=5)
