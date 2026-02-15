import os
import asyncio
import subprocess
import sys
import re
import json
from typing import Optional

OLLAMA_API_URL = os.getenv('OLLAMA_API_URL',"http://localhost:11434")
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b-instruct-q4_0')
OLLAMA_CLI = os.getenv('OLLAMA_CLI', 'false').lower() in ('1', 'true', 'yes')

# Force CLI mode on Python 3.14+ due to httpx/httpcore incompatibility
if sys.version_info >= (3, 14):
    OLLAMA_CLI = True


async def generate(prompt: str, model: Optional[str] = None) -> str:
    """Try HTTP Ollama API first, fall back to CLI if configured.

    HTTP client imports are done lazily to avoid importing `httpx` on Python
    versions where it's incompatible (e.g., Python 3.14). On Python 3.14+, CLI is
    automatically enabled.
    """
    model = model or OLLAMA_MODEL

    if OLLAMA_API_URL:
        url = OLLAMA_API_URL.rstrip('/') + '/api/generate'
        try:
            import httpx
            use_httpx = True
        except Exception:
            try:
                import requests
                import asyncio
                use_httpx = False
            except Exception:
                # no HTTP client available
                pass
            else:
                def post(url, json_data):
                    def post_sync(url, json_data):
                        resp = requests.post(url, json=json_data, stream=True, timeout=120)
                        resp.raise_for_status()
                        full_response = ""
                        for line in resp.iter_lines():
                            if line:
                                try:
                                    data = json.loads(line.decode('utf-8'))
                                    full_response += data.get('response', '')
                                    if data.get('done'):
                                        break
                                except (json.JSONDecodeError, UnicodeDecodeError):
                                    pass
                        return {'response': full_response}
                    return asyncio.to_thread(post_sync, url, json_data)
        else:
            def post(url, json_data):
                async def post_async(url, json_data):
                    async with httpx.AsyncClient(timeout=120) as client:
                        async with client.stream('POST', url, json=json_data) as resp:
                            resp.raise_for_status()
                            full_response = ""
                            async for line in resp.aiter_lines():
                                if line.strip():
                                    try:
                                        data = json.loads(line)
                                        full_response += data.get('response', '')
                                        if data.get('done'):
                                            break
                                    except json.JSONDecodeError:
                                        pass
                            return {'response': full_response}
                return post_async(url, json_data)

        if 'post' in locals():
            try:
                data = await post(url, {"model": model, "prompt": prompt})
                return data.get('response') or data.get('content') or data.get('text') or str(data)
            except Exception:
                # fall through to CLI fallback
                pass

    if OLLAMA_CLI:
        # best-effort CLI fallback
        try:
            proc = await asyncio.create_subprocess_exec(
                'ollama', 'generate', model, '--prompt', prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await proc.communicate()
            if out:
                return out.decode('utf-8')
            if err:
                return err.decode('utf-8')
        except FileNotFoundError:
            raise RuntimeError('Ollama HTTP API not reachable and ollama CLI not found')

    raise RuntimeError('Ollama API not configured (set OLLAMA_API_URL) or OLLAMA_CLI=true')


def extract_sql(text: str) -> str:
    """Naive extraction of SQL from model text. Handles ```sql blocks or plain SQL."""
    if not text:
        return ''
    t = text.strip()
    # handle ```sql ... ```
    if '```' in t:
        parts = t.split('```')
        # find block that contains sql or looks like it
        for p in parts:
            if p.strip().lower().startswith('sql'):
                # remove leading 'sql' if present
                return '\n'.join(p.splitlines()[1:]).strip()
        # otherwise return the longest block
        candidate = max(parts, key=lambda s: len(s))
        return candidate.strip()
    # try to find SELECT statement
    match = re.search(r'SELECT.*?;', t, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(0).strip()
    # otherwise return full text
    return t
