"""Tiny load test with the standard library only (PRD ТЗ№3 §84/§97).

    python scripts/load_test.py http://127.0.0.1:8000 --users 20 --seconds 30

Each simulated visitor loops over the public read endpoints and the script prints requests/s,
error count and p50/p95/p99 latency. Run it against a staging copy, never production: the
rate limiter will (correctly) answer 429 once a single IP is over its limits, and those are
counted separately so the numbers stay honest.
"""

import argparse
import statistics
import threading
import time
import urllib.error
import urllib.request

PATHS = [
    "/api/v1/products/?limit=24",
    "/api/v1/categories/",
    "/api/v1/site-settings",
    "/api/v1/exchange-rates/",
    "/api/v1/products/?sort=price_asc&limit=12",
]


def worker(base, deadline, results):
    i = 0
    while time.time() < deadline:
        url = base + PATHS[i % len(PATHS)]
        i += 1
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                code = r.status
                r.read()
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:  # noqa: BLE001
            code = 0
        results.append((code, (time.perf_counter() - start) * 1000))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("base")
    p.add_argument("--users", type=int, default=10)
    p.add_argument("--seconds", type=int, default=20)
    a = p.parse_args()
    results: list = []
    deadline = time.time() + a.seconds
    threads = [threading.Thread(target=worker, args=(a.base.rstrip("/"), deadline, results)) for _ in range(a.users)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    ok = sorted(ms for code, ms in results if code == 200)
    limited = sum(1 for code, _ in results if code == 429)
    errors = sum(1 for code, _ in results if code not in (200, 429))
    print(f"requests {len(results)} ({len(results) / a.seconds:.1f}/s), ok {len(ok)}, rate-limited {limited}, errors {errors}")
    if ok:
        q = statistics.quantiles(ok, n=100)
        print(f"latency ms: p50 {q[49]:.0f}  p95 {q[94]:.0f}  p99 {q[98]:.0f}  max {ok[-1]:.0f}")


if __name__ == "__main__":
    main()
