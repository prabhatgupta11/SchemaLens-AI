# SchemaLens: Natural Language Insights Engine

SchemaLens is a full-stack asynchronous application that allows users to upload unseen transactional CSV datasets and query them using plain English.

## Features
- **Upload any CSV**: Automatically infers schemas and loads data into a queryable DuckDB analytics engine. No code changes required for new datasets.
- **Asynchronous Processing**: Both ingestion and querying are handled asynchronously by a Celery task queue, ensuring the API and caller are never blocked.
- **Natural Language to SQL**: Powered by OpenAI's `gpt-4o` and LangChain, questions are translated to DuckDB SQL, safely executed, and summarized back into natural English.
- **Guardrails**: Safely refuses to answer questions that cannot be determined from the provided dataset.
- **Premium UI**: A sleek, dynamic React interface built with Tailwind CSS and Vite.

## Quick Start (One-Command Setup)

### Prerequisites
- Docker and Docker Compose
- An OpenAI API Key

### Setup
1. Clone the repository and navigate into it:
   ```bash
   git clone <repo-url> SchemaLens
   cd SchemaLens
   ```
2. Setup environment variables:
   ```bash
   make setup
   ```
   *This will create a `.env` file. Please open it and add your `OPENAI_API_KEY`.*
3. Start the application:
   ```bash
   make up
   ```

### Usage
- The Frontend UI will be available at [http://localhost:5173](http://localhost:5173).
- The Backend API is available at [http://localhost:8000/api](http://localhost:8000/api).

Upload a CSV file using the UI sidebar. Once processed, type your question in the chat bar!

### Evaluation
Once you have uploaded a dataset and obtained its ID (you can inspect the network tab or the sqlite database in `data/metadata.db`), you can run the evaluation script:
```bash
python evaluate.py <dataset_id>
```

### Testing
Run the backend test suite inside the docker container:
```bash
make test
```
