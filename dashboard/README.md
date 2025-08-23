# Process Mining Educational Dashboards

This project provides two Streamlit-based dashboards for educational process mining:

## Minimal Dashboard (Port 8501)
A lightweight dashboard focused on basic data loading and summary statistics. This dashboard provides:
- Simple session breakdown visualization
- Basic data summary metrics
- Fast loading and processing

**Use this dashboard when:**
- You need a quick overview of the dataset
- You want to check session data availability
- You're experiencing performance issues with the enhanced dashboard

## Enhanced Dashboard (Port 8502)
A comprehensive dashboard with advanced visualizations and analysis capabilities:
- Advanced process map visualization 
- Performance metrics and bottleneck analysis
- Pattern detection and insights
- Conformance checking capabilities
- Activity frequency analysis
- Temporal distribution of learning activities

**Use this dashboard when:**
- You need detailed process analysis
- You want to explore learning patterns
- You need comprehensive visualizations
- You're conducting in-depth educational process mining research

## Running Both Dashboards

### Windows
1. Run the `run_dashboards.bat` file by double-clicking it
2. Access the minimal dashboard at http://localhost:8501
3. Access the enhanced dashboard at http://localhost:8502

### PowerShell
1. Right-click `run_dashboards.ps1` and select "Run with PowerShell"
2. Access the minimal dashboard at http://localhost:8501
3. Access the enhanced dashboard at http://localhost:8502

### Manual Startup
To run the dashboards manually:

```
# Terminal 1 - Minimal Dashboard
cd c:\path\to\process-mining-education
streamlit run dashboard/minimal_app.py --server.port 8501

# Terminal 2 - Enhanced Dashboard
cd c:\path\to\process-mining-education
streamlit run dashboard/enhanced_app.py --server.port 8502
```

## Dataset Configuration

Both dashboards provide the ability to work with the EPM (Educational Process Mining) Dataset:

- The minimal dashboard provides basic dataset loading
- The enhanced dashboard adds filtering options, session selection, and the ability to upload custom datasets

## System Requirements

- Python 3.8+
- Streamlit
- PM4Py
- Pandas
- Plotly
- NetworkX
