#!/bin/bash
# UV Project Initialization Script

echo "🚀 Initializing UV project..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
uv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Sync dependencies
echo "📥 Syncing dependencies..."
uv sync

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env if needed"
echo "2. Start the FastAPI server: python app/main.py"
echo "3. Open chatbot_ui.html in your browser"
