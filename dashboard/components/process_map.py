import pm4py
import plotly.graph_objects as go
import networkx as nx
import pandas as pd
import numpy as np

def generate_process_map(event_log):
    """
    Generate an interactive process map visualization using Plotly.
    
    Args:
        event_log: PM4Py event log or DataFrame
        
    Returns:
        Plotly figure object
    """
    # Handle different types of event logs
    if isinstance(event_log, pd.DataFrame):
        # If it's a DataFrame, ensure it has the required columns
        if not all(col in event_log.columns for col in ['case:concept:name', 'concept:name', 'time:timestamp']):
            raise ValueError("DataFrame must contain 'case:concept:name', 'concept:name', and 'time:timestamp' columns")
    
    # Discover process model (directly-follows graph)
    try:
        dfg, start_activities, end_activities = pm4py.discover_directly_follows_graph(event_log)
    except Exception as e:
        # Convert DataFrame to EventLog if needed
        if isinstance(event_log, pd.DataFrame):
            try:
                # Try to convert the DataFrame to a PM4Py format
                event_log_converted = pm4py.format_dataframe(
                    event_log,
                    case_id='case:concept:name',
                    activity_key='concept:name',
                    timestamp_key='time:timestamp'
                )
                dfg, start_activities, end_activities = pm4py.discover_directly_follows_graph(event_log_converted)
            except Exception as conv_error:
                raise ValueError(f"Failed to process event log: {str(conv_error)}")
        else:
            raise ValueError(f"Failed to discover directly-follows graph: {str(e)}")
    
    # Convert to networkx graph for layout calculation
    G = nx.DiGraph()
    
    # Add nodes
    activities = set()
    for (act1, act2) in dfg:
        activities.add(act1)
        activities.add(act2)
    
    for act in activities:
        G.add_node(act)
    
    # Add edges with weights
    for (act1, act2), weight in dfg.items():
        G.add_edge(act1, act2, weight=weight)
    
    # Calculate layout using Fruchterman-Reingold algorithm
    pos = nx.spring_layout(G, seed=42)
    
    # Normalize edge weights for visualization
    max_weight = max(dfg.values()) if dfg else 1
    
    # Create edges trace
    edge_x = []
    edge_y = []
    edge_text = []
    edge_width = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
        weight = G.edges[edge]['weight']
        edge_text.append(f"{edge[0]} → {edge[1]}<br>Frequency: {weight}")
        edge_width.append((weight / max_weight) * 5)
    
    # Create edge trace
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#888'),  # Use fixed width instead of list
        hoverinfo='text',
        text=edge_text,
        mode='lines')
    
    # Create nodes trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    # Calculate activity frequencies - handle different event log formats
    activity_counts = {}
    
    if isinstance(event_log, pd.DataFrame):
        if 'concept:name' in event_log.columns:
            activity_counts = event_log['concept:name'].value_counts().to_dict()
    else:
        # Try PM4Py EventLog object
        try:
            for trace in event_log:
                for event in trace:
                    try:
                        # Handle both dict-like access and attribute access
                        if isinstance(event, dict):
                            activity = event.get("concept:name")
                        else:
                            activity = event["concept:name"]
                            
                        if activity is not None:
                            activity_counts[activity] = activity_counts.get(activity, 0) + 1
                    except (TypeError, KeyError, AttributeError):
                        continue
        except Exception as e:
            # If we can't extract activity counts, use DFG frequency instead
            for (act1, act2), weight in dfg.items():
                activity_counts[act1] = activity_counts.get(act1, 0) + weight
                activity_counts[act2] = activity_counts.get(act2, 0) + weight
    
    max_count = max(activity_counts.values()) if activity_counts else 1
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        count = activity_counts.get(node, 0)
        is_start = node in start_activities
        is_end = node in end_activities
        
        status = []
        if is_start:
            status.append("Start activity")
        if is_end:
            status.append("End activity")
        
        status_str = f"<br>Type: {', '.join(status)}" if status else ""
        node_text.append(f"Activity: {node}<br>Frequency: {count}{status_str}")
        
        # Size based on frequency
        node_size.append((count / max_count) * 50 + 20)
        
        # Color: blue for start, red for end, purple for both, green for regular
        if is_start and is_end:
            node_color.append('purple')
        elif is_start:
            node_color.append('blue')
        elif is_end:
            node_color.append('red')
        else:
            node_color.append('green')
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line=dict(width=2, color='white'))
    )
    
    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='Interactive Process Map',
                    titlefont=dict(size=16),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    height=600,
                    annotations=[
                        dict(
                            text=f"Created: 2025-08-22 | By: MustafaHameed",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.01, y=-0.05,
                            font=dict(size=10, color="gray")
                        )
                    ]
                 ))
    
    return fig