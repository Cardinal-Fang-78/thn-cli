@echo off
setlocal ENABLEDELAYEDEXPANSION

echo.
echo ==========================================
echo   THN CLI Self-Test (Windows / CMD)
echo ==========================================
echo.

REM 1) Check that "thn" is on PATH
where thn >nul 2>&1
if errorlevel 1 (
    echo [FAIL] "thn" command not found on PATH.
    echo        Ensure the thn-cli package is installed and pipx/scrips dir is in PATH.
    exit /b 1
)

echo [OK] "thn" command found.
echo.

REM 2) Basic help
echo [STEP] thn --help
thn --help >nul 2>&1
if errorlevel 1 (
    echo [FAIL] "thn --help" failed.
    exit /b 1
)
echo [OK] Help runs.
echo.

REM 3) List paths
echo [STEP] thn list
thn list
if errorlevel 1 (
    echo [FAIL] "thn list" failed.
    exit /b 1
)
echo.

REM 4) Sanity diagnostics
echo [STEP] thn diag sanity
thn diag sanity
if errorlevel 1 (
    echo [FAIL] "thn diag sanity" failed.
    exit /b 1
)
echo.

REM 5) Routing show
echo [STEP] thn routing show
thn routing show
if errorlevel 1 (
    echo [FAIL] "thn routing show" failed.
    exit /b 1
)
echo.

REM 6) Sync Web dry-run smoke
echo [STEP] thn sync web --input . --dry-run
thn sync web --input . --dry-run
if errorlevel 1 (
    echo [FAIL] "thn sync web --dry-run" failed.
    exit /b 1
)
echo.

echo [SUCCESS] THN CLI self-test completed successfully.
exit /b 0
