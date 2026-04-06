@echo off
REM ═══════════════════════════════════════════════════════════════════
REM  LAS CMS Analysis — Windows Conda Setup Script
REM
REM  Run this ONCE from Anaconda Prompt:
REM    cd E:\devgate\Legal_AI_Society\LAS_CMS_Analysis
REM    setup_environment.bat
REM ═══════════════════════════════════════════════════════════════════

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     LAS CMS Analysis — Environment Setup                 ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM ── Step 1: Create conda environment from yml ─────────────────────
echo [1/4] Creating conda environment 'las_cms'...
echo       This may take 5-10 minutes on first run...
echo.
conda env create -f environment.yml
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Environment may already exist. Updating instead...
    conda env update -f environment.yml --prune
)

REM ── Step 2: Activate ──────────────────────────────────────────────
echo.
echo [2/4] Activating environment...
CALL conda activate las_cms
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Could not activate 'las_cms'. Try manually:
    echo   conda activate las_cms
    pause
    exit /b 1
)

REM ── Step 3: Register Jupyter kernel ───────────────────────────────
echo.
echo [3/4] Registering Jupyter kernel...
python -m ipykernel install --user --name las_cms --display-name "LAS CMS Analysis"

REM ── Step 4: Download spaCy model for PII detection ────────────────
echo.
echo [4/4] Downloading spaCy English model for PII detection...
python -m spacy download en_core_web_lg

REM ── Sanity Check ──────────────────────────────────────────────────
echo.
echo Running sanity check...
python -c "import pandas; import matplotlib; import seaborn; print('  pandas:', pandas.__version__); print('  matplotlib:', matplotlib.__version__); print('  seaborn:', seaborn.__version__); print('  All OK!')"

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                  Setup Complete!                         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo To start working:
echo   1. conda activate las_cms
echo   2. jupyter lab
echo   3. Open the notebooks in the 'notebooks' folder
echo.
pause
