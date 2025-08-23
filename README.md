# Process Mining Education

Two Streamlit dashboards plus a reproducible analysis pipeline for the Educational Process Mining (EPM) dataset.

## What’s in here

- Dashboards (Streamlit):
  - Minimal dashboard at `dashboard/minimal_app.py` (port 8501)
  - Enhanced dashboard at `dashboard/enhanced_app.py` (port 8502)
- Reusable modules under `dashboard/components` and `dashboard/interpreters`
- Analysis scripts: `data_preprocessing.py`, `process_discovery.py`, `performance_analysis.py`, `conformance_checking.py`

## Quick start

1) Install Python 3.10+ and dependencies:

   - Option A: pip
   - Option B: a virtual environment is recommended

2) Install packages:

   pip install -r requirements.txt

3) Run both dashboards on Windows:

   - Double‑click `run_dashboards.bat`, or
   - Right‑click `run_dashboards.ps1` → Run with PowerShell

   Then open:
   - Minimal: http://localhost:8501
   - Enhanced: http://localhost:8502

## Graphviz note (for process visualizations)

Some visualizations require the Graphviz system package in addition to the Python package. On Windows:

1) Download Graphviz from https://graphviz.org/download/
2) Install it and add its bin folder (e.g., `C:\Program Files\Graphviz\bin`) to your PATH

If Graphviz isn’t installed, certain PM4Py/graph exports may fail.

## Smoke tests

- Run pipeline once to generate outputs:
  - PowerShell: `python .\main.py --dataset "EPM Dataset 2" --output output`
- Launch dashboards and verify they start and load a CSV

## Repo layout

- `dashboard/` – Streamlit apps and shared components
- `output/` – Generated charts and reports
- `EPM Dataset 2/` – Included sample dataset