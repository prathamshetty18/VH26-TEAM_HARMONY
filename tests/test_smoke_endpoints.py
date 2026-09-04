import requests
import json
import time
import random
import string
import concurrent.futures

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    print("--- 1. Testing All API Endpoints Availability & Schema ---")
    endpoints = [
        ("GET", "/", 200),
        ("GET", "/health", 200),
        ("GET", "/api/health", 200),
        ("GET", "/machines", 200),
        ("GET", "/api/manuals", 200),
        ("GET", "/api/benchmarks", 200),
        ("GET", "/api/system-status", 200),
        ("GET", "/dashboard", 200),
    ]
    for method, path, exp_code in endpoints:
        r = requests.request(method, f"{BASE_URL}{path}")
        assert r.status_code == exp_code, f"Endpoint {path} returned {r.status_code}, expected {exp_code}"
        print(f"  [OK] {method} {path} -> {r.status_code}")

if __name__ == '__main__':
    test_endpoints()
