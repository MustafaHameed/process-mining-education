# PowerShell script to run both dashboards on separate ports
Write-Host "Starting Process Mining Educational Dashboards..." -ForegroundColor Green
Write-Host ""
Write-Host "Minimal Dashboard will be available at: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Enhanced Dashboard will be available at: http://localhost:8502" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop the dashboards." -ForegroundColor Yellow
Write-Host ""

# Get the current directory
$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start both dashboards in separate terminals
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$currentDir'; streamlit run dashboard/minimal_app.py --server.port 8501"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$currentDir'; streamlit run dashboard\enhanced_app.py --server.port 8502"

Write-Host "Both dashboards are now running." -ForegroundColor Green
Write-Host ""
