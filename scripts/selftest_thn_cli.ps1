Param(
    [switch] $VerboseMode
)

Write-Host ""
Write-Host "==========================================" 
Write-Host "  THN CLI Self-Test (PowerShell)"
Write-Host "==========================================" 
Write-Host ""

function Assert-LastExitCode {
    param(
        [string] $Step
    )
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[FAIL] $Step (exit code $LASTEXITCODE)"
        exit $LASTEXITCODE
    }
}

# 1) Ensure 'thn' is available
Write-Host "[STEP] Checking 'thn' on PATH..."
$thnCmd = Get-Command thn -ErrorAction SilentlyContinue
if (-not $thnCmd) {
    Write-Error "[FAIL] 'thn' command not found on PATH. Install thn-cli or fix PATH."
    exit 1
}
Write-Host "[OK] thn = $($thnCmd.Source)"
Write-Host ""

# 2) Help
Write-Host "[STEP] thn --help"
thn --help | Out-Null
Assert-LastExitCode "thn --help"
Write-Host "[OK] Help runs."
Write-Host ""

# 3) Path listing
Write-Host "[STEP] thn list"
thn list
Assert-LastExitCode "thn list"
Write-Host ""

# 4) Sanity diagnostics
Write-Host "[STEP] thn diag sanity"
thn diag sanity
Assert-LastExitCode "thn diag sanity"
Write-Host ""

# 5) Routing config
Write-Host "[STEP] thn routing show"
thn routing show
Assert-LastExitCode "thn routing show"
Write-Host ""

# 6) Sync Web dry-run
Write-Host "[STEP] thn sync web --input . --dry-run"
thn sync web --input . --dry-run
Assert-LastExitCode "thn sync web --dry-run"
Write-Host ""

Write-Host "[SUCCESS] THN CLI self-test completed successfully."
