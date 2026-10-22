"""
ai/assessment/condition_index.py - Pipe Condition Index (PCI) & Work Order Prioritization Engine

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Purpose: Evaluates aggregate pipe segment health on a standard 0 to 100 scale:
1. Pipe Condition Index (PCI): Overall health metric.
2. Structural Condition Index (SCI): Structural integrity and collapse resistance.
3. Operational Condition Index (OCI): Hydraulic cleanliness and free-flow capacity.
4. Maintenance Work Order Priority Queue (P1: Emergency to P4: Routine Monitoring).
"""

from typing import Dict, List, Tuple


def classify_pci(score: float) -> Tuple[str, str]:
    """Map 0-100 PCI score to asset health state."""
    if score >= 85.0:
        return "EXCELLENT", "Pristine pipe segment; no structural or hydraulic distress."
    elif score >= 70.0:
        return "GOOD", "Minor superficial defects; pipe functioning within normal design parameters."
    elif score >= 50.0:
        return "FAIR", "Moderate deterioration detected; scheduled preventive maintenance required."
    elif score >= 30.0:
        return "POOR", "Significant defect accumulation; priority rehabilitation needed to prevent failure."
    else:
        return "CRITICAL", "High collapse or blockage risk; immediate emergency intervention mandatory."


class PipeConditionEvaluator:
    """Computes aggregate asset condition indices and assigns work order priority."""

    def evaluate_pipe_health(
        self,
        evaluated_defects: List[Dict],
        blockage_report: Dict,
        optical_quality_degraded_pct: float = 0.0,
    ) -> Dict:
        """
        Compute PCI, SCI, OCI, and determine dispatch priority queue tier.
        """
        base_pci = 100.0
        base_sci = 100.0
        base_oci = 100.0

        structural_deductions = 0.0
        operational_deductions = 0.0

        max_defect_grade = 0
        critical_defects_count = 0

        for d in evaluated_defects:
            sev_score = d["severity_score"]
            grade = d["severity_grade"]
            max_defect_grade = max(max_defect_grade, grade)

            if grade >= 4:
                critical_defects_count += 1

            # Deductions scale non-linearly with severity
            deduction = (sev_score ** 1.15) * 0.18

            if d["failure_mode"] == "STRUCTURAL":
                structural_deductions += deduction
            else:
                operational_deductions += deduction

        # Optical inspection penalty (if >20% of footage was degraded, reduce confidence)
        inspection_confidence_penalty = 0.0
        if optical_quality_degraded_pct >= 20.0:
            inspection_confidence_penalty = 5.0

        # Calculate bounded Indices
        sci = round(max(5.0, min(100.0, base_sci - structural_deductions)), 1)
        oci = round(max(5.0, min(100.0, base_oci - operational_deductions - (blockage_report.get("blockage_percentage", 0.0) * 0.4))), 1)

        # Overall PCI is weighted composite (60% structural + 40% operational)
        pci = round(max(5.0, min(100.0, (0.60 * sci + 0.40 * oci) - inspection_confidence_penalty)), 1)
        condition_state, condition_desc = classify_pci(pci)

        # Work Order Priority Determination (P1 to P4)
        blockage_pct = blockage_report.get("blockage_percentage", 0.0)

        if max_defect_grade == 5 or pci < 30.0 or blockage_pct >= 60.0 or any(d["class_name"] == "BX_Deformation" and d["severity_grade"] >= 4 for d in evaluated_defects):
            priority = "P1_EMERGENCY"
            sla_timeframe = "24 - 48 Hours"
            rationale = "Imminent collapse, major void/sinkhole formation hazard, or severe hydraulic surcharge risk."
        elif max_defect_grade == 4 or pci < 50.0 or blockage_pct >= 40.0:
            priority = "P2_HIGH_PRIORITY"
            sla_timeframe = "14 - 30 Days"
            rationale = "Severe localized structural crack/disconnection or heavy sediment/root blockage requiring prompt intervention."
        elif max_defect_grade == 3 or pci < 70.0 or blockage_pct >= 20.0:
            priority = "P3_MEDIUM_PRIORITY"
            sla_timeframe = "60 - 90 Days"
            rationale = "Moderate wear or flow impediment suitable for scheduled quarterly maintenance / pre-monsoon cycle."
        else:
            priority = "P4_ROUTINE_MONITORING"
            sla_timeframe = "Annual Review Cycle (12 Months)"
            rationale = "Minor superficial defects; pipe is structurally sound and operating at full conveyance capacity."

        return {
            "pci_score": pci,
            "condition_state": condition_state,
            "condition_description": condition_desc,
            "structural_index_sci": sci,
            "operational_index_oci": oci,
            "max_defect_grade": max_defect_grade,
            "critical_defects_count": critical_defects_count,
            "work_order_priority": priority,
            "sla_timeframe": sla_timeframe,
            "priority_rationale": rationale,
        }
