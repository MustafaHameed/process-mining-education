# Educational Process Mining Analysis

This project implements educational process mining analysis on the EPM (Educational Process Mining) dataset from the University of Genoa. The analysis provides insights into student learning behaviors, process patterns, and educational performance.

## Dataset
The EPM dataset contains behavioral data from 115 first-year engineering students during 6 laboratory sessions of a digital electronics course. Students used the DEEDS (Digital Electronics Education and Design Suite) simulation environment.

## Features
- **Data Extraction and Preprocessing**: Clean and prepare the dataset for process mining
- **Process Discovery**: Discover educational process models and visualize learning paths
- **Performance Analysis**: Calculate metrics and identify patterns in student progression
- **Conformance Checking**: Compare actual vs expected learning behaviors
- **Insights Generation**: Create visualizations and actionable insights

## Installation

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Graphviz Installation (Required for Process Visualizations)
For full process mining visualizations, you need to install Graphviz on your system:

**Ubuntu/Debian:**
```bash
sudo apt-get install graphviz
```

**macOS:**
```bash
brew install graphviz
```

**Windows:**
1. Download from [https://graphviz.org/download/](https://graphviz.org/download/)
2. Install and ensure `dot.exe` is in your system PATH

**Verify Installation:**
```bash
dot -V
```

> **Note:** If Graphviz is not available, the analysis will continue with text-based fallbacks for process visualizations.

## Usage
```bash
python main.py
```

## Output
The analysis generates:
- Process models and visualizations
- Performance metrics and statistics
- Conformance checking results
- Educational insights and recommendations

## Citation
If you use this analysis, please cite the original dataset:
M. Vahdat, L. Oneto, D. Anguita, M. Funk, M. Rauterberg. Educational Process Mining (EPM): A Learning Analytics Data Set. EC-TEL 2015.