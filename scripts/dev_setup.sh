#!/usr/bin/env bash
echo "THN Developer Bootstrap"
echo "Installing development dependencies..."

pip install -e .[dev]

echo ""
echo "Running environment verification..."
thn diag env

echo ""
echo "Developer environment ready."
