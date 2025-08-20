#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
MAIN_SCRIPT="$PROJECT_DIR/main.py"

echo "🚀 Doc-Crawler Launcher"
echo "========================"

cd "$PROJECT_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

if [ ! -f "$VENV_DIR/requirements_installed.flag" ]; then
    echo "📋 Installing requirements..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    touch "$VENV_DIR/requirements_installed.flag"
    echo "✅ Requirements installed"
else
    echo "✅ Requirements already installed"
fi

echo "🏃 Launching Doc-Crawler..."
echo ""

python "$MAIN_SCRIPT"