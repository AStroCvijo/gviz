#!/bin/bash
# setup.sh — install all gviz components and start the Django dev server.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
# Prerequisites:
#   - Python 3.9+ available as 'python' or 'python3'
#   - pip available

set -e  # exit on first error

# ---------------------------------------------------------------------------
# Locate Python
# ---------------------------------------------------------------------------
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "ERROR: Python not found. Install Python 3.9+ and re-run." >&2
    exit 1
fi

echo "Using Python: $($PYTHON --version)"

# ---------------------------------------------------------------------------
# Create / activate virtual environment
# ---------------------------------------------------------------------------
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR ..."
    $PYTHON -m venv "$VENV_DIR"
fi

# Activate (works on Linux/macOS; on Windows use .venv\Scripts\activate)
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Activated venv: $(which python)"

# ---------------------------------------------------------------------------
# Upgrade pip
# ---------------------------------------------------------------------------
pip install --upgrade pip --quiet

# ---------------------------------------------------------------------------
# Install Django and other third-party dependencies
# ---------------------------------------------------------------------------
echo "Installing third-party dependencies ..."
pip install -r requirements.txt --quiet

# ---------------------------------------------------------------------------
# Install gviz components (order matters: api first, then platform, then plugins)
# ---------------------------------------------------------------------------
echo "Installing gviz-api ..."
pip install -e api/ --quiet

echo "Installing gviz-platform ..."
pip install -e platform/ --quiet

echo "Installing gviz-json-datasource ..."
pip install -e json_data_source/ --quiet

# ---------------------------------------------------------------------------
# Django setup
# ---------------------------------------------------------------------------
echo "Running Django migrations ..."
cd gviz/
python manage.py migrate --run-syncdb

# ---------------------------------------------------------------------------
# Start development server
# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "  gviz is ready!  Open http://127.0.0.1:8000"
echo "============================================"
python manage.py runserver
