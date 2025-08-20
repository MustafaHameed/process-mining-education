"""
Data preprocessing module for EPM (Educational Process Mining) dataset.
Extracts and prepares the educational process data for PM4Py analysis.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')


class EPMDataProcessor:
    """Class to handle EPM dataset extraction and preprocessing for process mining."""
    
    def __init__(self, dataset_path: str = "EPM Dataset 2"):
        """
        Initialize the data processor.
        
        Args:
            dataset_path: Path to the EPM dataset directory
        """
        self.dataset_path = dataset_path
        self.processes_path = os.path.join(dataset_path, "Data", "Processes")
        self.sessions = ["Session 1", "Session 2", "Session 3", "Session 4", "Session 5", "Session 6"]
        
    def load_student_data(self, session: str, student_id: str) -> pd.DataFrame:
        """
        Load data for a specific student in a specific session.
        
        Args:
            session: Session folder name (e.g., "Session 1")
            student_id: Student ID as string
            
        Returns:
            DataFrame with student's process data
        """
        file_path = os.path.join(self.processes_path, session, student_id)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()
            
        try:
            # Read CSV data with proper column names
            columns = ['session', 'student_id', 'exercise', 'activity', 'start_time', 
                      'end_time', 'idle_time', 'mouse_wheel', 'mouse_wheel_click',
                      'mouse_click_left', 'mouse_click_right', 'mouse_movement', 'keystroke']
            
            df = pd.read_csv(file_path, header=None, names=columns)
            
            # Parse timestamps
            df['start_time'] = pd.to_datetime(df['start_time'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
            df['end_time'] = pd.to_datetime(df['end_time'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
            
            # Calculate duration in seconds
            df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds()
            
            # Add case ID (combining student and session)
            df['case_id'] = f"Student_{student_id}_Session_{df['session'].iloc[0]}"
            
            return df
            
        except Exception as e:
            print(f"Error loading data for student {student_id} in {session}: {e}")
            return pd.DataFrame()
    
    def load_all_data(self) -> pd.DataFrame:
        """
        Load data for all students across all sessions.
        
        Returns:
            Combined DataFrame with all student data
        """
        all_data = []
        
        print("Loading EPM dataset...")
        for session in self.sessions:
            session_path = os.path.join(self.processes_path, session)
            if not os.path.exists(session_path):
                continue
                
            student_files = os.listdir(session_path)
            print(f"Loading {session}: {len(student_files)} students")
            
            for student_file in student_files:
                if student_file.isdigit():  # Only process numeric student IDs
                    student_data = self.load_student_data(session, student_file)
                    if not student_data.empty:
                        all_data.append(student_data)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"Loaded {len(combined_df)} events from {len(all_data)} student-session combinations")
            return combined_df
        else:
            print("No data loaded!")
            return pd.DataFrame()
    
    def create_event_log(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert raw data to event log format for PM4Py.
        
        Args:
            df: Raw student data DataFrame
            
        Returns:
            Event log DataFrame with proper PM4Py format
        """
        if df.empty:
            return df
            
        # Create event log format
        event_log = df.copy()
        
        # Rename columns for PM4Py compatibility
        event_log = event_log.rename(columns={
            'case_id': 'case:concept:name',
            'activity': 'concept:name',
            'start_time': 'time:timestamp'
        })
        
        # Clean activity names (remove leading/trailing spaces)
        event_log['concept:name'] = event_log['concept:name'].str.strip()
        
        # Filter out invalid timestamps
        event_log = event_log.dropna(subset=['time:timestamp'])
        
        # Sort by case and timestamp
        event_log = event_log.sort_values(['case:concept:name', 'time:timestamp'])
        
        # Add event index within case
        event_log['event_index'] = event_log.groupby('case:concept:name').cumcount() + 1
        
        print(f"Created event log with {len(event_log)} events and {event_log['case:concept:name'].nunique()} cases")
        
        return event_log
    
    def get_activity_mapping(self) -> Dict[str, str]:
        """
        Get mapping of activity codes to descriptive names.
        
        Returns:
            Dictionary mapping activity codes to descriptions
        """
        activity_info_path = os.path.join(self.dataset_path, "activities_info.txt")
        
        # Basic activity mapping based on the dataset documentation
        activity_mapping = {
            'Study_Es': 'Studying Exercise Content',
            'Deeds_Es': 'Working in DEEDS Simulator',
            'Deeds': 'DEEDS Related Activities',
            'TextEditor_Es': 'Writing Exercise Solutions',
            'TextEditor': 'Text Editor Activities',
            'Diagram': 'Timing Diagram Simulation',
            'Properties': 'Setting Component Properties',
            'Study_Materials': 'Viewing Study Materials',
            'FSM_Es': 'Finite State Machine Exercises',
            'FSM_Related': 'FSM Related Activities',
            'Aulaweb': 'Learning Management System',
            'Blank': 'Blank Page',
            'Other': 'Other Activities'
        }
        
        return activity_mapping
    
    def get_basic_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate basic statistics about the dataset.
        
        Args:
            df: Event log DataFrame
            
        Returns:
            Dictionary with basic statistics
        """
        if df.empty:
            return {}
            
        stats = {
            'total_events': len(df),
            'total_cases': df['case:concept:name'].nunique(),
            'total_activities': df['concept:name'].nunique(),
            'total_students': df['student_id'].nunique(),
            'total_sessions': df['session'].nunique(),
            'date_range': {
                'start': df['time:timestamp'].min(),
                'end': df['time:timestamp'].max()
            },
            'avg_events_per_case': len(df) / df['case:concept:name'].nunique(),
            'activity_distribution': df['concept:name'].value_counts().to_dict()
        }
        
        return stats
    
    def filter_by_criteria(self, df: pd.DataFrame, 
                          min_events_per_case: int = 5,
                          exclude_activities: List[str] = None) -> pd.DataFrame:
        """
        Filter event log by various criteria for quality.
        
        Args:
            df: Event log DataFrame
            min_events_per_case: Minimum number of events per case
            exclude_activities: List of activities to exclude
            
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
            
        filtered_df = df.copy()
        
        # Exclude specified activities
        if exclude_activities:
            filtered_df = filtered_df[~filtered_df['concept:name'].isin(exclude_activities)]
            print(f"Excluded activities: {exclude_activities}")
        
        # Filter cases with minimum events
        case_counts = filtered_df['case:concept:name'].value_counts()
        valid_cases = case_counts[case_counts >= min_events_per_case].index
        filtered_df = filtered_df[filtered_df['case:concept:name'].isin(valid_cases)]
        
        print(f"Filtered to {len(filtered_df)} events and {filtered_df['case:concept:name'].nunique()} cases")
        print(f"Excluded {len(df) - len(filtered_df)} events below quality threshold")
        
        return filtered_df


