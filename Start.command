#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Run the setup commands in README.md first."
  exit 1
fi
exec .venv/bin/python app.py
