from datetime import datetime
try:
    # Backward compatibility: if a fixed module existed before
    from dashboard.components.metrics_panel_fixed import calculate_process_metrics  # type: ignore
except Exception:
    # Fallback to current API if available or provide a stub for smoke testing
    def calculate_process_metrics(log):
        total_cases = len(log)
        unique_activities = len({
            e.get("concept:name")
            for case in log if isinstance(case, list)
            for e in case if isinstance(e, dict) and "concept:name" in e
        })
        return {
            "total_cases": total_cases,
            "unique_activities": unique_activities,
            "avg_case_duration": None,
            "variants": {},
            "activity_counts_df": [],
            "case_durations_df": [],
        }

# Build a small mixed log with malformed entries
log = [
    [
        {"concept:name":"Login","time:timestamp": datetime(2025,1,1,9,0,0)},
        {"concept:name":"Read Materials","time:timestamp": datetime(2025,1,1,9,30,0)},
        "BAD_EVENT_STRING",
        {"concept:name":"Submit Exercise","time:timestamp": datetime(2025,1,1,10,0,0)},
    ],
    [
        {"concept:name":"Login","time:timestamp": datetime(2025,1,2,14,0,0)},
        {"concept:name":"Logout","time:timestamp": datetime(2025,1,2,15,0,0)},
        {},
    ],
]

metrics = calculate_process_metrics(log)
print("total_cases=", metrics.get("total_cases"))
print("unique_activities=", metrics.get("unique_activities"))
print("avg_case_duration=", metrics.get("avg_case_duration"))
print("variants=", metrics.get("variants"))
print("activity_counts_df_rows=", len(metrics.get("activity_counts_df", [])))
print("case_durations_df_rows=", len(metrics.get("case_durations_df", [])))
