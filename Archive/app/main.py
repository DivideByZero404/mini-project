import os
import sys
import json
import re
import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
from dotenv import load_dotenv

# Guard against running on Python 3.14+ where httpx/httpcore may be incompatible
# if sys.version_info >= (3, 14):
#     raise RuntimeError(
#         'Detected Python 3.14+. httpx/httpcore have known incompatibilities with Python 3.14. '
#         'Please use Python 3.11–3.13. Recreate your virtualenv with a supported Python and reinstall requirements.'
#     )

try:
    from app.ollama_client import generate, extract_sql
except ModuleNotFoundError:
    # When running `python app/main.py` the package name `app` may not be importable;
    # import the local module directly as a fallback.
    from ollama_client import generate, extract_sql

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL',"postgresql://postgres:postgres@localhost:5432/chatbot")
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b-instruct-q4_0')

app = FastAPI(title='nl-to-sql-chatbot')

# Add CORS middleware to allow cross-origin requests from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class QueryRequest(BaseModel):
    nl: str


class QueryResponse(BaseModel):
    sql: str
    rows: Any
    summary: str


POOL: asyncpg.pool.Pool | None = None


@app.on_event('startup')
async def startup():
    global POOL
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL not set')
    POOL = await asyncpg.create_pool(DATABASE_URL)


@app.on_event('shutdown')
async def shutdown():
    global POOL
    if POOL:
        await POOL.close()


def build_schema_description() -> str:
    # Simple inline schema description used in prompts — keep in sync with db/init.sql
    return (
        'Tables:\n'
        '- categories(id, name)\n'
        '- products(id, name, category_id)\n'
        '- customers(id, name, location)\n'
        '- purchases(id, customer_id, product_id, unit_price, total_price)\n'
    )


async def ask_model_to_generate_sql(nl: str, context_schema: str) -> str:
    prompt = (
        'You are given a Postgres database with schema:\n'
        f'{context_schema}\n'
        'Translate the user natural language request into a single valid SQL SELECT query for Postgres. '
        'Only output the SQL. Do not add explanation or commentary. Use proper SQL that works with the schema. '\
        f'User request: {nl}'
    )
    resp = await generate(prompt, model=OLLAMA_MODEL)
    print('Model response:', resp)
    sql = extract_sql(resp)
    return sql


async def ask_model_to_fix_sql(nl: str, bad_sql: str, error_msg: str, context_schema: str) -> str:
    prompt = (
        'A SQL query you generated failed when executed on Postgres.\n'
        f'Schema:\n{context_schema}\n'
        f'Original user request: {nl}\n'
        f'Previous SQL: {bad_sql}\n'
        f'Error message: {error_msg}\n'
        'Please provide a corrected SQL SELECT query only. No explanation.'
    )
    resp = await generate(prompt, model=OLLAMA_MODEL)
    return extract_sql(resp)


async def ask_model_to_summarize(nl: str, rows: list[dict]) -> str:
    prompt = (
        'Given the following query result rows as JSON and the original user request, write a concise natural-language summary of the results.\n'
        f'User request: {nl}\n'
        f'Results JSON: {json.dumps(rows, default=str)}\n'
        'Provide a short summary.'
    )
    resp = await generate(prompt, model=OLLAMA_MODEL)
    return resp.strip()


def looks_like_select(sql: str) -> bool:
    if not sql:
        return False
    s = sql.strip().lower()
    return s.startswith('select')


@app.post('/query', response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    global POOL
    if POOL is None:
        raise HTTPException(status_code=500, detail='DB pool not initialized')

    schema = build_schema_description()
    sql = await ask_model_to_generate_sql(req.nl, schema)
    if not sql:
        raise HTTPException(status_code=400, detail='Model did not return SQL')

    if not looks_like_select(sql):
        raise HTTPException(status_code=400, detail='Only SELECT queries are allowed')

    async with POOL.acquire() as conn:
        try:
            rows = await conn.fetch(sql)
            # convert Record -> dicts
            print('Query executed successfully:', rows)
            rows_json = [dict(r) for r in rows]
        except Exception as e:
            # try to ask model to fix SQL once
            fixed_sql = await ask_model_to_fix_sql(req.nl, sql, str(e), schema)
            if not fixed_sql or not looks_like_select(fixed_sql):
                raise HTTPException(status_code=400, detail=f'SQL execution error: {e}')
            try:
                rows = await conn.fetch(fixed_sql)
                rows_json = [dict(r) for r in rows]
                sql = fixed_sql
            except Exception as e2:
                raise HTTPException(status_code=400, detail=f'SQL execution error after fix: {e2}')

    summary = await ask_model_to_summarize(req.nl, rows_json)
    print('Summary generated:', summary)
    return QueryResponse(sql=sql, rows=rows_json, summary=summary)


if __name__ == '__main__':
    import uvicorn
    import sys
    import os

    # Ensure the project root (parent of this `app` package) is on sys.path so
    # the import string `app.main:app` can be imported by the reloader process.
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    if sys.path[0] == here:
        sys.path[0] = root

    # Pass import string to enable reload/workers as required by uvicorn.
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
