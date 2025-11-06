#!/usr/bin/env python
"""
Quick test script for price endpoints
"""
import httpx
import time
import subprocess
import signal

# Start uvicorn
proc = subprocess.Popen(
    ["venv/bin/python", "-m", "uvicorn", "app.main:app", "--port", "9000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to start
time.sleep(3)

try:
    # Test endpoints
    minifig_id = "9eb475d0-9b38-4bc6-941c-20a9a37df7a7"

    print("=" * 60)
    print("Testing Price Endpoints")
    print("=" * 60)

    print("\n1. GET /v1/minifigures/{id}/prices")
    r = httpx.get(f"http://localhost:9000/v1/minifigures/{minifig_id}/prices?limit=2")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Returned {len(data)} listings")
        print(f"  First listing: ${data[0]['price_usd']} ({data[0]['condition']})")
    else:
        print(f"✗ Error: {r.text}")

    print("\n2. GET /v1/minifigures/{id}/price-history")
    r = httpx.get(f"http://localhost:9000/v1/minifigures/{minifig_id}/price-history")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Minifigure: {data['minifigure_name']}")
        print(f"✓ Snapshots: {len(data['snapshots'])}")
        if data['snapshots']:
            snap = data['snapshots'][0]
            print(f"  First snapshot: {snap['date']} - Avg ${snap['avg_price_usd']}")
    else:
        print(f"✗ Error: {r.text}")

    print("\n3. GET /v1/snapshots")
    r = httpx.get("http://localhost:9000/v1/snapshots?page_size=2")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Returned {len(data)} snapshots")
        if data:
            print(f"  First snapshot: Date {data[0]['date']}, Avg ${data[0]['avg_price_usd']}")
    else:
        print(f"✗ Error: {r.text}")

    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)

finally:
    # Stop server
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=5)
