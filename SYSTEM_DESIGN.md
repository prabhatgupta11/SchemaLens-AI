# SchemaLens System Design

This document details the architecture, design decisions, and future extensions of the SchemaLens Natural Language Insights Engine.

## Architecture Diagram

*(Since this is a text-based repository, here is a Mermaid representation of the architecture)*

```mermaid
graph TD
    User([User]) -->|HTTP (React)| UI[Frontend UI]
    UI -->|REST API| API[FastAPI Backend]
    
    API -->|Write metadata| SQLite[(SQLite Metadata DB)]
    API -->|Publish Job| RedisBroker[(Redis Broker)]
    
    RedisBroker -->|Consume Job| Worker[Celery Worker]
    
    Worker -->|Read/Write schema status| SQLite
    Worker -->|Ingest / Query| DuckDB[(DuckDB Analytics)]
    Worker <-->|NL to SQL via Prompting| LLM[OpenAI API GPT-4o]
```

## Component Ownership

1. **Frontend (React/Vite)**
   - Responsible for presentation, handling file uploads, maintaining conversation state, and polling the backend for async job status.

2. **Backend API (FastAPI)**
   - Provides a clean HTTP interface. Owns validation, creation of job IDs, saving temporary files, and persisting job states to SQLite.
   - Decoupled from heavy processing to ensure it never blocks incoming requests.

3. **Task Queue & Worker (Celery + Redis)**
   - Manages asynchronous, long-running tasks: CSV ingestion and LLM querying.
   - Ensures robustness under concurrent load. If a query takes 30 seconds or the LLM rate limits, the queue handles it without dropping requests.

4. **Analytics Engine (DuckDB)**
   - Owns the transactional data. duckdb is an in-process, high-performance SQL OLAP database.

5. **LLM Agent (LangChain + OpenAI)**
   - Owns prompt construction, context injection (schema + samples), and response parsing. Translates English -> SQL -> English.

## The Path of a Question

1. **Input**: User submits "Top 10 products by revenue".
2. **API Layer**: API creates a `Job` record in SQLite (status `PENDING`), pushes `answer_question` to Redis, and returns `job_id=123`.
3. **Queueing**: The UI starts polling `GET /jobs/123`.
4. **Processing**: Celery worker picks up the job, marks it `PROCESSING`.
5. **Context Building**: Worker fetches the dataset's inferred schema from SQLite.
6. **SQL Generation**: The LLM Agent injects the schema into a prompt and asks GPT-4o for a raw SQL query.
7. **Execution**: The generated SQL is executed safely against the specific dataset's DuckDB file in `read_only=True` mode.
8. **Summarization**: The raw JSON results and the question are fed back to the LLM to generate a natural English answer.
9. **Fulfillment**: Worker updates the SQLite job to `COMPLETED` with the answer. The polling UI receives the final payload.

## Handling Unseen Schemas

When a new CSV is uploaded, DuckDB's `read_csv_auto` is used to load it. DuckDB aggressively samples the file to infer column names and data types (e.g., BIGINT, VARCHAR, TIMESTAMP). 
The backend then queries `PRAGMA table_info()` to extract this schema and saves it as JSON in SQLite.
**Where it breaks:** 
- If column names contain heavily ambiguous or encoded names (e.g., `col_01`, `x_fact`), the LLM will struggle to map "revenue" to `col_01` without a semantic layer or data dictionary.
- If dates are in highly non-standard formats that DuckDB fails to parse, they may be loaded as `VARCHAR`, which breaks time-series SQL generation unless the LLM dynamically casts them.

## Biggest Decisions & Alternatives

1. **DuckDB vs PostgreSQL vs Pandas**
   - *Decision:* DuckDB.
   - *Why:* We needed a way to dynamically ingest arbitrary CSVs and execute complex analytic SQL quickly. Pandas cannot natively execute SQL without heavy abstraction layers, and spinning up a new PostgreSQL database per dataset (or handling schema separation) is overly complex. DuckDB provides massive analytical performance while remaining embedded and serverless.
   
2. **Celery/Redis vs asyncio.BackgroundTasks**
   - *Decision:* Celery + Redis.
   - *Why:* The PRD required explicit handling of concurrent load and partial failures. FastAPI's `BackgroundTasks` run in the same event loop memory space; if the API server crashes, all running jobs are lost. Celery provides a durable queue, automatic retries, and allows workers to scale horizontally on separate machines.

3. **Separate DuckDB Files per Dataset vs Single File**
   - *Decision:* Separate `dataset_{id}.duckdb` files.
   - *Why:* DuckDB currently only allows one process to hold a write lock on a file. By isolating datasets into their own files, multiple Celery workers can ingest different datasets completely concurrently without locking contention.

4. **Direct Prompting vs Agentic Loops (ReAct)**
   - *Decision:* Direct 2-step prompting (NL -> SQL -> Execute -> Summarize).
   - *Why:* Agentic loops (where the LLM decides when to execute queries and can self-correct) are powerful but slow and prone to infinite loops. For a straightforward schema, generating SQL in a single zero-shot pass with `gpt-4o` is highly reliable, faster, and much cheaper.

## Next Steps (What I would build next)

1. **Semantic Layer / Data Dictionary Extraction**: Run an LLM pass over the schema *during ingestion* to generate a human-readable description for each column. This would vastly improve query accuracy on obscure column names.
2. **Self-Correction Loop**: If DuckDB throws a syntax error on the generated SQL, feed the error back to the LLM once to allow it to fix the syntax.
3. **Caching**: Cache exact string matches of questions for a specific dataset to return instant answers and save LLM costs.
4. **Streaming Answers**: Use WebSockets or Server-Sent Events (SSE) instead of HTTP polling to reduce latency and stream the LLM summary back token-by-token.
5. **Data Visualization**: Have the LLM output a Chart.js/Recharts configuration object alongside the answer to automatically render bar charts or line graphs for time-series questions.
