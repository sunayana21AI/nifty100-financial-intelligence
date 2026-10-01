"""
tests/perf_test.py
Day 43 — Performance & Integration Testing.
"""
import time
import sqlite3
import threading
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"

API_BASE = "http://127.0.0.1:8000"


def test_concurrent_screener():
    print("\n" + "=" * 60)
    print("TEST 1: 10 concurrent screener API calls")
    print("=" * 60)

    results = []
    errors = []

    def call_screener(i):
        try:
            start = time.time()
            r = requests.get(f"{API_BASE}/api/v1/screener?min_roe=15", timeout=15)
            elapsed = time.time() - start
            results.append({
                "thread": i, "status": r.status_code,
                "elapsed": round(elapsed, 3),
                "count": len(r.json()) if r.status_code == 200 else 0,
            })
        except Exception as e:
            errors.append({"thread": i, "error": str(e)})

    start_all = time.time()
    threads = [threading.Thread(target=call_screener, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    total_time = time.time() - start_all

    print(f"Total time: {total_time:.2f}s (target < 10s)")
    print(f"Successful: {len(results)}/10")
    print(f"Errors: {len(errors)}")

    if results:
        avg = sum(r["elapsed"] for r in results) / len(results)
        mx = max(r["elapsed"] for r in results)
        print(f"Avg response: {avg:.3f}s")
        print(f"Max response: {mx:.3f}s")

    status = "PASS" if total_time < 10 and len(errors) == 0 else "FAIL"
    print(f"\n[{status}] Concurrent screener test")

    return {
        "test": "concurrent_screener",
        "total_time": round(total_time, 3),
        "success": len(results),
        "errors": len(errors),
        "status": status,
    }


def check_indexes():
    print("\n" + "=" * 60)
    print("TEST 2: SQLite indexes")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    indexes = cur.execute("""
        SELECT name, tbl_name FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY tbl_name, name
    """).fetchall()

    print(f"Custom indexes found: {len(indexes)}")
    for name, table in indexes:
        print(f"  {table}.{name}")

    conn.close()
    return indexes


def create_indexes():
    print("\nCreating indexes on large tables...")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    idx_sql = [
        "CREATE INDEX IF NOT EXISTS idx_ratios_company_year ON financial_ratios(company_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_ratios_year ON financial_ratios(year)",
        "CREATE INDEX IF NOT EXISTS idx_pl_company_year ON profitandloss(company_id, year_int)",
        "CREATE INDEX IF NOT EXISTS idx_bs_company_year ON balancesheet(company_id, year_int)",
        "CREATE INDEX IF NOT EXISTS idx_cf_company_year ON cashflow(company_id, year_int)",
        "CREATE INDEX IF NOT EXISTS idx_docs_company ON documents(company_id)",
        "CREATE INDEX IF NOT EXISTS idx_peers_group ON peer_percentiles(peer_group_name)",
    ]

    for sql in idx_sql:
        try:
            cur.execute(sql)
            table = sql.split(' ON ')[1].split('(')[0]
            print(f"  OK: {table}")
        except Exception as e:
            print(f"  WARN: {e}")

    conn.commit()
    conn.close()
    print("Done creating indexes")


def test_db_queries():
    print("\n" + "=" * 60)
    print("TEST 3: DB query performance")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    queries = [
        ("Latest ratios for TCS", """
            SELECT * FROM financial_ratios WHERE company_id = 'TCS'
            ORDER BY year DESC LIMIT 1
        """),
        ("All companies count", "SELECT COUNT(*) FROM companies"),
        ("Screener filter", """
            SELECT company_id FROM financial_ratios
            WHERE year = 2024 AND return_on_equity_pct > 15
        """),
    ]

    results = []
    for name, sql in queries:
        start = time.time()
        cur.execute(sql)
        cur.fetchall()
        elapsed = (time.time() - start) * 1000
        results.append({"query": name, "ms": round(elapsed, 2)})
        print(f"  {name}: {elapsed:.1f}ms")

    conn.close()
    return results


def save_report(sections):
    out_path = OUTPUT_DIR / "perf_notes.md"
    lines = ["# Performance Notes — Day 43\n"]

    for section in sections:
        lines.append(f"\n## {section['title']}\n")
        for item in section["items"]:
            lines.append(f"- {item}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nOK: Wrote {out_path}")


def main():
    print("=" * 60)
    print("Day 43 — Performance & Integration Testing")
    print("=" * 60)

    sections = []

    existing = check_indexes()
    if len(existing) < 5:
        create_indexes()
        existing = check_indexes()

    sections.append({
        "title": "SQLite Indexes",
        "items": [f"{table}.{name}" for name, table in existing],
    })

    db_results = test_db_queries()
    sections.append({
        "title": "DB Query Times",
        "items": [f"{r['query']}: {r['ms']}ms" for r in db_results],
    })

    try:
        api_result = test_concurrent_screener()
        sections.append({
            "title": "Concurrent Screener API Calls",
            "items": [
                f"Total time: {api_result['total_time']}s",
                f"Success: {api_result['success']}/10",
                f"Errors: {api_result['errors']}",
                f"Status: {api_result['status']}",
            ],
        })
    except Exception as e:
        print(f"\nWARN: API test skipped (uvicorn running?): {e}")
        sections.append({
            "title": "Concurrent Screener API Calls",
            "items": [f"Skipped: {e}"],
        })

    save_report(sections)


if __name__ == "__main__":
    main()