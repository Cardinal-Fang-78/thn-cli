Write-Host "THN Developer Bootstrap"
Write-Host "Installing development dependencies..."

pip install -e .[dev]

Write-Host ""
Write-Host "Running environment verification..."
thn diag env

Write-Host ""
Write-Host "Developer environment ready."
