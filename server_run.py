import os

def main():
    port = os.getenv("PORT", "8000")
    workers = os.getenv("WORKERS", str(os.cpu_count()))

    cmd = [
        "granian",
        "--interface", "asgi",
        "--host", "0.0.0.0",
        "--port", port,
        "--workers", workers,
        "app.main:app",
    ]

    os.execvp(cmd[0], cmd)

if __name__ == "__main__":
    main()