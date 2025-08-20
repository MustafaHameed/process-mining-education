import pm4py
import pandas as pd
import tempfile
import os
from datetime import datetime

def analyze_conformance(event_log, model_file):
    """
    Analyze conformance between event log and reference model.
    
    Args:
        event_log: PM4Py event log
        model_file: Uploaded file object containing BPMN or Petri net model
        
    Returns:
        Dictionary with conformance checking results
    """
    # Add analysis metadata
    analysis_metadata = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyst": "MustafaHameed",
        "model_name": model_file.name
    }
    
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(model_file.name)[1]) as tmp:
        tmp.write(model_file.getvalue())
        tmp_path = tmp.name
    
    try:
        # Load the model based on file extension
        if model_file.name.endswith('.pnml'):
            net, initial_marking, final_marking = pm4py.read_pnml(tmp_path)
            
            # Perform conformance checking with token-based replay
            replayed_traces = pm4py.conformance_diagnostics_token_based_replay(
                event_log, net, initial_marking, final_marking
            )
            
            # Calculate fitness
            fitness = 0
            for trace in replayed_traces:
                fitness += trace['trace_fitness']
            
            avg_fitness = fitness / len(replayed_traces) if replayed_traces else 0
            
            # Generate alignment-based diagnostics if possible
            try:
                alignments = pm4py.conformance_diagnostics_alignments(
                    event_log, net, initial_marking, final_marking
                )
                alignment_stats = calculate_alignment_statistics(alignments)
            except:
                alignment_stats = {"error": "Could not compute alignments"}
            
            # Try to calculate precision
            try:
                precision = pm4py.precision_token_based_replay(
                    event_log, net, initial_marking, final_marking
                )
            except:
                precision = None
            
            results = {
                "metadata": analysis_metadata,
                "token_based_replay": {
                    "average_fitness": avg_fitness,
                    "fraction_of_fitting_traces": calculate_fitting_traces_percentage(replayed_traces)
                },
                "precision": precision,
                "alignment_statistics": alignment_stats
            }
            
        elif model_file.name.endswith('.bpmn'):
            # For BPMN models, convert to Petri net first
            bpmn_graph = pm4py.read_bpmn(tmp_path)
            net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_graph)
            
            # Perform conformance checking
            replayed_traces = pm4py.conformance_diagnostics_token_based_replay(
                event_log, net, initial_marking, final_marking
            )
            
            # Calculate fitness
            fitness = 0
            for trace in replayed_traces:
                fitness += trace['trace_fitness']
            
            avg_fitness = fitness / len(replayed_traces) if replayed_traces else 0
            
            results = {
                "metadata": analysis_metadata,
                "token_based_replay": {
                    "average_fitness": avg_fitness,
                    "fraction_of_fitting_traces": calculate_fitting_traces_percentage(replayed_traces)
                }
            }
        else:
            results = {
                "metadata": analysis_metadata,
                "error": "Unsupported model format"
            }
    
    except Exception as e:
        results = {
            "metadata": analysis_metadata,
            "error": f"Error in conformance checking: {str(e)}"
        }
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    return results

def calculate_fitting_traces_percentage(replayed_traces):
    """Calculate percentage of perfectly fitting traces"""
    if not replayed_traces:
        return 0
    
    fitting_traces = sum(1 for trace in replayed_traces if trace['trace_fitness'] == 1.0)
    return fitting_traces / len(replayed_traces)

def calculate_alignment_statistics(alignments):
    """Extract statistics from alignment results"""
    if not alignments:
        return {}
    
    total_cost = 0
    max_cost = 0
    costs = []
    
    for alignment in alignments:
        cost = alignment.get('cost', 0)
        total_cost += cost
        max_cost = max(max_cost, cost)
        costs.append(cost)
    
    return {
        "average_cost": total_cost / len(alignments) if alignments else 0,
        "max_cost": max_cost,
        "perfectly_fitting_cases": sum(1 for c in costs if c == 0),
        "percentage_perfectly_fitting": sum(1 for c in costs if c == 0) / len(costs) if costs else 0
    }