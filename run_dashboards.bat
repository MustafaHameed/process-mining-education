@echo off
echo Starting Process Mining Educational Dashboards...
echo.
echo Minimal Dashboard will be available at: http://localhost:8501
echo Enhanced Dashboard will be available at: http://localhost:8502
echo.
echo Press Ctrl+C in this terminal window to stop both dashboards.
echo.

:: Start both dashboards in separate terminals
start "Minimal Dashboard" cmd /k "cd %~dp0 && streamlit run dashboard/minimal_app.py --server.port 8501"
start "Enhanced Dashboard" cmd /k "cd %~dp0 && streamlit run dashboard/enhanced_app.py --server.port 8502"

echo Both dashboards are now running.
echo.
