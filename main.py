"""
Main script for Educational Process Mining Analysis.
Integrates all components: data preprocessing, process discovery, 
performance analysis, and conformance checking.
"""

import os
import pandas as pd
import argparse
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_preprocessing import EPMDataProcessor
from process_discovery import ProcessDiscovery
from performance_analysis import PerformanceAnalysis
from conformance_checking import ConformanceChecker


class EducationalProcessMiningAnalysis:
    """Main class that orchestrates the complete educational process mining analysis."""
    
    def __init__(self, dataset_path: str = "EPM Dataset 2", output_dir: str = "output"):
        """
        Initialize the educational process mining analysis.
        
        Args:
            dataset_path: Path to the EPM dataset directory
            output_dir: Directory to save all outputs
        """
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize components
        self.data_processor = EPMDataProcessor(dataset_path)
        self.process_discovery = ProcessDiscovery(output_dir)
        self.performance_analysis = PerformanceAnalysis(output_dir)
        self.conformance_checker = ConformanceChecker(output_dir)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def run_complete_analysis(self, min_events_per_case: int = 10, 
                            exclude_activities: list = None) -> dict:
        """
        Run the complete educational process mining analysis pipeline.
        
        Args:
            min_events_per_case: Minimum number of events per case for quality filtering
            exclude_activities: List of activities to exclude from analysis
            
        Returns:
            Dictionary containing all analysis results
        """
        if exclude_activities is None:
            exclude_activities = ['Blank', 'Other']
            
        print("=" * 60)
        print("EDUCATIONAL PROCESS MINING ANALYSIS")
        print("=" * 60)
        print(f"Starting analysis at {datetime.now()}")
        print(f"Dataset: {self.dataset_path}")
        print(f"Output directory: {self.output_dir}")
        print()
        
        results = {}
        
        # Step 1: Data Preprocessing
        print("STEP 1: DATA EXTRACTION AND PREPROCESSING")
        print("-" * 45)
        
        # Load raw data
        raw_data = self.data_processor.load_all_data()
        if raw_data.empty:
            raise ValueError("Failed to load dataset. Please check the dataset path.")
        
        # Create event log
        event_log = self.data_processor.create_event_log(raw_data)
        
        # Get basic statistics
        basic_stats = self.data_processor.get_basic_statistics(event_log)
        print(f"✓ Loaded {basic_stats['total_events']:,} events from {basic_stats['total_cases']} cases")
        print(f"✓ {basic_stats['total_students']} students across {basic_stats['total_sessions']} sessions")
        
        # Apply quality filters
        quality_log = self.data_processor.filter_by_criteria(
            event_log, 
            min_events_per_case=min_events_per_case,
            exclude_activities=exclude_activities
        )
        
        quality_stats = self.data_processor.get_basic_statistics(quality_log)
        print(f"✓ Quality filtered to {quality_stats['total_events']:,} events from {quality_stats['total_cases']} cases")
        
        results['preprocessing'] = {
            'raw_data': raw_data,
            'event_log': event_log,
            'quality_log': quality_log,
            'basic_stats': basic_stats,
            'quality_stats': quality_stats
        }
        
        # Step 2: Process Discovery
        print("\\nSTEP 2: PROCESS DISCOVERY")
        print("-" * 30)
        
        discovery_results = self.process_discovery.discover_all_models(quality_log)
        print("✓ Process models discovered and visualized")
        
        results['process_discovery'] = discovery_results
        
        # Step 3: Performance Analysis
        print("\\nSTEP 3: PERFORMANCE ANALYSIS")
        print("-" * 32)
        
        performance_results = self.performance_analysis.run_complete_analysis(quality_log)
        print("✓ Performance analysis completed")
        
        results['performance_analysis'] = performance_results
        
        # Step 4: Conformance Checking
        print("\\nSTEP 4: CONFORMANCE CHECKING")
        print("-" * 32)
        
        conformance_results = self.conformance_checker.run_complete_conformance_check(quality_log)
        print("✓ Conformance analysis completed")
        
        results['conformance_checking'] = conformance_results
        
        # Step 5: Generate Summary Report
        print("\\nSTEP 5: GENERATING SUMMARY REPORT")
        print("-" * 38)
        
        summary_report = self.generate_executive_summary(results)
        
        # Save summary report
        summary_path = os.path.join(self.output_dir, f'executive_summary_{self.timestamp}.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        print(f"✓ Executive summary saved to {summary_path}")
        
        results['executive_summary'] = summary_report
        
        # Final summary
        print("\\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Total processing time: {datetime.now()}")
        print(f"All outputs saved to: {self.output_dir}")
        print("\\nGenerated files:")
        self.list_output_files()
        
        return results
    
    def generate_executive_summary(self, results: dict) -> str:
        """
        Generate an executive summary combining insights from all analyses.
        
        Args:
            results: Dictionary containing all analysis results
            
        Returns:
            String with executive summary
        """
        summary = []
        summary.append("=" * 70)
        summary.append("EDUCATIONAL PROCESS MINING - EXECUTIVE SUMMARY")
        summary.append("=" * 70)
        summary.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Dataset: EPM (Educational Process Mining) - University of Genoa")
        summary.append("")
        
        # Key Findings
        summary.append("KEY FINDINGS")
        summary.append("-" * 20)
        
        # Dataset overview
        basic_stats = results['preprocessing']['basic_stats']
        summary.append(f"• Analyzed {basic_stats['total_students']} engineering students")
        summary.append(f"• {basic_stats['total_events']:,} learning activities recorded")
        summary.append(f"• {basic_stats['total_activities']} different activity types identified")
        summary.append("")
        
        # Process insights
        variant_analysis = results['process_discovery']['variant_analysis']
        summary.append(f"• {variant_analysis['total_variants']} unique learning paths discovered")
        summary.append(f"• Most students follow individualized learning approaches")
        summary.append("")
        
        # Performance insights
        performance_report = results['performance_analysis']['report']
        performance_lines = performance_report.split('\\n')
        
        # Extract key performance metrics
        for line in performance_lines:
            if 'Average Session Duration:' in line:
                summary.append(f"• {line.strip()}")
            elif 'Average Events per Session:' in line:
                summary.append(f"• {line.strip()}")
            elif 'Average Activity Diversity:' in line:
                summary.append(f"• {line.strip()}")
        summary.append("")
        
        # Conformance insights
        conformance_report = results['conformance_checking']['report']
        conformance_lines = conformance_report.split('\\n')
        
        for line in conformance_lines:
            if 'Average Sequence Conformance:' in line:
                summary.append(f"• {line.strip()}")
            elif 'Average Behavioral Conformance:' in line:
                summary.append(f"• {line.strip()}")
        summary.append("")
        
        # Top Activities
        summary.append("MOST COMMON LEARNING ACTIVITIES")
        summary.append("-" * 35)
        activity_freq = results['performance_analysis']['patterns']['activity_frequency']
        for i, (activity, count) in enumerate(list(activity_freq.items())[:5], 1):
            summary.append(f"{i}. {activity}: {count:,} occurrences")
        summary.append("")
        
        # Learning Patterns
        summary.append("LEARNING PATTERN INSIGHTS")
        summary.append("-" * 30)
        summary.append("• Students primarily use DEEDS simulator for practical exercises")
        summary.append("• Diagram analysis is heavily used for verification")
        summary.append("• Text editor usage indicates solution documentation")
        summary.append("• Aulaweb platform serves as primary navigation hub")
        summary.append("")
        
        # Process Deviations
        deviations = results['conformance_checking']['deviations']
        total_cases = len(results['conformance_checking']['sequence_conformance'])
        
        summary.append("PROCESS DEVIATIONS IDENTIFIED")
        summary.append("-" * 35)
        for deviation_type, cases in deviations.items():
            if cases:  # Only show non-empty deviation types
                percentage = (len(cases) / total_cases) * 100
                readable_name = deviation_type.replace('_', ' ').title()
                summary.append(f"• {readable_name}: {len(cases)} students ({percentage:.1f}%)")
        summary.append("")
        
        # Recommendations
        summary.append("RECOMMENDATIONS FOR EDUCATIONAL IMPROVEMENT")
        summary.append("-" * 50)
        
        # Extract recommendations from conformance report
        in_recommendations = False
        for line in conformance_lines:
            if "RECOMMENDATIONS FOR IMPROVEMENT" in line:
                in_recommendations = True
                continue
            elif in_recommendations and line.startswith("6."):
                break
            elif in_recommendations and line.strip().startswith("•"):
                summary.append(line.strip())
        
        # Additional recommendations based on analysis
        summary.append("• Consider implementing learning path templates for consistency")
        summary.append("• Provide real-time feedback on student progress patterns")
        summary.append("• Develop adaptive learning suggestions based on individual patterns")
        summary.append("")
        
        # Technical Summary
        summary.append("TECHNICAL ANALYSIS SUMMARY")
        summary.append("-" * 35)
        summary.append("Process Mining Techniques Applied:")
        summary.append("  → Directly-Follows Graph (DFG) analysis")
        summary.append("  → Inductive process mining")
        summary.append("  → Behavioral pattern analysis")
        summary.append("  → Sequence conformance checking")
        summary.append("  → Performance bottleneck identification")
        summary.append("")
        
        summary.append("Visualizations Generated:")
        summary.append("  → Process flow diagrams")
        summary.append("  → Activity frequency charts")
        summary.append("  → Performance distribution plots")
        summary.append("  → Conformance analysis charts")
        summary.append("  → Learning pattern heatmaps")
        summary.append("")
        
        # Conclusion
        summary.append("CONCLUSION")
        summary.append("-" * 15)
        summary.append("This analysis reveals significant insights into student learning")
        summary.append("behaviors in digital electronics education. The process mining")
        summary.append("approach successfully identified learning patterns, performance")
        summary.append("variations, and areas for educational process improvement.")
        summary.append("")
        summary.append("The findings can inform curriculum design, learning platform")
        summary.append("optimization, and personalized learning interventions to enhance")
        summary.append("student success in engineering education.")
        summary.append("")
        summary.append("=" * 70)
        
        return "\\n".join(summary)
    
    def list_output_files(self):
        """List all generated output files."""
        if os.path.exists(self.output_dir):
            files = os.listdir(self.output_dir)
            for file in sorted(files):
                file_path = os.path.join(self.output_dir, file)
                size = os.path.getsize(file_path)
                size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"
                print(f"  - {file} ({size_str})")
    
    def create_analysis_index(self):
        """Create an HTML index file linking all outputs."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Educational Process Mining Analysis Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
                .section {{ margin: 20px 0; }}
                .file-list {{ list-style-type: none; padding: 0; }}
                .file-list li {{ margin: 10px 0; }}
                .file-list a {{ text-decoration: none; color: #3498db; }}
                .file-list a:hover {{ text-decoration: underline; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Educational Process Mining Analysis Results</h1>
            <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Analysis Summary</h2>
                <p>This analysis applied process mining techniques to educational data from the University of Genoa's 
                digital electronics course, analyzing learning behaviors of {self.data_processor.load_all_data()['student_id'].nunique() if not self.data_processor.load_all_data().empty else 'N/A'} engineering students.</p>
            </div>
            
            <div class="section">
                <h2>Generated Reports</h2>
                <ul class="file-list">
                    <li><a href="performance_analysis_report.txt">📊 Performance Analysis Report</a> - Detailed performance metrics and insights</li>
                    <li><a href="conformance_analysis_report.txt">✅ Conformance Analysis Report</a> - Process compliance and deviations</li>
                    <li><a href="executive_summary_{self.timestamp}.txt">📋 Executive Summary</a> - High-level findings and recommendations</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Process Visualizations</h2>
                <ul class="file-list">
                    <li><a href="inductive_process_tree.png">🌳 Process Tree</a> - Discovered process model structure</li>
                    <li><a href="inductive_petri_net.png">🕸️ Petri Net</a> - Formal process representation</li>
                    <li><a href="activity_frequency.png">📈 Activity Frequency Chart</a> - Most common learning activities</li>
                    <li><a href="session_activity_heatmap.png">🔥 Session Activity Heatmap</a> - Activity distribution across sessions</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Performance Analysis</h2>
                <ul class="file-list">
                    <li><a href="duration_vs_events.png">⏱️ Duration vs Events</a> - Relationship between session length and activity count</li>
                    <li><a href="activity_diversity_distribution.png">🎨 Activity Diversity</a> - Distribution of student activity patterns</li>
                    <li><a href="learning_activity_ratios.png">📊 Learning Activity Ratios</a> - Time allocation across activity types</li>
                    <li><a href="hourly_activity_distribution.png">🕐 Hourly Activity Distribution</a> - Learning patterns by time of day</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Conformance Analysis</h2>
                <ul class="file-list">
                    <li><a href="conformance_analysis.png">✅ Conformance Analysis</a> - Process compliance evaluation</li>
                    <li><a href="activity_category_heatmap.png">🗂️ Activity Category Heatmap</a> - Learning behavior categorization</li>
                </ul>
            </div>
            
            <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d;">
                <p>Generated by Educational Process Mining Analysis Tool</p>
                <p>Based on PM4Py process mining framework</p>
            </footer>
        </body>
        </html>
        """
        
        index_path = os.path.join(self.output_dir, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Analysis index created: {index_path}")


def main():
    """Main function to run the educational process mining analysis."""
    parser = argparse.ArgumentParser(description='Educational Process Mining Analysis')
    parser.add_argument('--dataset', default='EPM Dataset 2', 
                       help='Path to EPM dataset directory')
    parser.add_argument('--output', default='output', 
                       help='Output directory for results')
    parser.add_argument('--min-events', type=int, default=10,
                       help='Minimum events per case for quality filtering')
    parser.add_argument('--exclude', nargs='*', default=['Blank', 'Other'],
                       help='Activities to exclude from analysis')
    
    args = parser.parse_args()
    
    # Create analysis instance
    analysis = EducationalProcessMiningAnalysis(
        dataset_path=args.dataset,
        output_dir=args.output
    )
    
    try:
        # Run complete analysis
        results = analysis.run_complete_analysis(
            min_events_per_case=args.min_events,
            exclude_activities=args.exclude
        )
        
        # Create HTML index
        analysis.create_analysis_index()
        
        print("\\n🎉 Analysis completed successfully!")
        print(f"📁 Check the '{args.output}' directory for all results")
        print(f"🌐 Open '{args.output}/index.html' for a complete overview")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()