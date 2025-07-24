#!/bin/bash

# Script to build and serve documentation locally for development

set -e

echo "📚 libCacheSim-python Documentation Builder"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "docs/mkdocs.yml" ]; then
    echo "❌ Error: mkdocs.yml not found. Please run this script from the project root."
    exit 1
fi

# Change to docs directory
cd docs

# Check if dependencies are installed
if ! python -c "import mkdocs_material, mkdocs_static_i18n" 2>/dev/null; then
    echo "🔧 Installing documentation dependencies..."
    pip install -r requirements.txt
else
    echo "🔧 Dependencies already installed"
fi

# Build documentation
echo "🏗️  Building documentation..."
python -m mkdocs build --clean --strict

# Check if serve flag is passed
if [ "$1" = "--serve" ] || [ "$1" = "-s" ]; then
    echo "🚀 Starting development server..."
    echo "📖 Documentation will be available at: http://127.0.0.1:8000"
    echo "🌐 English docs: http://127.0.0.1:8000/en/"
    echo "🌏 Chinese docs: http://127.0.0.1:8000/zh/"
    echo ""
    echo "Press Ctrl+C to stop the server"
    python -m mkdocs serve
else
    echo "✅ Documentation built successfully!"
    echo "📁 Output directory: docs/site/"
    echo ""
    echo "To serve locally, run:"
    echo "  ./scripts/build_docs.sh --serve"
    echo "  OR"
    echo "  cd docs && python -m mkdocs serve"
fi
