"""
Process discovery module for educational process mining.
Discovers process models from student learning event logs using PM4Py.
"""

import pandas as pd
import pm4py
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.statistics.start_activities.log import get as start_activities_get
from pm4py.statistics.end_activities.log import get as end_activities_get
import matplotlib.pyplot as plt
import seaborn as sns
import os
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class ProcessDiscovery:
    """Class for discovering educational process models from event logs."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize process discovery.
        
        Args:
            output_dir: Directory to save outputs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def create_pm4py_log(self, df: pd.DataFrame) -> object:
        """
        Convert DataFrame to PM4Py log object.
        
        Args:
            df: Event log DataFrame
            
        Returns:
            PM4Py log object
        """
        # Ensure required columns exist
        required_cols = ['case:concept:name', 'concept:name', 'time:timestamp']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # Clean the dataframe first
        clean_df = df[required_cols].copy()
        clean_df = clean_df.dropna()
        
        # Convert to PM4Py format using the updated API
        log = pm4py.convert_to_event_log(clean_df)
        
        print(f"Created PM4Py log with {len(log)} traces")
        return log
    
    def discover_dfg(self, log: object) -> Tuple[Dict, Dict, Dict]:
        """
        Discover Directly-Follows Graph (DFG).
        
        Args:
            log: PM4Py log object
            
        Returns:
            Tuple of (dfg, start_activities, end_activities)
        """
        # Discover DFG
        dfg = dfg_discovery.apply(log)
        
        # Get start and end activities
        start_activities = start_activities_get.get_start_activities(log)
        end_activities = end_activities_get.get_end_activities(log)
        
        print(f"DFG discovered with {len(dfg)} edges")
        print(f"Start activities: {len(start_activities)}")
        print(f"End activities: {len(end_activities)}")
        
        return dfg, start_activities, end_activities
    
    def visualize_dfg(self, dfg: Dict, start_activities: Dict, end_activities: Dict, 
                     title: str = "Educational Process DFG") -> None:
        """
        Visualize the Directly-Follows Graph.
        
        Args:
            dfg: Directly-follows graph
            start_activities: Start activities dictionary
            end_activities: End activities dictionary
            title: Title for the visualization
        """
        try:
            # Create visualization without service time (which is causing the error)
            parameters = {dfg_visualizer.Variants.FREQUENCY.value.Parameters.FORMAT: "png"}
            gviz = dfg_visualizer.apply(dfg, start_activities, end_activities, parameters=parameters)
            
            # Save visualization
            output_path = os.path.join(self.output_dir, f"{title.lower().replace(' ', '_')}.png")
            dfg_visualizer.save(gviz, output_path)
            print(f"DFG visualization saved to {output_path}")
        except Exception as e:
            print(f"Error creating DFG visualization: {e}")
            print("Continuing with other process discovery methods...")
    
    def discover_inductive_model(self, log: object) -> Tuple[object, object, object]:
        """
        Discover process model using Inductive Miner.
        
        Args:
            log: PM4Py log object
            
        Returns:
            Tuple of (process_tree, net, initial_marking, final_marking)
        """
        # Apply inductive miner
        process_tree = inductive_miner.apply(log)
        
        # Convert to Petri net
        net, initial_marking, final_marking = pm4py.convert_to_petri_net(process_tree)
        
        print(f"Inductive miner discovered process tree with {len(net.places)} places and {len(net.transitions)} transitions")
        
        return process_tree, net, initial_marking, final_marking
    
    def discover_heuristics_model(self, log: object) -> Tuple[object, object, object]:
        """
        Discover process model using Heuristics Miner.
        
        Args:
            log: PM4Py log object
            
        Returns:
            Tuple of (heuristics_net, net, initial_marking, final_marking)
        """
        try:
            # Apply heuristics miner
            heu_net = heuristics_miner.apply(log, parameters={heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.5})
            
            # Convert to Petri net (use convert_to_petri_net for heuristics net)
            from pm4py.objects.conversion.heuristics_net import converter as hn_converter
            net, initial_marking, final_marking = hn_converter.apply(heu_net)
            
            print(f"Heuristics miner discovered model with {len(net.places)} places and {len(net.transitions)} transitions")
            
            return heu_net, net, initial_marking, final_marking
        except Exception as e:
            print(f"Error in heuristics model discovery: {e}")
            # Return None values if heuristics mining fails
            return None, None, None, None
    
    def visualize_process_tree(self, process_tree: object, title: str = "Process Tree") -> None:
        """
        Visualize process tree.
        
        Args:
            process_tree: PM4Py process tree object
            title: Title for the visualization
        """
        try:
            gviz = pt_visualizer.apply(process_tree, parameters={pt_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "png"})
            output_path = os.path.join(self.output_dir, f"{title.lower().replace(' ', '_')}.png")
            pt_visualizer.save(gviz, output_path)
            print(f"Process tree visualization saved to {output_path}")
        except Exception as e:
            print(f"Error creating process tree visualization: {e}")
    
    def visualize_petri_net(self, net: object, initial_marking: object, final_marking: object,
                           title: str = "Petri Net") -> None:
        """
        Visualize Petri net.
        
        Args:
            net: Petri net object
            initial_marking: Initial marking
            final_marking: Final marking
            title: Title for the visualization
        """
        try:
            gviz = pn_visualizer.apply(net, initial_marking, final_marking,
                                     parameters={pn_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "png"})
            output_path = os.path.join(self.output_dir, f"{title.lower().replace(' ', '_')}.png")
            pn_visualizer.save(gviz, output_path)
            print(f"Petri net visualization saved to {output_path}")
        except Exception as e:
            print(f"Error creating Petri net visualization: {e}")
    
    def visualize_heuristics_net(self, heu_net: object, title: str = "Heuristics Net") -> None:
        """
        Visualize heuristics net.
        
        Args:
            heu_net: Heuristics net object
            title: Title for the visualization
        """
        try:
            gviz = hn_visualizer.apply(heu_net, parameters={hn_visualizer.Variants.PYDOTPLUS.value.Parameters.FORMAT: "png"})
            output_path = os.path.join(self.output_dir, f"{title.lower().replace(' ', '_')}.png")
            hn_visualizer.save(gviz, output_path)
            print(f"Heuristics net visualization saved to {output_path}")
        except Exception as e:
            print(f"Error creating heuristics net visualization: {e}")
    
    def analyze_process_variants(self, log: object) -> Dict:
        """
        Analyze process variants (traces) in the log.
        
        Args:
            log: PM4Py log object
            
        Returns:
            Dictionary with variant analysis
        """
        # Get case statistics
        case_stats = case_statistics.get_variant_statistics(log)
        
        # Create variant analysis
        variant_analysis = {
            'total_variants': len(case_stats),
            'most_common_variants': case_stats[:10],  # Top 10 variants
            'variant_distribution': {variant['variant']: variant['count'] for variant in case_stats[:20]}
        }
        
        print(f"Process has {variant_analysis['total_variants']} unique variants")
        
        return variant_analysis
    
    def create_activity_frequency_chart(self, df: pd.DataFrame) -> None:
        """
        Create activity frequency visualization.
        
        Args:
            df: Event log DataFrame
        """
        plt.figure(figsize=(15, 8))
        
        # Get activity frequencies
        activity_counts = df['concept:name'].value_counts().head(20)
        
        # Create bar plot
        sns.barplot(x=activity_counts.values, y=activity_counts.index, palette='viridis')
        plt.title('Top 20 Most Frequent Educational Activities')
        plt.xlabel('Frequency')
        plt.ylabel('Activity')
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(self.output_dir, 'activity_frequency.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Activity frequency chart saved to {output_path}")
    
    def create_session_comparison(self, df: pd.DataFrame) -> None:
        """
        Create comparison visualization across sessions.
        
        Args:
            df: Event log DataFrame
        """
        if 'session' not in df.columns:
            print("Session information not available for comparison")
            return
            
        plt.figure(figsize=(15, 10))
        
        # Session activity heatmap
        session_activity = pd.crosstab(df['session'], df['concept:name'])
        
        # Get top activities for better visualization
        top_activities = df['concept:name'].value_counts().head(15).index
        session_activity_filtered = session_activity[top_activities]
        
        sns.heatmap(session_activity_filtered, annot=True, fmt='d', cmap='YlOrRd')
        plt.title('Activity Distribution Across Sessions')
        plt.xlabel('Activities')
        plt.ylabel('Session')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(self.output_dir, 'session_activity_heatmap.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Session comparison heatmap saved to {output_path}")
    
    def discover_all_models(self, df: pd.DataFrame) -> Dict:
        """
        Discover all process models and create visualizations.
        
        Args:
            df: Event log DataFrame
            
        Returns:
            Dictionary with all discovered models and statistics
        """
        print("\n=== Starting Process Discovery ===")
        
        # Convert to PM4Py log
        log = self.create_pm4py_log(df)
        
        # Discover DFG
        print("\n--- Discovering Directly-Follows Graph ---")
        dfg, start_activities, end_activities = self.discover_dfg(log)
        self.visualize_dfg(dfg, start_activities, end_activities, "Educational Process DFG")
        
        # Discover Inductive Model
        print("\n--- Discovering Inductive Model ---")
        process_tree, inductive_net, inductive_im, inductive_fm = self.discover_inductive_model(log)
        self.visualize_process_tree(process_tree, "Inductive Process Tree")
        self.visualize_petri_net(inductive_net, inductive_im, inductive_fm, "Inductive Petri Net")
        
        # Discover Heuristics Model
        print("\n--- Discovering Heuristics Model ---")
        heu_net, heuristics_net, heuristics_im, heuristics_fm = self.discover_heuristics_model(log)
        if heu_net is not None:
            self.visualize_heuristics_net(heu_net, "Heuristics Net")
            self.visualize_petri_net(heuristics_net, heuristics_im, heuristics_fm, "Heuristics Petri Net")
        
        # Analyze variants
        print("\n--- Analyzing Process Variants ---")
        variant_analysis = self.analyze_process_variants(log)
        
        # Create additional visualizations
        print("\n--- Creating Additional Visualizations ---")
        self.create_activity_frequency_chart(df)
        self.create_session_comparison(df)
        
        # Compile results
        results = {
            'log': log,
            'dfg': dfg,
            'start_activities': start_activities,
            'end_activities': end_activities,
            'process_tree': process_tree,
            'inductive_model': {
                'net': inductive_net,
                'initial_marking': inductive_im,
                'final_marking': inductive_fm
            },
            'heuristics_model': {
                'net': heuristics_net,
                'initial_marking': heuristics_im,
                'final_marking': heuristics_fm
            },
            'variant_analysis': variant_analysis
        }
        
        print(f"\n=== Process Discovery Complete ===")
        print(f"All visualizations saved to {self.output_dir}/")
        
        return results


def main():
    """Test the process discovery functionality."""
    from data_preprocessing import EPMDataProcessor
    
    # Load and preprocess data
    processor = EPMDataProcessor()
    raw_data = processor.load_all_data()
    event_log = processor.create_event_log(raw_data)
    
    # Filter for quality
    quality_log = processor.filter_by_criteria(
        event_log, 
        min_events_per_case=10,
        exclude_activities=['Blank', 'Other']
    )
    
    # Discover processes
    discovery = ProcessDiscovery()
    results = discovery.discover_all_models(quality_log)
    
    return results


if __name__ == "__main__":
    results = main()