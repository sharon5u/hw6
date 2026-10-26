#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Run the setup commands in README.md first."
  exit 1
fi
echo "Open http://127.0.0.1:8000 in your browser once the server is ready."
exec .venv/bin/python web_app.py
