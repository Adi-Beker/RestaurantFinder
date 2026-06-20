#!/usr/bin/env bash
set -e

echo "======================================"
echo "Restaurant Finder – Local Demo Script"
echo "======================================"
echo

echo "[1/7] Start the full stack:"
echo "  docker compose up --build"
echo
echo "After the stack is healthy, open:"
echo "  Frontend:   http://localhost:5173"
echo "  API docs:   http://localhost:8000/docs"
echo "  AI service: http://localhost:8001/health"
echo

echo "[2/7] Register a new user in the frontend"
echo "  - Open http://localhost:5173"
echo "  - Click Register"
echo "  - Create a new account"
echo

echo "[3/7] Explore the Discover page"
echo "  - Browse restaurants by city"
echo "  - Try switching between cities"
echo "  - Use search and cuisine filters"
echo

echo "[4/7] Add restaurants to My Visited"
echo "  - Add one or more restaurants from Discover"
echo "  - Open My Visited"
echo "  - Verify create / edit / delete flow"
echo

echo "[5/7] Test AI Recommendation"
echo "  - Click 'Get AI Recommendation'"
echo "  - Verify the restaurant comes from the Israeli discover catalogue"
echo "  - Click 'Ask again' and verify a different recommendation appears"
echo

echo "[6/7] Test Analyze My Dining Summary"
echo "  - Click 'Analyze My Dining Summary'"
echo "  - Wait for the background job to complete"
echo "  - Verify the summary panel appears"
echo

echo "[7/7] Test Profile and Change Password"
echo "  - Open Profile"
echo "  - Verify account info is shown"
echo "  - Change the password"
echo "  - Log out and log back in with the new password"
echo

echo "======================================"
echo "Optional verification commands"
echo "======================================"
echo
echo "Run backend tests:"
echo "  uv run pytest -v"
echo
echo "Run frontend build:"
echo "  cd frontend && npm run build"
echo
echo "Run discover ingest script:"
echo "  uv run python -m scripts.ingest_discover"
echo
echo "Run refresh script:"
echo "  uv run python -m scripts.refresh --url http://localhost:8000 --token <your_token>"
echo

echo "======================================"
echo "Demo checklist complete"
echo "======================================"
