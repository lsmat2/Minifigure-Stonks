#!/bin/bash
# Stop Minifigure-Stonks network services

echo "🛑 Stopping Minifigure-Stonks services..."

# Kill by PID files if they exist
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "✓ Stopped backend (PID: $BACKEND_PID)"
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "✓ Stopped frontend (PID: $FRONTEND_PID)"
    rm .frontend.pid
fi

# Fallback: kill by port
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9
    echo "✓ Stopped process on port 8000"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    lsof -ti:3000 | xargs kill -9
    echo "✓ Stopped process on port 3000"
fi

echo "✅ All services stopped"
