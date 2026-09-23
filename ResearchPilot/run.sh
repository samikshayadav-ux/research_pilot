#!/usr/bin/env bash
# ResearchPilot AI — quick start
set -e

cd "$(dirname "$0")"

echo "📦  Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🚀  Starting ResearchPilot AI at http://localhost:5001"
echo "    Demo mode is active by default — no IBM credentials required."
echo "    To enable IBM Granite AI generation:"
echo "      cp .env.example .env"
echo "      # Edit .env with your WATSONX_API_KEY and WATSONX_PROJECT_ID"
echo ""
echo "    Press Ctrl+C to stop."
echo ""

PORT=5001 python app.py
