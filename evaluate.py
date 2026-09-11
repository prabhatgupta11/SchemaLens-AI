import os
import time
import requests
import argparse

API_URL = "http://localhost:8000/api"

QUESTIONS = [
    {"q": "Top 10 products by revenue", "expect_fail": False},
    {"q": "Which countries grew most between two quarters", "expect_fail": False},
    {"q": "Net revenue in a given month", "expect_fail": False},
    {"q": "How many customers bought only once, and what share of revenue they represent", "expect_fail": False},
    {"q": "Which products are most often bought together", "expect_fail": False},
    {"q": "What is the name of the CEO of the company?", "expect_fail": True} # Unanswerable
]

def evaluate(dataset_id: str):
    print(f"Evaluating dataset {dataset_id}...\n")
    
    for q_data in QUESTIONS:
        question = q_data['q']
        print(f"=== Q: {question} ===")
        
        # Submit query
        res = requests.post(f"{API_URL}/query", json={"dataset_id": dataset_id, "question": question})
        if res.status_code != 200:
            print(f"Error submitting query: {res.text}")
            continue
            
        job_id = res.json()["job_id"]
        
        # Poll
        start_time = time.time()
        while True:
            job_res = requests.get(f"{API_URL}/jobs/{job_id}")
            job_data = job_res.json()
            
            if job_data["status"] == "COMPLETED":
                result = job_data["result"]
                print(f"SQL: {result.get('sql', 'None')}")
                print(f"Answer: {result.get('answer')}")
                break
            elif job_data["status"] == "FAILED":
                print(f"Job failed: {job_data.get('error')}")
                break
                
            time.sleep(1)
            
        print(f"Time taken: {time.time() - start_time:.2f}s\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SchemaLens on a specific dataset")
    parser.add_argument("dataset_id", help="The ID of the dataset to evaluate against")
    args = parser.parse_args()
    evaluate(args.dataset_id)
