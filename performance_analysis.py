"""
Performance analysis module for educational process mining.
Analyzes student performance, timing patterns, and learning behaviors.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import timedelta
import pm4py
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.statistics.variants.log import get as variants_get
import os
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class PerformanceAnalysis:
    """Class for analyzing educational process performance metrics."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize performance analysis.
        
        Args:
            output_dir: Directory to save outputs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def calculate_case_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate performance metrics for each case (student-session).
        
        Args:
            df: Event log DataFrame
            
        Returns:
            DataFrame with case-level metrics
        """
        case_metrics = []
        
        for case_id in df['case:concept:name'].unique():
            case_data = df[df['case:concept:name'] == case_id].sort_values('time:timestamp')
            
            # Basic metrics
            total_events = len(case_data)
            start_time = case_data['time:timestamp'].min()
            end_time = case_data['time:timestamp'].max()
            total_duration = (end_time - start_time).total_seconds() / 3600  # hours
            
            # Activity diversity
            unique_activities = case_data['concept:name'].nunique()
            activity_diversity = unique_activities / total_events if total_events > 0 else 0
            
            # Session and student info
            session = case_data['session'].iloc[0] if 'session' in case_data.columns else None
            student_id = case_data['student_id'].iloc[0] if 'student_id' in case_data.columns else None
            
            # Interaction metrics (if available)
            total_clicks = 0
            total_keystrokes = 0
            total_mouse_movement = 0
            
            if 'mouse_click_left' in case_data.columns:
                total_clicks = case_data['mouse_click_left'].sum() + case_data['mouse_click_right'].sum()
            if 'keystroke' in case_data.columns:
                total_keystrokes = case_data['keystroke'].sum()
            if 'mouse_movement' in case_data.columns:
                total_mouse_movement = case_data['mouse_movement'].sum()
                
            # Calculate idle time if available
            total_idle_time = 0
            if 'idle_time' in case_data.columns:
                total_idle_time = case_data['idle_time'].sum() / 1000 / 60  # minutes
            
            # Learning pattern metrics
            deeds_activities = case_data[case_data['concept:name'].str.contains('Deeds', na=False)]
            study_activities = case_data[case_data['concept:name'].str.contains('Study', na=False)]
            texteditor_activities = case_data[case_data['concept:name'].str.contains('TextEditor', na=False)]
            
            deeds_time_ratio = len(deeds_activities) / total_events if total_events > 0 else 0
            study_time_ratio = len(study_activities) / total_events if total_events > 0 else 0
            texteditor_time_ratio = len(texteditor_activities) / total_events if total_events > 0 else 0
            
            case_metrics.append({
                'case_id': case_id,
                'student_id': student_id,
                'session': session,
                'total_events': total_events,
                'total_duration_hours': total_duration,
                'unique_activities': unique_activities,
                'activity_diversity': activity_diversity,
                'total_clicks': total_clicks,
                'total_keystrokes': total_keystrokes,
                'total_mouse_movement': total_mouse_movement,
                'total_idle_time_minutes': total_idle_time,
                'deeds_time_ratio': deeds_time_ratio,
                'study_time_ratio': study_time_ratio,
                'texteditor_time_ratio': texteditor_time_ratio,
                'start_time': start_time,
                'end_time': end_time
            })
        
        metrics_df = pd.DataFrame(case_metrics)
        print(f"Calculated metrics for {len(metrics_df)} cases")
        
        return metrics_df
    
    def analyze_activity_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze patterns in activity sequences and timing.
        
        Args:
            df: Event log DataFrame
            
        Returns:
            Dictionary with activity pattern analysis
        """
        # Activity frequency analysis
        activity_freq = df['concept:name'].value_counts()
        
        # Activity transition analysis
        transitions = []
        for case_id in df['case:concept:name'].unique():
            case_data = df[df['case:concept:name'] == case_id].sort_values('time:timestamp')
            activities = case_data['concept:name'].tolist()
            
            for i in range(len(activities) - 1):
                transitions.append((activities[i], activities[i+1]))
        
        transition_freq = pd.Series(transitions).value_counts()
        
        # Time-based patterns
        df['hour'] = df['time:timestamp'].dt.hour
        hourly_activity = df.groupby('hour')['concept:name'].count()
        
        # Activity duration analysis (if duration available)
        activity_durations = {}
        if 'duration' in df.columns:
            for activity in df['concept:name'].unique():
                activity_data = df[df['concept:name'] == activity]['duration']
                activity_durations[activity] = {
                    'mean': activity_data.mean(),
                    'median': activity_data.median(),
                    'std': activity_data.std()
                }
        
        patterns = {
            'activity_frequency': activity_freq.to_dict(),
            'top_transitions': transition_freq.head(20).to_dict(),
            'hourly_distribution': hourly_activity.to_dict(),
            'activity_durations': activity_durations
        }
        
        return patterns
    
    def identify_learning_paths(self, df: pd.DataFrame) -> Dict:
        """
        Identify common learning paths and sequences.
        
        Args:
            df: Event log DataFrame
            
        Returns:
            Dictionary with learning path analysis
        """
        # Get unique trace variants
        trace_variants = {}
        
        for case_id in df['case:concept:name'].unique():
            case_data = df[df['case:concept:name'] == case_id].sort_values('time:timestamp')
            activities = case_data['concept:name'].tolist()
            
            # Create simplified trace (group consecutive same activities)
            simplified_trace = []
            prev_activity = None
            for activity in activities:
                if activity != prev_activity:
                    simplified_trace.append(activity)
                    prev_activity = activity
            
            trace_key = tuple(simplified_trace)
            if trace_key not in trace_variants:
                trace_variants[trace_key] = []
            trace_variants[trace_key].append(case_id)
        
        # Analyze variant popularity
        variant_counts = {trace: len(cases) for trace, cases in trace_variants.items()}
        popular_variants = sorted(variant_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Identify exercise progression patterns
        exercise_patterns = {}
        for case_id in df['case:concept:name'].unique():
            case_data = df[df['case:concept:name'] == case_id].sort_values('time:timestamp')
            
            if 'exercise' in case_data.columns:
                exercises = case_data['exercise'].dropna().unique()
                exercise_sequence = tuple(exercises)
                
                if exercise_sequence not in exercise_patterns:
                    exercise_patterns[exercise_sequence] = 0
                exercise_patterns[exercise_sequence] += 1
        
        learning_paths = {
            'total_variants': len(trace_variants),
            'most_common_paths': popular_variants[:10],
            'exercise_patterns': exercise_patterns,
            'variant_distribution': variant_counts
        }
        
        return learning_paths
    
    def analyze_performance_by_session(self, metrics_df: pd.DataFrame) -> Dict:
        """
        Analyze performance differences across sessions.
        
        Args:
            metrics_df: DataFrame with case metrics
            
        Returns:
            Dictionary with session-based performance analysis
        """
        if 'session' not in metrics_df.columns:
            return {'error': 'Session information not available'}
        
        session_analysis = {}
        
        for session in sorted(metrics_df['session'].unique()):
            session_data = metrics_df[metrics_df['session'] == session]
            
            session_stats = {
                'student_count': len(session_data),
                'avg_duration_hours': session_data['total_duration_hours'].mean(),
                'avg_events': session_data['total_events'].mean(),
                'avg_activity_diversity': session_data['activity_diversity'].mean(),
                'avg_clicks': session_data['total_clicks'].mean(),
                'avg_keystrokes': session_data['total_keystrokes'].mean(),
                'avg_idle_time_minutes': session_data['total_idle_time_minutes'].mean(),
                'deeds_usage': session_data['deeds_time_ratio'].mean(),
                'study_usage': session_data['study_time_ratio'].mean(),
                'texteditor_usage': session_data['texteditor_time_ratio'].mean()
            }
            
            session_analysis[f'Session_{session}'] = session_stats
        
        return session_analysis
    
    def identify_student_clusters(self, metrics_df: pd.DataFrame) -> Dict:
        """
        Identify clusters of students with similar learning behaviors.
        
        Args:
            metrics_df: DataFrame with case metrics
            
        Returns:
            Dictionary with clustering analysis
        """
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        # Select features for clustering
        feature_cols = [
            'total_duration_hours', 'activity_diversity', 'total_clicks',
            'total_keystrokes', 'deeds_time_ratio', 'study_time_ratio', 'texteditor_time_ratio'
        ]
        
        # Filter available features
        available_features = [col for col in feature_cols if col in metrics_df.columns]
        
        if len(available_features) < 3:
            return {'error': 'Insufficient features for clustering'}
        
        # Prepare data
        cluster_data = metrics_df[available_features].fillna(0)
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(cluster_data)
        
        # Perform clustering
        n_clusters = min(5, len(metrics_df) // 3)  # Ensure reasonable cluster count
        if n_clusters < 2:
            return {'error': 'Insufficient data for clustering'}
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(scaled_data)
        
        # Analyze clusters
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_data = metrics_df[clusters == i]
            
            cluster_stats = {
                'size': len(cluster_data),
                'avg_duration': cluster_data['total_duration_hours'].mean(),
                'avg_events': cluster_data['total_events'].mean(),
                'avg_diversity': cluster_data['activity_diversity'].mean(),
                'characteristics': {}
            }
            
            # Add feature-specific characteristics
            for feature in available_features:
                cluster_stats['characteristics'][feature] = cluster_data[feature].mean()
            
            cluster_analysis[f'Cluster_{i}'] = cluster_stats
        
        return {
            'clusters': cluster_analysis,
            'features_used': available_features,
            'n_clusters': n_clusters
        }
    
    def create_performance_visualizations(self, metrics_df: pd.DataFrame, patterns: Dict) -> None:
        """
        Create performance visualization charts.
        
        Args:
            metrics_df: DataFrame with case metrics
            patterns: Dictionary with activity patterns
        """
        # 1. Duration vs Events scatter plot
        plt.figure(figsize=(12, 8))
        plt.scatter(metrics_df['total_events'], metrics_df['total_duration_hours'], 
                   alpha=0.6, s=60)
        plt.xlabel('Total Events')
        plt.ylabel('Total Duration (Hours)')
        plt.title('Student Session Duration vs Activity Count')
        
        # Add trend line
        z = np.polyfit(metrics_df['total_events'], metrics_df['total_duration_hours'], 1)
        p = np.poly1d(z)
        plt.plot(metrics_df['total_events'], p(metrics_df['total_events']), "r--", alpha=0.8)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'duration_vs_events.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Activity diversity distribution
        plt.figure(figsize=(10, 6))
        plt.hist(metrics_df['activity_diversity'], bins=20, alpha=0.7, edgecolor='black')
        plt.xlabel('Activity Diversity (Unique Activities / Total Events)')
        plt.ylabel('Number of Students')
        plt.title('Distribution of Student Activity Diversity')
        plt.axvline(metrics_df['activity_diversity'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {metrics_df["activity_diversity"].mean():.3f}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'activity_diversity_distribution.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Learning activity ratios
        if 'session' in metrics_df.columns:
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            
            activity_types = ['deeds_time_ratio', 'study_time_ratio', 'texteditor_time_ratio']
            activity_labels = ['DEEDS Simulator', 'Study Materials', 'Text Editor']
            
            for i, (activity_type, label) in enumerate(zip(activity_types, activity_labels)):
                if activity_type in metrics_df.columns:
                    session_data = metrics_df.groupby('session')[activity_type].mean()
                    axes[i].bar(session_data.index, session_data.values)
                    axes[i].set_title(f'{label} Usage by Session')
                    axes[i].set_xlabel('Session')
                    axes[i].set_ylabel('Average Ratio')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'learning_activity_ratios.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 4. Hourly activity distribution
        if 'hourly_distribution' in patterns:
            plt.figure(figsize=(12, 6))
            hours = list(patterns['hourly_distribution'].keys())
            counts = list(patterns['hourly_distribution'].values())
            
            plt.bar(hours, counts, alpha=0.7)
            plt.xlabel('Hour of Day')
            plt.ylabel('Number of Activities')
            plt.title('Student Activity Distribution by Hour')
            plt.xticks(range(0, 24))
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'hourly_activity_distribution.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        print("Performance visualization charts created successfully")
    
    def generate_performance_report(self, metrics_df: pd.DataFrame, patterns: Dict, 
                                  learning_paths: Dict, session_analysis: Dict) -> str:
        """
        Generate a comprehensive performance analysis report.
        
        Args:
            metrics_df: DataFrame with case metrics
            patterns: Activity patterns analysis
            learning_paths: Learning paths analysis
            session_analysis: Session-based analysis
            
        Returns:
            String with formatted report
        """
        report = []
        report.append("=" * 60)
        report.append("EDUCATIONAL PROCESS MINING - PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Overall statistics
        report.append("\n1. OVERALL STATISTICS")
        report.append("-" * 30)
        report.append(f"Total Students Analyzed: {metrics_df['student_id'].nunique()}")
        report.append(f"Total Learning Sessions: {len(metrics_df)}")
        report.append(f"Average Session Duration: {metrics_df['total_duration_hours'].mean():.2f} hours")
        report.append(f"Average Events per Session: {metrics_df['total_events'].mean():.1f}")
        report.append(f"Average Activity Diversity: {metrics_df['activity_diversity'].mean():.3f}")
        
        # Activity patterns
        report.append("\n2. ACTIVITY PATTERNS")
        report.append("-" * 30)
        report.append("Top 5 Most Frequent Activities:")
        for i, (activity, count) in enumerate(list(patterns['activity_frequency'].items())[:5], 1):
            report.append(f"  {i}. {activity}: {count} occurrences")
        
        # Learning paths
        report.append("\n3. LEARNING PATH ANALYSIS")
        report.append("-" * 30)
        report.append(f"Total Unique Learning Paths: {learning_paths['total_variants']}")
        report.append("Most Common Learning Patterns:")
        for i, (path, count) in enumerate(learning_paths['most_common_paths'][:3], 1):
            path_str = " → ".join(path[:5]) + ("..." if len(path) > 5 else "")
            report.append(f"  {i}. {path_str} ({count} students)")
        
        # Session comparison
        if 'Session_1' in session_analysis:
            report.append("\n4. SESSION COMPARISON")
            report.append("-" * 30)
            for session, stats in session_analysis.items():
                report.append(f"{session}:")
                report.append(f"  Students: {stats['student_count']}")
                report.append(f"  Avg Duration: {stats['avg_duration_hours']:.2f} hours")
                report.append(f"  Avg Events: {stats['avg_events']:.1f}")
                report.append(f"  DEEDS Usage: {stats['deeds_usage']:.1%}")
                report.append("")
        
        # Performance insights
        report.append("\n5. KEY INSIGHTS")
        report.append("-" * 30)
        
        # Duration insights
        duration_median = metrics_df['total_duration_hours'].median()
        long_sessions = len(metrics_df[metrics_df['total_duration_hours'] > duration_median * 1.5])
        report.append(f"• {long_sessions} students had unusually long sessions (>1.5x median)")
        
        # Activity diversity insights
        diversity_median = metrics_df['activity_diversity'].median()
        diverse_students = len(metrics_df[metrics_df['activity_diversity'] > diversity_median * 1.5])
        report.append(f"• {diverse_students} students showed high activity diversity")
        
        # Learning tool preferences
        if 'deeds_time_ratio' in metrics_df.columns:
            deeds_preference = len(metrics_df[metrics_df['deeds_time_ratio'] > 0.5])
            study_preference = len(metrics_df[metrics_df['study_time_ratio'] > 0.3])
            report.append(f"• {deeds_preference} students heavily used DEEDS simulator (>50% time)")
            report.append(f"• {study_preference} students spent significant time on study materials (>30%)")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def run_complete_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Run complete performance analysis.
        
        Args:
            df: Event log DataFrame
            
        Returns:
            Dictionary with all analysis results
        """
        print("\n=== Starting Performance Analysis ===")
        
        # Calculate case metrics
        print("Calculating case-level metrics...")
        metrics_df = self.calculate_case_metrics(df)
        
        # Analyze activity patterns
        print("Analyzing activity patterns...")
        patterns = self.analyze_activity_patterns(df)
        
        # Identify learning paths
        print("Identifying learning paths...")
        learning_paths = self.identify_learning_paths(df)
        
        # Session-based analysis
        print("Analyzing performance by session...")
        session_analysis = self.analyze_performance_by_session(metrics_df)
        
        # Student clustering
        print("Performing student clustering...")
        try:
            clustering = self.identify_student_clusters(metrics_df)
        except ImportError:
            print("Scikit-learn not available for clustering analysis")
            clustering = {'error': 'Scikit-learn not installed'}
        
        # Create visualizations
        print("Creating performance visualizations...")
        self.create_performance_visualizations(metrics_df, patterns)
        
        # Generate report
        print("Generating performance report...")
        report = self.generate_performance_report(metrics_df, patterns, learning_paths, session_analysis)
        
        # Save report
        report_path = os.path.join(self.output_dir, 'performance_analysis_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Performance analysis complete. Report saved to {report_path}")
        
        return {
            'metrics': metrics_df,
            'patterns': patterns,
            'learning_paths': learning_paths,
            'session_analysis': session_analysis,
            'clustering': clustering,
            'report': report
        }


def main():
    """Test the performance analysis functionality."""
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
    
    # Run performance analysis
    analysis = PerformanceAnalysis()
    results = analysis.run_complete_analysis(quality_log)
    
    return results


if __name__ == "__main__":
    results = main()