$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -e .
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name TibiaHuntTracker `
    --paths src `
    --add-data "data/tracker_catalog.json;data" `
    --collect-all pyttsx3 `
    run.py

Write-Host "Executável criado em dist\TibiaHuntTracker.exe"
