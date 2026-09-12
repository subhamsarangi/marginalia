import sys
import time
import httpx

GROBID_URL = "http://localhost:8070"


def wait_for_grobid(retries: int = 10, delay: float = 2.0):
    print("[GROBID] checking...", end="", flush=True)
    for i in range(retries):
        try:
            r = httpx.get(f"{GROBID_URL}/api/isalive", timeout=5)
            r.raise_for_status()
            print(" alive")
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(delay)
    print(" not responding")
    print("[GROBID] not running — start it with: docker compose up -d")
    sys.exit(1)
