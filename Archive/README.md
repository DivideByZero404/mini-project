# Chatbot NL→SQL (LangGraph-style) — Example

This project is a minimal prototype that accepts a natural-language query, uses an Ollama Llama model to generate SQL for a simple Postgres schema, executes the SQL, and asks the model to summarize the results.

Prerequisites
- Docker & Docker Compose (to run Postgres)
- Python 3.11–3.13 (recommended). Python 3.14+ may be incompatible with `httpx`/`httpcore`.
- Ollama installed and available either as an HTTP API or CLI on the machine

Quick start

1. Copy `.env.example` to `.env` and adjust if needed.
2. Start the database:

```bash
docker-compose up -d
```

3. Install Python deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Run the app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Example request:

```bash
curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{"nl":"List product names and total purchases for category 'Electronics'"}'
```

Notes
- The app expects an Ollama endpoint configured via `OLLAMA_API_URL` or `ollama` available on the PATH for a CLI fallback. Adjust `OLLAMA_MODEL` in `.env` to pick the model.
- For safety this prototype restricts generated SQL to `SELECT` statements only.
