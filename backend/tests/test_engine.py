import pytest
import os
import duckdb
from analytics.engine import AnalyticsEngine

def test_ingest_and_query():
    # Setup test file
    csv_content = """id,name,value
1,Test A,10.5
2,Test B,20.5
"""
    test_csv = "test_engine_data.csv"
    with open(test_csv, "w") as f:
        f.write(csv_content)
        
    engine = AnalyticsEngine(dataset_id="test_engine_1")
    
    try:
        # Test ingestion
        schema_info = engine.ingest_csv(test_csv, table_name="test_table")
        assert schema_info["table_name"] == "test_table"
        
        # Verify schema is correctly inferred
        columns = {col["column_name"]: col["data_type"] for col in schema_info["columns"]}
        assert "id" in columns
        assert "name" in columns
        assert "value" in columns
        assert len(schema_info["sample_data"]) == 2
        
        # Test querying
        results = engine.execute_query("SELECT SUM(value) as total FROM test_table")
        assert len(results) == 1
        assert results[0]["total"] == 31.0
        
    finally:
        # Cleanup
        if os.path.exists(test_csv):
            os.remove(test_csv)
        if os.path.exists(engine.db_path):
            os.remove(engine.db_path)
