import pytest
from llm.agent import DataAgent

def test_format_schema_context():
    schema_info = {
        "table_name": "transactions",
        "columns": [
            {"column_name": "id", "data_type": "INTEGER"},
            {"column_name": "name", "data_type": "VARCHAR"}
        ],
        "sample_data": [
            {"id": 1, "name": "Test"},
            {"id": 2, "name": "Product"}
        ]
    }
    
    # We can mock the LLM or just avoid calling answer()
    agent = DataAgent(dataset_id="test_ds", schema_info=schema_info)
    
    context = agent._format_schema_context()
    
    assert "Table name: transactions" in context
    assert "id (INTEGER)" in context
    assert "name (VARCHAR)" in context
    assert "Test" in context
