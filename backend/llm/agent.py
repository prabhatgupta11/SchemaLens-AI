from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from core.config import settings
from analytics.engine import AnalyticsEngine
import json

class DataAgent:
    def __init__(self, dataset_id: str, schema_info: dict):
        self.dataset_id = dataset_id
        self.schema_info = schema_info
        self.engine = AnalyticsEngine(dataset_id=dataset_id)
        # Using gpt-4o for best SQL generation capabilities
        self.llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o", temperature=0)
        
    def _format_schema_context(self):
        context = f"Table name: {self.schema_info['table_name']}\n"
        context += "Columns:\n"
        for col in self.schema_info['columns']:
            context += f"- {col['column_name']} ({col['data_type']})\n"
        context += "\nSample Data (first 3 rows):\n"
        context += json.dumps(self.schema_info.get('sample_data', []), indent=2)
        return context

    def generate_sql(self, question: str):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a DuckDB SQL expert. Your job is to translate a user's natural language question into a DuckDB SQL query based on the provided database schema.

CRITICAL RULES:
1. ONLY return the raw SQL query. Do not wrap it in markdown code blocks like ```sql ... ```. No explanations.
2. If the question cannot be answered using the provided schema, return the exact string: "UNANSWERABLE". Do not try to guess or invent tables/columns.
3. The table name is '{table_name}'.
4. Always handle potential NULLs or messy data if the question implies it.

Schema Context:
{schema_context}"""),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "table_name": self.schema_info['table_name'],
            "schema_context": self._format_schema_context(),
            "question": question
        })
        
        sql = response.content.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        return sql.strip()

    def generate_answer(self, question: str, sql: str, results: list):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data analyst. You are given a user's question, the SQL query used to find the answer, and the raw JSON results from the database.
Your job is to provide a clear, concise, and accurate answer in plain English.

CRITICAL RULES:
1. Base your answer ONLY on the provided results. Do not invent data.
2. If the result is empty or indicates no data found, say so.
3. Keep the answer professional and easy to understand for business users.
"""),
            ("human", "Question: {question}\n\nSQL Query:\n{sql}\n\nResults:\n{results}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "question": question,
            "sql": sql,
            "results": json.dumps(results, indent=2)
        })
        
        return response.content.strip()

    def answer(self, question: str):
        sql = self.generate_sql(question)
        
        if sql == "UNANSWERABLE":
            return {
                "answer": "I'm sorry, I cannot answer this question based on the provided data schema.",
                "sql": None,
                "data": None
            }
            
        try:
            results = self.engine.execute_query(sql)
            answer_text = self.generate_answer(question, sql, results)
            
            return {
                "answer": answer_text,
                "sql": sql,
                "data": results
            }
        except Exception as e:
            return {
                "answer": f"I tried to answer the question, but the generated SQL query failed: {str(e)}",
                "sql": sql,
                "data": None,
                "error": str(e)
            }
