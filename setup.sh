#!/bin/bash
# setup.sh - One-time setup for the Voice Bot
set -e

echo "=== Voice Bot Setup ==="

# Check Python
echo "Checking Python..."
python3 --version || { echo "ERROR: Python 3 not found"; exit 1; }

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    brew install ffmpeg
else
    echo "ffmpeg found: $(ffmpeg -version 2>&1 | head -1)"
fi

# Check ngrok
if ! command -v ngrok &> /dev/null; then
    echo "Installing ngrok..."
    brew install ngrok
else
    echo "ngrok found"
fi

# Check ngrok auth token
if ! ngrok config check > /dev/null 2>&1; then
    echo ""
    echo "WARNING: ngrok requires an auth token (free)."
    echo "  1. Sign up at https://dashboard.ngrok.com/signup"
    echo "  2. Get your token at https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "  3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
fi

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "WARNING: Ollama not found. Install from https://ollama.com"
    echo "Then run: ollama pull llama3"
else
    echo "Ollama found"
    # Ensure llama3 is available
    if ! ollama list | grep -q "llama3"; then
        echo "Pulling llama3 model..."
        ollama pull llama3
    else
        echo "llama3 model available"
    fi
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

# Create output directories
mkdir -p output/transcripts output/reports

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env with your Twilio credentials:"
    echo "  TWILIO_ACCOUNT_SID=your_sid"
    echo "  TWILIO_AUTH_TOKEN=your_token"
    echo "  TWILIO_FROM_NUMBER=+1XXXXXXXXXX"
    echo ""
fi

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "  1. Edit .env with your Twilio credentials"
echo "  2. Start Ollama: ollama serve"
echo "  3. Run: ./run.sh"
