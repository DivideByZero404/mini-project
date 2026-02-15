# UV Project Configuration
# This project uses uv for dependency management
# https://docs.astral.sh/uv/

## Installation & Setup

### Using UV (recommended)

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create and activate virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Sync dependencies:
   ```bash
   uv sync
   ```

### Using Traditional pip

1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Start FastAPI Server
```bash
python app/main.py
```

### Open Web UI
Open `chatbot_ui.html` in your browser to interact with the chatbot.

### Start PostgreSQL Database
```bash
docker-compose up -d
```

### Access pgAdmin
- URL: http://localhost:5050
- Email: admin@test.com
- Password: admin

## Project Structure

```
chatbot-nl-sql/
├── app/                    # FastAPI application
│   ├── __init__.py
│   ├── main.py            # FastAPI app and endpoints
│   └── ollama_client.py    # Ollama integration
├── db/
│   └── init.sql           # Database schema and seed data
├── chatbot_ui.html        # Web UI for the chatbot
├── docker-compose.yml     # PostgreSQL setup
├── pyproject.toml         # UV project configuration
├── requirements.txt       # Traditional pip requirements
└── README.md
```

## Features

- Natural language queries converted to SQL
- Integration with Ollama for LLM inference
- PostgreSQL database backend
- RESTful API with FastAPI
- Web-based chat interface
- Python 3.14 compatibility with streaming responses

## API Endpoints

- **POST** `/query` - Submit a natural language query
  - Request: `{"nl": "Show me all products"}`
  - Response: `{"sql": "...", "rows": [...], "summary": "..."}`

## Database Tables

- **categories** - Product categories
- **products** - Product information with category links
- **purchases** - Purchase records
- **customers** - Customer information

## Environment Variables

See `.env.example` for required environment variables.

## Development

### Add New Dependencies
```bash
uv add package-name
```

### Update Dependencies
```bash
uv sync --upgrade
```

### Run Tests (if configured)
```bash
uv run pytest
```
