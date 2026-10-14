# AI-Powered RAG Service

A Retrieval-Augmented Generation (RAG) service built with Python and FastAPI that enables context-aware question answering over uploaded PDF documents. The service combines document processing, text chunking, semantic embeddings, vector similarity search, and large language model inference.

## Features

- **PDF Processing:** Extracts text from uploaded PDF documents.
- **Text Chunking:** Splits documents into smaller chunks for retrieval.
- **Semantic Embeddings:** Generates vector embeddings using Sentence Transformers.
- **Vector Search:** Uses PostgreSQL and pgvector for similarity-based document retrieval.
- **AI-Powered Question Answering:** Uses retrieved document context to generate relevant answers with an LLM.
- **JWT Authentication:** Protects endpoints using bearer tokens.
- **Multi-Tenant Support:** Associates document operations with tenant identities.
- **Document Management:** Supports document ingestion and tenant-scoped retrieval and management.
- **REST API:** Provides endpoints through FastAPI.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- pgvector
- Sentence Transformers
- Hugging Face Transformers
- Qwen2.5-0.5B-Instruct
- PyMuPDF
- JWT authentication
- Uvicorn

## Architecture

```text
Client
  |
  v
Spring Boot Backend
  |
  | JWT Authorization
  v
Python FastAPI RAG Service
  |
  |-- PDF text extraction
  |-- Text chunking
  |-- Embedding generation
  |-- Semantic retrieval
  |-- LLM answer generation
  |
  v
PostgreSQL + pgvector
  |
  v
Context-aware answer
```

## Prerequisites

- Python 3
- PostgreSQL
- The pgvector PostgreSQL extension
- A compatible environment for loading the configured embedding and language models
- The Spring Boot backend for the integrated application

## Installation

Clone the repository:

```bash
git clone https://github.com/naveenvijaykumar5573-star/rag-service.git
cd rag-service
```

Create and activate a virtual environment on Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Environment Configuration

Create a local `.env` file and configure your database connection and JWT settings.

Example configuration:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_local_database_password
JWT_SECRET=your_generated_secret
JWT_ALGORITHM=HS256
```

Replace the example values with your local configuration. The JWT secret must match the secret used by the Spring Boot backend.

**Security:** Never commit `.env` files, database passwords, JWT secrets, uploaded documents, or other private data.

## Run the Service

Start the FastAPI application from the project root:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The service will be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

## API Overview

The service includes endpoints for:

- Health or root information
- Asking questions using retrieved document context
- Uploading PDF documents
- Listing and retrieving documents
- Deleting documents

Protected endpoints require a valid JWT bearer token. See the FastAPI interactive documentation for the exact request schemas and available routes.

## Testing

Run the automated tests with:

```bash
python -m pytest
```

The repository includes authentication and RAG quality test modules.

## Related Repository

**Spring Boot Backend:** [rag-backend](https://github.com/naveenvijaykumar5573-star/rag-backend)

The Spring Boot service handles application authentication and API orchestration, while this Python service performs document processing, retrieval, and LLM inference.

## Future Improvements

- Improve retrieval and response latency
- Expand automated integration and security testing
- Add monitoring and structured logging
- Containerize the services with Docker
- Improve evaluation of retrieval relevance and answer quality

## Author

Naveen V

[GitHub Profile](https://github.com/naveenvijaykumar5573-star)
