import subprocess
import sys
import time
import os

def main():
    print("=" * 60)
    print("Averish Shipping AI - Intelligent Document Verification & Inbox Management")
    print("=" * 60)

    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(workspace_dir, "frontend")

    # Set PYTHONPATH to workspace root
    env = os.environ.copy()
    env["PYTHONPATH"] = workspace_dir

    # Start FastAPI Backend
    print("[1/2] Starting Python FastAPI Backend Server on http://localhost:8000 ...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=workspace_dir,
        env=env
    )

    time.sleep(2)

    # Start Vite Frontend
    print("[2/2] Starting Vite React Frontend Desktop UI on http://localhost:3000 ...")
    if os.name == 'nt':
        frontend_cmd = ["cmd", "/c", "npm.cmd", "run", "dev"]
    else:
        frontend_cmd = ["npm", "run", "dev"]

    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir
    )

    print("\n[OK] System Online!")
    print("   -> API Docs & Server: http://localhost:8000")
    print("   -> Desktop Web App:   http://localhost:3000")
    print("=" * 60)
    print("Press Ctrl+C to stop servers.")

    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
