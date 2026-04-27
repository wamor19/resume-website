param(
  [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

Write-Host "Serving on http://localhost:$Port"
Write-Host "Press Ctrl+C to stop."

python -m http.server $Port

