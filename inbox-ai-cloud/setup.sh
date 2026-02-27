#!/bin/bash
# Setup script for Inbox AI Cloud
# Usage: ./setup.sh

echo "📬 Inbox AI Cloud - Setup"
echo "=========================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "✅ Python $PYTHON_VERSION found"

# Create directories
mkdir -p .state
echo "✅ State directory created"

# Check if accounts.json exists
if [ ! -f accounts.json ]; then
    echo ""
    echo "📝 Creating accounts.json from template..."
    cp accounts.json.example accounts.json
    echo "⚠️  Please edit accounts.json with your email credentials"
    echo ""
else
    echo "✅ accounts.json already exists"
fi

# Test mode prompt
echo ""
echo "🧪 Testing configuration..."
python3 inbox_processor_cloud.py --test --config=accounts.json 2>&1 | head -20

echo ""
echo "=========================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit accounts.json with your credentials"
echo "2. Run: python3 inbox_processor_cloud.py --mode=monitor --config=accounts.json"
echo "3. For GitHub Actions: Push to repository and configure secrets"
echo ""
