$ErrorActionPreference = "Stop"

Write-Host "Starting skill server on :8010"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn skill_server.app:app --reload --port 8010"

Write-Host "Starting API server on :8000"
uvicorn interview_ai.main:app --reload --port 8000
