import subprocess
import sys
import time

processes = []

try:
    backend = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd="backend",
    )

    processes.append(backend)

    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="frontend",
        shell=True,
    )

    processes.append(frontend)

    print("DRIFT iniciado.")
    print("Frontend: http://localhost:3000")
    print("Backend:  http://localhost:8000")
    print("Presiona Ctrl+C para detener ambos procesos.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nDeteniendo DRIFT...")

finally:
    for process in processes:
        if process.poll() is None:
            process.terminate()

    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()