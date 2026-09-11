import duckdb
import os
import json
from core.config import settings

class AnalyticsEngine:
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.db_path = f"/app/data/dataset_{dataset_id}.duckdb"
        # If not in docker, fallback to local path
        if not os.path.exists("/app/data"):
            os.makedirs("data", exist_ok=True)
            self.db_path = f"data/dataset_{dataset_id}.duckdb"

    def ingest_csv(self, file_path: str, table_name: str = "transactions"):
        """
        Loads a CSV file into DuckDB. DuckDB automatically infers the schema.
        Returns the inferred schema and a few sample rows to build context for the LLM.
        """
        conn = duckdb.connect(self.db_path)
        try:
            # Create table and load data using DuckDB's robust CSV reader
            query = f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}', sample_size=-1);"
            conn.execute(query)
            
            # Extract schema for the LLM
            schema_query = f"PRAGMA table_info('{table_name}');"
            schema_result = conn.execute(schema_query).fetchall()
            
            # Format schema: row[1] is name, row[2] is type
            schema = [{"column_name": row[1], "data_type": row[2]} for row in schema_result]
            
            # Get sample data to help LLM understand value formats
            sample_query = f"SELECT * FROM {table_name} LIMIT 3;"
            sample_result = conn.execute(sample_query).fetchdf().to_dict(orient="records")
            
            # Convert timestamp/date objects to string for JSON serialization
            for row in sample_result:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
            
            return {
                "table_name": table_name,
                "columns": schema,
                "sample_data": sample_result
            }
        finally:
            conn.close()

    def execute_query(self, query: str):
        """
        Executes a SQL query in read-only mode for safety.
        """
        conn = duckdb.connect(self.db_path, read_only=True)
        try:
            # Execute query and return results as dict
            df = conn.execute(query).fetchdf()
            # Handle NaN values for JSON serialization
            df = df.fillna("")
            result = df.to_dict(orient="records")
            
            # Convert complex objects to string for JSON serialization
            for row in result:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
            return result
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {str(e)}")
        finally:
            conn.close()