def main():
    """Test the data preprocessing functionality."""
    processor = EPMDataProcessor()
    
    # Load all data
    raw_data = processor.load_all_data()
    
    if raw_data.empty:
        print("No data loaded. Please check the dataset path.")
        return
    
    # Create event log
    event_log = processor.create_event_log(raw_data)
    
    # Get basic statistics
    stats = processor.get_basic_statistics(event_log)
    
    print("\n=== EPM Dataset Statistics ===")
    print(f"Total Events: {stats['total_events']:,}")
    print(f"Total Cases: {stats['total_cases']:,}")
    print(f"Total Students: {stats['total_students']:,}")
    print(f"Total Sessions: {stats['total_sessions']:,}")
    print(f"Total Activities: {stats['total_activities']:,}")
    print(f"Average Events per Case: {stats['avg_events_per_case']:.1f}")
    print(f"Date Range: {stats['date_range']['start']} to {stats['date_range']['end']}")
    
    print("\n=== Top 10 Activities ===")
    for activity, count in list(stats['activity_distribution'].items())[:10]:
        print(f"{activity}: {count:,}")
    
    # Filter data for quality
    quality_log = processor.filter_by_criteria(
        event_log, 
        min_events_per_case=10,
        exclude_activities=['Blank', 'Other']
    )
    
    print(f"\n=== Quality Filtered Data ===")
    print(f"Events: {len(quality_log):,}")
    print(f"Cases: {quality_log['case:concept:name'].nunique():,}")
    
    return event_log, quality_log


if __name__ == "__main__":
    event_log, quality_log = main()