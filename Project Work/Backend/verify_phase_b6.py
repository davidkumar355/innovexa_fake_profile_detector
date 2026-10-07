"""
Verification script for Phase B6 — API Hardening, Integration, and Docs
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE B6 — FULL API HARDENING & DOCS")
    print("=" * 60)
    
    client = TestClient(app)
    checks = []

    # 1. Root & Health Check
    res_root = client.get("/")
    root_ok = (res_root.status_code == 200 and res_root.json().get("status") == "online")
    checks.append(("GET / (Root health check)", "200 OK, status=online", f"{res_root.status_code}", root_ok))

    res_health = client.get("/api/health")
    health_ok = (res_health.status_code == 200 and res_health.json().get("status") == "healthy")
    checks.append(("GET /api/health", "200 OK, status=healthy", f"{res_health.status_code}", health_ok))

    # 2. OpenAPI & Docs
    res_docs = client.get("/docs")
    checks.append(("GET /docs (Swagger UI)", "200 OK", f"{res_docs.status_code}", res_docs.status_code == 200))

    res_openapi = client.get("/openapi.json")
    openapi_ok = (res_openapi.status_code == 200 and "paths" in res_openapi.json())
    checks.append(("GET /openapi.json (OpenAPI schema)", "200 OK with paths", f"{res_openapi.status_code}", openapi_ok))

    # 3. Dashboard endpoint
    res_dash = client.get("/api/dashboard/summary")
    dash_ok = (res_dash.status_code == 200 and "total_profiles_analyzed" in res_dash.json())
    checks.append(("GET /api/dashboard/summary", "200 OK with summary", f"{res_dash.status_code}", dash_ok))

    # 4. Predict browse endpoint
    res_browse = client.post("/api/predict/browse/100")
    browse_ok = (res_browse.status_code == 200 and "risk_score" in res_browse.json())
    checks.append(("POST /api/predict/browse/100", "200 OK with prediction", f"{res_browse.status_code}", browse_ok))

    # 4b. Predict browse 404 handling
    res_browse_404 = client.post("/api/predict/browse/999999")
    checks.append(("POST /api/predict/browse/999999 (404 Error handling)", "404 Not Found", f"{res_browse_404.status_code}", res_browse_404.status_code == 404))

    # 5. Predict simulate endpoint
    payload_sim = {
        "active_feature_indices": [5, 12, 100, 250],
        "connection_node_ids": [10, 20, 30]
    }
    res_sim = client.post("/api/predict/simulate", json=payload_sim)
    sim_ok = (res_sim.status_code == 200 and "risk_tier" in res_sim.json())
    checks.append(("POST /api/predict/simulate", "200 OK with simulation", f"{res_sim.status_code}", sim_ok))

    # 5b. Predict simulate bad input (400)
    bad_payload = {
        "active_feature_indices": [1, 2],
        "connection_node_ids": [999999]  # invalid connection ID
    }
    res_sim_400 = client.post("/api/predict/simulate", json=bad_payload)
    checks.append(("POST /api/predict/simulate bad ID (400 Error handling)", "400 Bad Request", f"{res_sim_400.status_code}", res_sim_400.status_code == 400))

    # 5c. Malformed body (422)
    res_sim_422 = client.post("/api/predict/simulate", content=b"invalid-json")
    checks.append(("POST /api/predict/simulate malformed (422 Validation)", "422 Unprocessable", f"{res_sim_422.status_code}", res_sim_422.status_code == 422))

    # 6. Network endpoints
    res_net_c = client.get("/api/network/clusters")
    net_c_ok = (res_net_c.status_code == 200 and res_net_c.json().get("total_clusters") > 0)
    checks.append(("GET /api/network/clusters", "200 OK with clusters", f"{res_net_c.status_code}", net_c_ok))

    res_net_sub = client.get("/api/network/node/42/subgraph")
    net_sub_ok = (res_net_sub.status_code == 200 and "nodes" in res_net_sub.json())
    checks.append(("GET /api/network/node/42/subgraph", "200 OK with subgraph", f"{res_net_sub.status_code}", net_sub_ok))

    # 7. Profiles endpoints
    res_prof_list = client.get("/api/profiles?page=1&page_size=10")
    prof_ok = (res_prof_list.status_code == 200 and len(res_prof_list.json()["items"]) == 10)
    checks.append(("GET /api/profiles", "200 OK, 10 items", f"{res_prof_list.status_code}", prof_ok))

    res_cats = client.get("/api/profiles/categories")
    cats_ok = (res_cats.status_code == 200 and len(res_cats.json()) > 0)
    checks.append(("GET /api/profiles/categories", "200 OK with categories", f"{res_cats.status_code}", cats_ok))

    res_prof_detail = client.get("/api/profiles/42")
    prof_detail_ok = (res_prof_detail.status_code == 200 and res_prof_detail.json()["node_id"] == 42)
    checks.append(("GET /api/profiles/42", "200 OK with details", f"{res_prof_detail.status_code}", prof_detail_ok))

    # 8. Detection history endpoint
    res_hist = client.get("/api/history?page=1&page_size=5")
    hist_ok = (res_hist.status_code == 200 and "items" in res_hist.json())
    checks.append(("GET /api/history", "200 OK with history items", f"{res_hist.status_code}", hist_ok))

    # 9. Middleware Process-Time header
    has_header = "X-Process-Time-Ms" in res_root.headers
    checks.append(("Response Header X-Process-Time-Ms", "Header present", f"{res_root.headers.get('X-Process-Time-Ms')} ms", has_header))

    print("\nVERIFICATION RESULTS TABLE:")
    print(f"{'Check':<52} | {'Expected':<22} | {'Actual':<22} | {'Status'}")
    print("-" * 106)
    all_passed = True
    for name, exp, act, passed in checks:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        print(f"{name:<52} | {exp:<22} | {act:<22} | {status_str}")

    print("=" * 60)
    if all_passed:
        print("OVERALL STATUS: ✅ ALL CHECKS PASSED")
    else:
        print("OVERALL STATUS: ❌ SOME CHECKS FAILED")
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
