import pm4py
import plotly.graph_objects as go
import networkx as nx
import pandas as pd
import numpy as np

def make_dummy_process_graph():
    g = nx.DiGraph()
    g.add_edge("Start", "Activity A")
    g.add_edge("Activity A", "End")
    return g