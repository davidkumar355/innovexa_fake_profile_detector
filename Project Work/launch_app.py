"""
Innovexa Localhost Application Orchestrator
Launches FastAPI backend (port 8000) and Frontend static server (port 3000),
verifies health, opens the default web browser, and cleanly stops all servers on exit.
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
import urllib.request
import urllib.error

# Resolve directories relative to this file
PROJECT_WORK_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_WORK_DIR, "Backend")
FRONTEND_DIR = os.path.join(PROJECT_WORK_DIR, "Frontend")

BACKEND_PORT = 8000
FRONTEND_PORT = 3000
HEALTH_URL = f"http://127.0.0.1:{BACKEND_PORT}/api/health"
APP_URL = f"http://127.0.0.1:{FRONTEND_PORT}"


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a network port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def check_backend_healthy() -> bool:
    """Check if the Innovexa FastAPI backend is responding with 200 OK."""
    try:
        req = urllib.request.Request(HEALTH_URL, headers={"User-Agent": "InnovexaLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def kill_process_tree(proc: subprocess.Popen):
    """Safely terminate a subprocess and any of its children."""
    if proc is None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            proc.terminate()
            proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main():
    print("=" * 68)
    print("        INNOVEXA — FAKE PROFILE DETECTOR LOCAL LAUNCHER         ")
    print("=" * 68)
    print(f"[*] Project Directory: {PROJECT_WORK_DIR}")
    print(f"[*] Python Interpreter: {sys.executable}")
    print("-" * 68)

    backend_proc = None
    frontend_proc = None

    # 1. Start Backend Server
    if is_port_in_use(BACKEND_PORT):
        if check_backend_healthy():
            print(f"[+] Backend is already running and healthy on port {BACKEND_PORT}.")
        else:
            print(f"[!] Warning: Port {BACKEND_PORT} is already occupied by another service.")
    else:
        print(f"[*] [1/3] Starting FastAPI Backend on http://127.0.0.1:{BACKEND_PORT} ...")
        cmd_backend = [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1",
            "--port", str(BACKEND_PORT)
        ]
        backend_proc = subprocess.Popen(
            cmd_backend,
            cwd=BACKEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # 2. Start Frontend Server
    if is_port_in_use(FRONTEND_PORT):
        print(f"[+] Frontend server is already active on port {FRONTEND_PORT}.")
    else:
        print(f"[*] [2/3] Starting Frontend Server on http://127.0.0.1:{FRONTEND_PORT} ...")
        cmd_frontend = [
            sys.executable, "-m", "http.server", str(FRONTEND_PORT)
        ]
        frontend_proc = subprocess.Popen(
            cmd_frontend,
            cwd=FRONTEND_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # 3. Wait for Backend Health
    print(f"[*] [3/3] Verifying server health at {HEALTH_URL} ...", end="", flush=True)
    ready = False
    for attempt in range(20):
        if check_backend_healthy():
            ready = True
            break
        time.sleep(0.5)
        print(".", end="", flush=True)
    print()

    if ready:
        print(f"[+] All systems operational! Health check passed.")
    else:
        print(f"[!] Notice: Backend health check timed out, attempting to launch browser anyway...")

    # 4. Open Default Web Browser
    print(f"[*] Opening browser to {APP_URL} ...")
    try:
        webbrowser.open(APP_URL)
    except Exception as e:
        print(f"[!] Could not automatically open browser: {e}")

    # 5. Active Console Monitor
    print("=" * 68)
    print("  APPLICATION IS RUNNING SUCCESSFULLY ON LOCALHOST")
    print("=" * 68)
    print(f"  * Frontend Web UI:       {APP_URL}")
    print(f"  * Backend Swagger Docs:  http://127.0.0.1:{BACKEND_PORT}/docs")
    print(f"  * Backend API Health:    {HEALTH_URL}")
    print("=" * 68)
    print("  -> Keep this window open while using the application.")
    print("  -> Press [Ctrl + C] at any time in this window to stop all servers.")
    print("=" * 68)

    try:
        while True:
            # Check if our spawned processes unexpectedly died
            if backend_proc and backend_proc.poll() is not None:
                print("\n[!] Backend server process exited unexpectedly.")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print("\n[!] Frontend server process exited unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Received shutdown signal (Ctrl+C). Stopping servers...")
    finally:
        if backend_proc:
            print("[*] Terminating FastAPI Backend...")
            kill_process_tree(backend_proc)
        if frontend_proc:
            print("[*] Terminating Frontend HTTP Server...")
            kill_process_tree(frontend_proc)
        print("[+] All local servers stopped cleanly. Goodbye!\n")


if __name__ == "__main__":
    main()
