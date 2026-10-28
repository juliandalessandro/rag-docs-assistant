
# RAG Docs Assistant

A document retrieval API built with Python, FastAPI, PostgreSQL, and pgvector. The project implements the retrieval component of a Retrieval-Augmented Generation (RAG) pipeline, allowing users to upload text documents, split them into smaller chunks, generate vector embeddings, and retrieve relevant content through semantic search.

## Overview

RAG Docs Assistant is a backend project designed to explore the core building blocks of a RAG system.

Instead of searching for exact keywords, the API converts document chunks and user queries into vector embeddings and compares them using cosine distance. This allows the system to retrieve text based on semantic similarity.

The current implementation focuses on document ingestion, chunking, embedding generation, vector storage, and retrieval. It does not yet generate answers using a Large Language Model (LLM).

## Features

- Upload and store plain-text (`.txt`) documents.
- Split documents into overlapping chunks.
- Generate 384-dimensional embeddings using a local Sentence Transformers model.
- Store document chunks and embeddings in PostgreSQL with pgvector.
- Perform semantic search using cosine distance.
- Optionally filter search results by maximum cosine distance.
- Validate API inputs and uploaded files.
- Run automated tests against a separate test database.


## Tech Stack

- **Language:** Python 3.13
- **API Framework:** FastAPI
- **Database:** PostgreSQL
- **Vector Search:** pgvector
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`)
- **Database Driver:** Psycopg 3
- **Configuration:** python-dotenv
- **Testing:** pytest and HTTPX
- **Infrastructure:** Docker Compose


## Project Structure

```text

rag-docs-assistant/
|-- app/
|   |-- main.py
|   |-- database.py
|   |-- embeddings.py
|   |-- chunking.py
|   |-- chunks.py
|   |-- processing.py
|   `-- search.py
|-- sample_documents/
|   `-- rag-test.txt
|-- sql/
|   `-- init.sql
|-- tests/
|   |-- conftest.py
|   |-- test_chunking.py
|   |-- test_chunks.py
|   |-- test_main.py
|   `-- test_search.py
|-- .env.example
|-- .gitignore
|-- compose.yaml
|-- requirements.txt
`-- README.md
```


## Prerequisites

Before running the project, make sure you have installed:

- Python 3.13 or a compatible version.
- Docker Desktop with Docker Compose.
- Git.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/juliandalessandro/rag-docs-assistant.git
cd rag-docs-assistant
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

The `.env` file contains the database connection settings. The example configuration is intended for local development only.

### 5. Start PostgreSQL with pgvector

Make sure Docker Desktop is running, then execute:

```powershell
docker compose up -d db
```

### 6. Initialize the database schema

Apply the SQL schema to the main database:

```powershell
Get-Content -Raw .\sql\init.sql | docker compose exec -T db psql -U rag_user -d rag_docs
```

For a fresh setup, create the test database:

```powershell
docker compose exec db psql -U rag_user -d postgres -c "CREATE DATABASE rag_docs_test;"
```

Initialize its schema as well:

```powershell
Get-Content -Raw .\sql\init.sql | docker compose exec -T db psql -U rag_user -d rag_docs_test
```

The test suite uses `rag_docs_test` to keep automated tests separate from the main development database.



## Running the API

From the project root, activate the virtual environment and start the development server:

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

- **API base URL:** http://127.0.0.1:8000
- **Interactive API documentation (Swagger UI):** http://127.0.0.1:8000/docs
- **Alternative API documentation (ReDoc):** http://127.0.0.1:8000/redoc

The interactive documentation allows you to explore the available endpoints and send requests directly from your browser.




## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check whether the API is running. |
| GET | `/health/db` | Check database connectivity. |
| POST | `/documents` | Create a document from text content. |
| POST | `/documents/upload` | Upload and process a `.txt` file. |
| GET | `/documents` | List stored documents. |
| GET | `/documents/{id}` | Retrieve a document by ID. |
| GET | `/search` | Search for semantically similar document chunks. |

### Semantic Search Example

Search for content related to the question "What database stores the documents?":

```http
GET /search?q=What%20database%20stores%20the%20documents&limit=5
```

You can also set a maximum cosine distance to filter out less similar results:

```http
GET /search?q=database&limit=5&max_distance=0.5
```

The search endpoint returns matching document chunks ordered by cosine distance. Lower distances indicate greater similarity.



## Running Tests

The project uses pytest and HTTPX for automated testing.

Make sure Docker is running and both databases have been initialized before running the test suite.

Run all tests:

```powershell
pytest
```

Run tests for a specific module:

```powershell
pytest tests/test_chunking.py
pytest tests/test_chunks.py
pytest tests/test_main.py
pytest tests/test_search.py
```

The test suite covers text chunking, embedding persistence, API endpoints, input validation, and semantic search.

Tests use a dedicated `rag_docs_test` database to avoid modifying data in the main development database.

## Sample Document

A sample text file is available at `sample_documents/rag-test.txt`. It can be used to test document ingestion and semantic search through the API.

## Future Improvements

Potential next steps include:

- Integrate a Large Language Model (LLM) to generate answers from retrieved context.
- Add document deletion and update operations.
- Introduce database migrations.
- Explore hybrid search combining semantic and keyword-based retrieval.
- Evaluate retrieval quality using a dedicated evaluation dataset.
- Add authentication and prepare the application for deployment.
