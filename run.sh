#!/bin/bash
# run.sh - Start the Voice Bot server and make test calls
set -e

echo "=== Voice Bot Runner ==="

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in credentials."
    exit 1
fi

# Check Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Start ngrok in the background
echo "Starting ngrok tunnel..."
ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 3

# Get the ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    for t in tunnels:
        if t.get('proto') == 'https':
            print(t['public_url'])
            break
    else:
        if tunnels:
            print(tunnels[0]['public_url'])
except:
    pass
" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "ERROR: Could not get ngrok URL. Is ngrok running?"
    echo "Try running ngrok manually: ngrok http 8000"
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

echo "Ngrok URL: $NGROK_URL"

# Update .env with ngrok URL
if grep -q "NGROK_URL=" .env; then
    sed -i '' "s|NGROK_URL=.*|NGROK_URL=$NGROK_URL|" .env
else
    echo "NGROK_URL=$NGROK_URL" >> .env
fi

echo "Starting FastAPI server..."
echo ""
echo "==================================="
echo "Server running at http://localhost:8000"
echo "Ngrok tunnel: $NGROK_URL"
echo "==================================="
echo ""
echo "To make test calls, open a new terminal and run:"
echo "  source venv/bin/activate"
echo "  python -m app.pipeline.run_test_suite --scenario schedule_new"
echo "  python -m app.pipeline.run_test_suite  # Run all scenarios"
echo ""

# Trap to clean up ngrok on exit
cleanup() {
    echo "Shutting down..."
    kill $NGROK_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# Start the server (foreground)
uvicorn app.main:app --host 0.0.0.0 --port 8000
