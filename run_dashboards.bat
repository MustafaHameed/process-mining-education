@echo off
echo Starting Process Mining Educational Dashboards...
echo.
echo Minimal Dashboard will be available at: http://localhost:8501
echo Enhanced Dashboard will be available at: http://localhost:8502
echo.
start "" cmd /c "streamlit run dashboard\minimal_app.py --server.port 8501"
start "" cmd /c "streamlit run dashboard\enhanced_app.py --server.port 8502"
