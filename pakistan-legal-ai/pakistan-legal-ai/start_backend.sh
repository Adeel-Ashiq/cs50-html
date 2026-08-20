#!/bin/bash
cd "$(dirname "$0")/backend"
export PYTHONPATH=.
echo "Starting Pakistan Legal AI Backend on http://localhost:8000"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
