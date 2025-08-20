"""
Conformance checking module for educational process mining.
Analyzes how well actual student behavior conforms to expected educational processes.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import pm4py
import os
import warnings
warnings.filterwarnings('ignore')


class ConformanceChecker:
    """Class for checking conformance between actual and expected educational processes."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize conformance checker.
        
        Args:
            output_dir: Directory to save outputs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def define_reference_model(self) -> Dict:
        """
        Define expected educational process patterns based on domain knowledge.
        
        Returns:
            Dictionary with reference process patterns
        """
        # Define expected learning sequences for digital electronics course
        reference_patterns = {
            'ideal_exercise_sequence': [
                'Study_Es_1_1',      # Study exercise content
                'Deeds_Es_1_1',      # Work in simulator
                'TextEditor_Es_1_1', # Document solution
                'Study_Es_1_2',      # Move to next exercise
                'Deeds_Es_1_2',
                'TextEditor_Es_1_2'
            ],
            
            'expected_transitions': {
                # Common expected activity transitions
                ('Study_Es_1_1', 'Deeds_Es_1_1'): 'study_to_practice',
                ('Deeds_Es_1_1', 'TextEditor_Es_1_1'): 'practice_to_document',
                ('Study_Es_1_2', 'Deeds_Es_1_2'): 'study_to_practice',
                ('Deeds_Es_1_2', 'TextEditor_Es_1_2'): 'practice_to_document',
                ('Aulaweb', 'Study_Es_1_1'): 'platform_to_study',
                ('TextEditor_Es_1_1', 'Study_Es_1_2'): 'progression_to_next',
                ('Properties', 'Deeds_Es_1_1'): 'setup_to_practice',
                ('Diagram', 'TextEditor_Es_1_1'): 'verification_to_document'
            },
            
            'activity_categories': {
                'preparation': ['Aulaweb', 'Study_Materials'],
                'study': ['Study_Es_1_1', 'Study_Es_1_2', 'Study_Es_1_3'],
                'practice': ['Deeds_Es_1_1', 'Deeds_Es_1_2', 'Deeds_Es_1_3', 'Deeds'],
                'verification': ['Diagram', 'Properties'],
                'documentation': ['TextEditor_Es_1_1', 'TextEditor_Es_1_2', 'TextEditor_Es_1_3', 'TextEditor'],
                'other': ['FSM_Es', 'FSM_Related']
            },
            
            'quality_indicators': {
                'min_study_time_ratio': 0.1,     # At least 10% time on study activities
                'min_practice_time_ratio': 0.2,   # At least 20% time on practice
                'max_other_time_ratio': 0.3,      # No more than 30% on other activities
                'expected_exercise_progression': ['Es_1_1', 'Es_1_2', 'Es_1_3']
            }
        }
        
        return reference_patterns
    
    def calculate_sequence_conformance(self, df: pd.DataFrame, reference_patterns: Dict) -> Dict:
        """
        Calculate conformance based on activity sequences.
        
        Args:
            df: Event log DataFrame
            reference_patterns: Reference process patterns
            
        Returns:
            Dictionary with sequence conformance analysis
        """
        conformance_results = {}
        expected_transitions = reference_patterns['expected_transitions']
        
        for case_id in df['case:concept:name'].unique():
            case_data = df[df['case:concept:name'] == case_id].sort_values('time:timestamp')
            activities = case_data['concept:name'].tolist()
            
            # Calculate transition conformance
            case_transitions = []
            for i in range(len(activities) - 1):
                case_transitions.append((activities[i], activities[i+1]))
            
            # Count expected vs unexpected transitions
            expected_count = 0
            unexpected_transitions = []
            
            for transition in case_transitions:
                if transition in expected_transitions:
                    expected_count += 1
                else:
                    unexpected_transitions.append(transition)
            
            total_transitions = len(case_transitions)
            conformance_ratio = expected_count / total_transitions if total_transitions > 0 else 0
            
            # Check exercise progression
            exercises_encountered = []
            for activity in activities:
                if 'Es_1_' in activity:
                    exercise_num = activity.split('Es_1_')[-1].split('_')[0]
                    if exercise_num.isdigit() and exercise_num not in exercises_encountered:
                        exercises_encountered.append(exercise_num)
            
            # Check if exercises were done in order
            expected_order = reference_patterns['quality_indicators']['expected_exercise_progression']
            exercise_order_correct = all(
                exercises_encountered[i] <= exercises_encountered[i+1] 
                for i in range(len(exercises_encountered)-1)
            ) if len(exercises_encountered) > 1 else True
            
            conformance_results[case_id] = {
                'total_transitions': total_transitions,
                'expected_transitions': expected_count,
                'conformance_ratio': conformance_ratio,
                'unexpected_transitions': unexpected_transitions,
                'exercises_encountered': exercises_encountered,
                'exercise_order_correct': exercise_order_correct,
                'conformance_score': conformance_ratio * 0.7 + (1 if exercise_order_correct else 0) * 0.3
            }
        
        return conformance_results
    
    def calculate_behavioral_conformance(self, df: pd.DataFrame, reference_patterns: Dict) -> Dict:
        """
        Calculate conformance based on behavioral patterns and time allocation.
        
        Args:
            df: Event log DataFrame
            reference_patterns: Reference process patterns
            
        Returns:
            Dictionary with behavioral conformance analysis
        """
        behavioral_results = {}
        activity_categories = reference_patterns['activity_categories']
        quality_indicators = reference_patterns['quality_indicators']
        
        for case_id in df['case:concept:name'].unique():
            case_data = df[df['case:concept:name'] == case_id]
            total_events = len(case_data)
            
            # Calculate time allocation per category
            category_ratios = {}
            for category, activities in activity_categories.items():
                category_events = len(case_data[case_data['concept:name'].isin(activities)])
                category_ratios[category] = category_events / total_events if total_events > 0 else 0
            
            # Check against quality indicators
            conformance_checks = {
                'sufficient_study': category_ratios.get('study', 0) >= quality_indicators['min_study_time_ratio'],
                'sufficient_practice': category_ratios.get('practice', 0) >= quality_indicators['min_practice_time_ratio'],
                'limited_other': category_ratios.get('other', 0) <= quality_indicators['max_other_time_ratio']
            }
            
            # Calculate overall behavioral conformance
            conformance_score = sum(conformance_checks.values()) / len(conformance_checks)
            
            behavioral_results[case_id] = {
                'category_ratios': category_ratios,
                'conformance_checks': conformance_checks,
                'behavioral_conformance_score': conformance_score,
                'total_events': total_events
            }
        
        return behavioral_results
    
    def identify_deviations(self, sequence_conformance: Dict, behavioral_conformance: Dict) -> Dict:
        """
        Identify and categorize process deviations.
        
        Args:
            sequence_conformance: Sequence conformance results
            behavioral_conformance: Behavioral conformance results
            
        Returns:
            Dictionary with deviation analysis
        """
        deviations = {
            'low_sequence_conformance': [],
            'poor_exercise_progression': [],
            'insufficient_study_time': [],
            'insufficient_practice_time': [],
            'excessive_other_activities': [],
            'overall_low_conformance': []
        }
        
        # Identify different types of deviations
        for case_id in sequence_conformance.keys():
            seq_conf = sequence_conformance[case_id]
            beh_conf = behavioral_conformance[case_id]
            
            # Low sequence conformance
            if seq_conf['conformance_ratio'] < 0.3:
                deviations['low_sequence_conformance'].append({
                    'case_id': case_id,
                    'conformance_ratio': seq_conf['conformance_ratio'],
                    'unexpected_transitions': len(seq_conf['unexpected_transitions'])
                })
            
            # Poor exercise progression
            if not seq_conf['exercise_order_correct']:
                deviations['poor_exercise_progression'].append({
                    'case_id': case_id,
                    'exercises_encountered': seq_conf['exercises_encountered']
                })
            
            # Behavioral deviations
            if not beh_conf['conformance_checks']['sufficient_study']:
                deviations['insufficient_study_time'].append({
                    'case_id': case_id,
                    'study_ratio': beh_conf['category_ratios'].get('study', 0)
                })
            
            if not beh_conf['conformance_checks']['sufficient_practice']:
                deviations['insufficient_practice_time'].append({
                    'case_id': case_id,
                    'practice_ratio': beh_conf['category_ratios'].get('practice', 0)
                })
            
            if not beh_conf['conformance_checks']['limited_other']:
                deviations['excessive_other_activities'].append({
                    'case_id': case_id,
                    'other_ratio': beh_conf['category_ratios'].get('other', 0)
                })
            
            # Overall low conformance
            overall_score = (seq_conf['conformance_score'] + beh_conf['behavioral_conformance_score']) / 2
            if overall_score < 0.5:
                deviations['overall_low_conformance'].append({
                    'case_id': case_id,
                    'overall_score': overall_score,
                    'sequence_score': seq_conf['conformance_score'],
                    'behavioral_score': beh_conf['behavioral_conformance_score']
                })
        
        return deviations
    
    def create_conformance_visualizations(self, sequence_conformance: Dict, 
                                        behavioral_conformance: Dict, deviations: Dict) -> None:
        """
        Create visualizations for conformance analysis.
        
        Args:
            sequence_conformance: Sequence conformance results
            behavioral_conformance: Behavioral conformance results
            deviations: Deviation analysis results
        """
        # 1. Conformance score distribution
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Sequence conformance distribution
        seq_scores = [result['conformance_score'] for result in sequence_conformance.values()]
        axes[0, 0].hist(seq_scores, bins=20, alpha=0.7, edgecolor='black')
        axes[0, 0].set_title('Sequence Conformance Score Distribution')
        axes[0, 0].set_xlabel('Conformance Score')
        axes[0, 0].set_ylabel('Number of Students')
        axes[0, 0].axvline(np.mean(seq_scores), color='red', linestyle='--', 
                          label=f'Mean: {np.mean(seq_scores):.3f}')
        axes[0, 0].legend()
        
        # Behavioral conformance distribution
        beh_scores = [result['behavioral_conformance_score'] for result in behavioral_conformance.values()]
        axes[0, 1].hist(beh_scores, bins=20, alpha=0.7, edgecolor='black', color='orange')
        axes[0, 1].set_title('Behavioral Conformance Score Distribution')
        axes[0, 1].set_xlabel('Conformance Score')
        axes[0, 1].set_ylabel('Number of Students')
        axes[0, 1].axvline(np.mean(beh_scores), color='red', linestyle='--',
                          label=f'Mean: {np.mean(beh_scores):.3f}')
        axes[0, 1].legend()
        
        # Conformance correlation
        axes[1, 0].scatter(seq_scores, beh_scores, alpha=0.6)
        axes[1, 0].set_title('Sequence vs Behavioral Conformance')
        axes[1, 0].set_xlabel('Sequence Conformance Score')
        axes[1, 0].set_ylabel('Behavioral Conformance Score')
        
        # Add trend line
        z = np.polyfit(seq_scores, beh_scores, 1)
        p = np.poly1d(z)
        axes[1, 0].plot(seq_scores, p(seq_scores), "r--", alpha=0.8)
        
        # Deviation summary
        deviation_counts = [len(deviations[key]) for key in deviations.keys()]
        deviation_labels = [key.replace('_', ' ').title() for key in deviations.keys()]
        
        axes[1, 1].bar(range(len(deviation_counts)), deviation_counts, alpha=0.7)
        axes[1, 1].set_title('Types of Process Deviations')
        axes[1, 1].set_xlabel('Deviation Type')
        axes[1, 1].set_ylabel('Number of Cases')
        axes[1, 1].set_xticks(range(len(deviation_labels)))
        axes[1, 1].set_xticklabels(deviation_labels, rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'conformance_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Activity category allocation heatmap
        case_ids = list(behavioral_conformance.keys())
        categories = list(next(iter(behavioral_conformance.values()))['category_ratios'].keys())
        
        # Create matrix of category ratios
        ratio_matrix = []
        for case_id in case_ids:
            ratios = [behavioral_conformance[case_id]['category_ratios'].get(cat, 0) for cat in categories]
            ratio_matrix.append(ratios)
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(ratio_matrix, 
                   xticklabels=categories, 
                   yticklabels=[f"Student {i+1}" for i in range(len(case_ids))],
                   cmap='YlOrRd', 
                   annot=False)
        plt.title('Activity Category Allocation by Student')
        plt.xlabel('Activity Category')
        plt.ylabel('Students')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'activity_category_heatmap.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Conformance visualization charts created successfully")
    
    def generate_conformance_report(self, sequence_conformance: Dict, behavioral_conformance: Dict, 
                                  deviations: Dict, reference_patterns: Dict) -> str:
        """
        Generate comprehensive conformance checking report.
        
        Args:
            sequence_conformance: Sequence conformance results
            behavioral_conformance: Behavioral conformance results
            deviations: Deviation analysis results
            reference_patterns: Reference process patterns
            
        Returns:
            String with formatted report
        """
        report = []
        report.append("=" * 60)
        report.append("EDUCATIONAL PROCESS MINING - CONFORMANCE ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Overall conformance statistics
        seq_scores = [result['conformance_score'] for result in sequence_conformance.values()]
        beh_scores = [result['behavioral_conformance_score'] for result in behavioral_conformance.values()]
        
        report.append("\n1. OVERALL CONFORMANCE STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Cases Analyzed: {len(sequence_conformance)}")
        report.append(f"Average Sequence Conformance: {np.mean(seq_scores):.3f}")
        report.append(f"Average Behavioral Conformance: {np.mean(beh_scores):.3f}")
        report.append(f"Standard Deviation (Sequence): {np.std(seq_scores):.3f}")
        report.append(f"Standard Deviation (Behavioral): {np.std(beh_scores):.3f}")
        
        # High conformance cases
        high_seq_conformance = sum(1 for score in seq_scores if score > 0.7)
        high_beh_conformance = sum(1 for score in beh_scores if score > 0.7)
        report.append(f"High Sequence Conformance (>0.7): {high_seq_conformance} cases")
        report.append(f"High Behavioral Conformance (>0.7): {high_beh_conformance} cases")
        
        # Deviation analysis
        report.append("\n2. DEVIATION ANALYSIS")
        report.append("-" * 40)
        total_cases = len(sequence_conformance)
        
        for deviation_type, cases in deviations.items():
            percentage = (len(cases) / total_cases) * 100
            report.append(f"{deviation_type.replace('_', ' ').title()}: {len(cases)} cases ({percentage:.1f}%)")
        
        # Most common deviations
        report.append("\n3. MOST COMMON DEVIATIONS")
        report.append("-" * 40)
        
        if deviations['low_sequence_conformance']:
            report.append("Students with Low Sequence Conformance:")
            for case in deviations['low_sequence_conformance'][:5]:  # Top 5
                report.append(f"  • {case['case_id']}: {case['conformance_ratio']:.3f} conformance ratio")
        
        if deviations['insufficient_study_time']:
            report.append("\nStudents with Insufficient Study Time:")
            for case in deviations['insufficient_study_time'][:5]:
                report.append(f"  • {case['case_id']}: {case['study_ratio']:.1%} study time")
        
        # Best practices identification
        report.append("\n4. BEST PRACTICES IDENTIFIED")
        report.append("-" * 40)
        
        # Find cases with high conformance
        best_seq_cases = [case_id for case_id, result in sequence_conformance.items() 
                         if result['conformance_score'] > 0.8]
        best_beh_cases = [case_id for case_id, result in behavioral_conformance.items() 
                         if result['behavioral_conformance_score'] > 0.8]
        
        best_overall_cases = list(set(best_seq_cases) & set(best_beh_cases))
        
        report.append(f"Students Following Best Practices: {len(best_overall_cases)}")
        if best_overall_cases:
            report.append("Characteristics of High-Conformance Students:")
            for case_id in best_overall_cases[:3]:
                seq_score = sequence_conformance[case_id]['conformance_score']
                beh_score = behavioral_conformance[case_id]['behavioral_conformance_score']
                report.append(f"  • {case_id}: Seq={seq_score:.3f}, Beh={beh_score:.3f}")
        
        # Recommendations
        report.append("\n5. RECOMMENDATIONS FOR IMPROVEMENT")
        report.append("-" * 40)
        
        if len(deviations['insufficient_study_time']) > len(sequence_conformance) * 0.3:
            report.append("• Encourage more time on study materials before practical exercises")
        
        if len(deviations['poor_exercise_progression']) > len(sequence_conformance) * 0.2:
            report.append("• Provide clearer guidance on exercise progression order")
        
        if len(deviations['low_sequence_conformance']) > len(sequence_conformance) * 0.4:
            report.append("• Consider providing process guidelines or templates for students")
        
        if len(deviations['excessive_other_activities']) > len(sequence_conformance) * 0.3:
            report.append("• Reduce distractions and focus student attention on core activities")
        
        # Reference model summary
        report.append("\n6. REFERENCE MODEL SUMMARY")
        report.append("-" * 40)
        report.append("Expected Learning Process:")
        for step in reference_patterns['ideal_exercise_sequence']:
            report.append(f"  → {step}")
        
        report.append(f"\nQuality Thresholds Used:")
        for indicator, value in reference_patterns['quality_indicators'].items():
            if isinstance(value, float):
                report.append(f"  • {indicator}: {value:.1%}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def run_complete_conformance_check(self, df: pd.DataFrame) -> Dict:
        """
        Run complete conformance checking analysis.
        
        Args:
            df: Event log DataFrame
            
        Returns:
            Dictionary with all conformance analysis results
        """
        print("\n=== Starting Conformance Checking ===")
        
        # Define reference model
        print("Defining reference educational process model...")
        reference_patterns = self.define_reference_model()
        
        # Calculate sequence conformance
        print("Calculating sequence conformance...")
        sequence_conformance = self.calculate_sequence_conformance(df, reference_patterns)
        
        # Calculate behavioral conformance
        print("Calculating behavioral conformance...")
        behavioral_conformance = self.calculate_behavioral_conformance(df, reference_patterns)
        
        # Identify deviations
        print("Identifying process deviations...")
        deviations = self.identify_deviations(sequence_conformance, behavioral_conformance)
        
        # Create visualizations
        print("Creating conformance visualizations...")
        self.create_conformance_visualizations(sequence_conformance, behavioral_conformance, deviations)
        
        # Generate report
        print("Generating conformance report...")
        report = self.generate_conformance_report(sequence_conformance, behavioral_conformance, 
                                                deviations, reference_patterns)
        
        # Save report
        report_path = os.path.join(self.output_dir, 'conformance_analysis_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Conformance analysis complete. Report saved to {report_path}")
        
        return {
            'reference_patterns': reference_patterns,
            'sequence_conformance': sequence_conformance,
            'behavioral_conformance': behavioral_conformance,
            'deviations': deviations,
            'report': report
        }


def main():
    """Test the conformance checking functionality."""
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
    
    # Run conformance checking
    checker = ConformanceChecker()
    results = checker.run_complete_conformance_check(quality_log)
    
    return results


if __name__ == "__main__":
    results = main()