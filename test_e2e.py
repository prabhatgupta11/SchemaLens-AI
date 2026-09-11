import requests
import time
import sys

API_URL = "http://localhost:8000/api"

print("--- Testing E2E Functionality ---")

# 1. Create a dummy CSV file
csv_content = """InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country
536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,12/1/2010 8:26,2.55,17850,United Kingdom
536365,71053,WHITE METAL LANTERN,6,12/1/2010 8:26,3.39,17850,United Kingdom
536366,22633,HAND WARMER UNION JACK,6,12/1/2010 8:28,1.85,17850,United Kingdom
"""
with open("test_data.csv", "w") as f:
    f.write(csv_content)

# 2. Upload CSV
print("\n[1/4] Uploading CSV...")
with open("test_data.csv", "rb") as f:
    response = requests.post(f"{API_URL}/datasets", files={"file": ("test_data.csv", f, "text/csv")})
    
if response.status_code != 200:
    print("Failed to upload!", response.text)
    sys.exit(1)
    
job_id = response.json()["job_id"]
print(f"Upload initiated. Job ID: {job_id}")

# 3. Poll for ingestion completion
print("\n[2/4] Waiting for ingestion to complete...")
dataset_id = None
for _ in range(30):
    res = requests.get(f"{API_URL}/jobs/{job_id}").json()
    status = res["status"]
    print(f"Status: {status}")
    if status == "COMPLETED":
        dataset_id = res["result"]["dataset_id"]
        print(f"Ingestion successful! Dataset ID: {dataset_id}")
        break
    elif status == "FAILED":
        print("Ingestion failed!", res.get("error"))
        sys.exit(1)
    time.sleep(1)

if not dataset_id:
    print("Ingestion timed out.")
    sys.exit(1)

# 4. List Datasets (Verify it shows up)
print("\n[3/4] Fetching datasets list...")
datasets = requests.get(f"{API_URL}/datasets").json()
print("Available datasets:", [d['name'] for d in datasets])

# 5. Ask a question
print("\n[4/4] Asking a question: 'What is the total quantity sold?'")
q_res = requests.post(f"{API_URL}/query", json={
    "dataset_id": dataset_id,
    "question": "What is the total quantity sold?"
})
q_job = q_res.json()["job_id"]

for _ in range(30):
    res = requests.get(f"{API_URL}/jobs/{q_job}").json()
    status = res["status"]
    if status == "COMPLETED":
        print("\nSUCCESS! Answer received:")
        print("SQL Generated:", res["result"]["sql"])
        print("Final Answer:", res["result"]["answer"])
        print("Raw Data:", res["result"]["data"])
        sys.exit(0)
    elif status == "FAILED":
        print("Query failed!", res.get("error"))
        sys.exit(1)
    time.sleep(1.5)
    
print("Query timed out.")
