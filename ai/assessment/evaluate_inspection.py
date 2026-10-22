"""
ai/assessment/evaluate_inspection.py - Unified Condition Assessment & Priority Dispatch CLI

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Purpose: Evaluates CCTV inspection results (output from Phase 4 tracking) to generate:
1. Individual defect severity classifications (Grade 1 to Grade 5).
2. Recommended rehabilitation and repair techniques (CIPP, jetting, robotic milling).
3. Hydraulic blockage percentage and urban flood/monsoon surcharge risk.
4. Pipe Condition Index (PCI 0-100), SCI (Structural), OCI (Operational).
5. Work Order Priority Queue tier (P1: Emergency, P2: High, P3: Medium, P4: Routine).
6. Generates full municipal condition_assessment.json audit dossier.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from ai.assessment.severity import DefectSeverityAssessor
from ai.assessment.blockage import HydraulicBlockageAssessor
from ai.assessment.condition_index import PipeConditionEvaluator


def evaluate_inspection_file(
    inspection_json_path: str,
    output_path: str = None,
) -> Dict:
    """
    Run complete civil condition assessment on an inspection_summary.json file.
    """
    in_file = Path(inspection_json_path).resolve()
    if not in_file.exists():
        raise FileNotFoundError(f"Inspection summary not found at {in_file}")

    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    unique_defects = data.get("unique_defects", [])
    quality_info = data.get("quality_assessment", {})
    video_meta = data.get("video_metadata", {})
    degraded_pct = quality_info.get("degraded_percentage", 0.0)

    # 1. Evaluate Individual Defect Severities
    severity_assessor = DefectSeverityAssessor()
    evaluated_defects = [severity_assessor.evaluate_defect(d) for d in unique_defects]

    # 2. Evaluate Hydraulic Blockage & Flow Capacity
    blockage_assessor = HydraulicBlockageAssessor()
    blockage_report = blockage_assessor.evaluate_blockage(evaluated_defects)

    # 3. Evaluate Pipe Condition Index (PCI) & Work Order Priority
    condition_evaluator = PipeConditionEvaluator()
    condition_report = condition_evaluator.evaluate_pipe_health(
        evaluated_defects=evaluated_defects,
        blockage_report=blockage_report,
        optical_quality_degraded_pct=degraded_pct,
    )

    # 4. Compile Full Executive Dossier
    final_dossier = {
        "asset_inspection_meta": {
            "video_file": video_meta.get("filename", in_file.stem),
            "video_duration_seconds": video_meta.get("duration_seconds", 0.0),
            "total_frames_analyzed": video_meta.get("total_frames", 0),
            "inspection_optical_status": quality_info.get("overall_status", "ACCEPTABLE"),
            "degraded_footage_pct": degraded_pct,
        },
        "pipe_health_indices": {
            "pci_overall_score": condition_report["pci_score"],
            "condition_state": condition_report["condition_state"],
            "condition_description": condition_report["condition_description"],
            "structural_index_sci": condition_report["structural_index_sci"],
            "operational_index_oci": condition_report["operational_index_oci"],
        },
        "hydraulic_conveyance_assessment": blockage_report,
        "maintenance_dispatch_prioritization": {
            "work_order_priority": condition_report["work_order_priority"],
            "sla_target_timeframe": condition_report["sla_timeframe"],
            "dispatch_rationale": condition_report["priority_rationale"],
            "max_defect_grade_observed": condition_report["max_defect_grade"],
            "critical_defects_count": condition_report["critical_defects_count"],
        },
        "detailed_defect_inventory": evaluated_defects,
    }

    if output_path is None:
        output_path = in_file.parent / "condition_assessment.json"
    else:
        output_path = Path(output_path).resolve()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_dossier, f, indent=2)

    # Print Executive Summary Banner
    print("=" * 70)
    print("  AI Sewer Intelligence - Municipal Condition Assessment Report")
    print("=" * 70)
    print(f"Inspection Video    : {video_meta.get('filename')}")
    print(f"Optical Quality     : {quality_info.get('overall_status')} ({degraded_pct}% degraded)")
    print("-" * 70)
    print(f"Pipe Condition (PCI): {condition_report['pci_score']}/100 [{condition_report['condition_state']}]")
    print(f"Structural (SCI)    : {condition_report['structural_index_sci']}/100")
    print(f"Hydraulic (OCI)     : {condition_report['operational_index_oci']}/100")
    print(f"Blockage Risk       : {blockage_report['blockage_percentage']}% ({blockage_report['blockage_severity_tier']})")
    print(f"Monsoon Flood Risk  : {blockage_report['monsoon_overflow_risk']}")
    print("-" * 70)
    print(f"WORK ORDER PRIORITY : {condition_report['work_order_priority']} (Target: {condition_report['sla_timeframe']})")
    print(f"Priority Rationale  : {condition_report['priority_rationale']}")
    print("=" * 70)

    print("\nConfirmed Physical Defect Inventory:")
    if evaluated_defects:
        print(f"{'ID':>2} {'Class':<18} {'Mode':<11} {'Area%':>6} {'Score':>6} {'Grade':<8} {'Recommended Action'}")
        print("-" * 70)
        for d in evaluated_defects:
            print(f"{d['defect_id']:>2} {d['class_name']:<18} {d['failure_mode']:<11} {d['max_area_percentage']:>5.1f}% {d['severity_score']:>6.1f} G{d['severity_grade']} ({d['grade_description'][:8]}) {d['recommended_repair_action']}")
    else:
        print("  No physical defects detected. Pipe is clear.")

    print("\n" + "=" * 70)
    print(f"Full Assessment JSON Dossier Saved to: {output_path}")
    print("=" * 70)

    return final_dossier


def main():
    parser = argparse.ArgumentParser(description="Evaluate municipal condition assessment from inspection summary.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(PROJECT_ROOT / "mlops" / "experiments" / "tracking_output" / "inspection_summary.json"),
        help="Path to input inspection_summary.json.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "mlops" / "experiments" / "tracking_output" / "condition_assessment.json"),
        help="Path to output condition_assessment.json.",
    )
    args = parser.parse_args()
    evaluate_inspection_file(args.input, args.output)


if __name__ == "__main__":
    main()
