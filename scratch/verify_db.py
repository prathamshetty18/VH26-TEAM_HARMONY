import requests
import time

BASE_URL = "http://127.0.0.1:8000"
MACHINE_NAME = "test-db-machine"

def run_db_verification():
    print("--- Starting DB Verification ---")
    
    # 1. Baseline GET /machines and GET /manuals
    resp_machines_1 = requests.get(f"{BASE_URL}/machines").json()
    resp_manuals_1 = requests.get(f"{BASE_URL}/manuals").json()
    print("Initial Machines:", resp_machines_1.get("machines"))
    
    # 2. Upload new txt manual
    test_content = f"MACHINE: {MACHINE_NAME}\nSECTION: Test Section\nMEANING: This is a test."
    files = {"file": (f"{MACHINE_NAME}.txt", test_content.encode("utf-8"), "text/plain")}
    resp_upload = requests.post(f"{BASE_URL}/manuals/upload", files=files)
    print("Upload response status:", resp_upload.status_code)
    upload_data = resp_upload.json()
    print("Upload JSON:", upload_data)
    assert resp_upload.status_code == 200, "Expected 200 OK for valid txt"
    assert upload_data.get("status") == "success", "Expected status: success"
    initial_chunks = upload_data.get("chunk_count", 0)
    
    try:
        # 3. GET /machines to confirm cache update
        resp_machines_2 = requests.get(f"{BASE_URL}/machines").json()
        assert MACHINE_NAME in resp_machines_2.get("machines", []), "New machine not in /machines"
        print("Machine successfully appeared in cache immediately.")

        # 4. POST /query to confirm retrieval
        query_req = {"message": f"What is the test section on {MACHINE_NAME}?"}
        resp_query = requests.post(f"{BASE_URL}/query", json=query_req)
        assert resp_query.status_code == 200, "Query failed"
        query_data = resp_query.json()
        sources = query_data.get("sources", [])
        assert any(s.get("machine") == MACHINE_NAME for s in sources), "Retrieval failed for new machine"
        print("Query successfully retrieved new machine.")

        # 5. Re-upload with additional content
        new_test_content = test_content + "\nSECTION: Additional Section\nMEANING: More testing."
        files2 = {"file": (f"{MACHINE_NAME}.txt", new_test_content.encode("utf-8"), "text/plain")}
        resp_reupload = requests.post(f"{BASE_URL}/manuals/upload", files=files2)
        reupload_data = resp_reupload.json()
        new_chunks = reupload_data.get("chunk_count", 0)
        assert new_chunks > initial_chunks, "Expected chunk count to reflect new content"
        print(f"Re-upload successful. Initial chunks: {initial_chunks}, New chunks: {new_chunks}")
        
        # 6. DELETE the manual
        resp_delete = requests.delete(f"{BASE_URL}/manuals/{MACHINE_NAME}")
        assert resp_delete.status_code == 200, "Delete failed"
        print("Delete JSON:", resp_delete.json())
        
        # Confirm it's gone from /machines
        resp_machines_3 = requests.get(f"{BASE_URL}/machines").json()
        assert MACHINE_NAME not in resp_machines_3.get("machines", []), "Machine still in /machines after delete"
        print("Machine successfully removed from cache.")

        # 7. DELETE again and assert 404
        resp_delete_2 = requests.delete(f"{BASE_URL}/manuals/{MACHINE_NAME}")
        assert resp_delete_2.status_code == 404, f"Expected 404 on double delete, got {resp_delete_2.status_code}"
        print("Double delete returned 404 as expected.")
        
    finally:
        # Ensure cleanup
        requests.delete(f"{BASE_URL}/manuals/{MACHINE_NAME}")
        print("--- DB Verification Complete ---")

if __name__ == "__main__":
    run_db_verification()
