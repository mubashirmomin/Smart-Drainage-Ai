"""
ai/assessment/severity.py - Defect Severity & Civil Repair Recommendation Engine

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Purpose: Evaluates individual defect severity on a standard Grade 1 (Minor) to Grade 5 (Critical)
scale based on municipal drainage inspection standards (CJJ 181 / WRc).
Calculates explainable severity scores from:
1. Defect Category & structural vs. hydraulic failure mode
2. Maximum cross-sectional bounding box area ratio (A_box / A_pipe)
3. Longitudinal persistence (duration in CCTV video)
4. Detection confidence
5. Prescribes specific, non-destructive rehabilitation actions (e.g. CIPP, Jetting, Root Cutting).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


# Civil Engineering Defect Taxonomy, Failure Modes, Base Multipliers, and Actions
DEFECT_RULES = {
    # STRUCTURAL DEFECTS
    "PL_Crack": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.25,
        "description": "Fracture or longitudinal/circumferential crack in pipe barrel",
        "collapse_risk_factor": 1.4,
        "repair_action": "Cured-In-Place Pipe (CIPP) patch relining or localized structural sleeve",
        "urgency_days": 45,
    },
    "BX_Deformation": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.40,
        "description": "Pipe barrel cross-section ovality or crown deflection",
        "collapse_risk_factor": 1.6,
        "repair_action": "Structural relining or targeted trenchless pipe bursting replacement",
        "urgency_days": 30,
    },
    "CK_Dislocation": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.20,
        "description": "Joint offset / shear displacement between pipe segments",
        "collapse_risk_factor": 1.3,
        "repair_action": "Internal robotic mechanical joint seal or chemical grout injection",
        "urgency_days": 60,
    },
    "CR_Disconnection": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.35,
        "description": "Open / pulled joint allowing soil bedding ingress",
        "collapse_risk_factor": 1.5,
        "repair_action": "Internal joint expansion sleeve and stabilization grouting",
        "urgency_days": 30,
    },
    "FS_Corrosion": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.15,
        "description": "Biogenic H2S acid corrosion or aggregate exposure",
        "collapse_risk_factor": 1.2,
        "repair_action": "Anti-corrosion spray polymer liner (polyurea/epoxy) or full CIPP inversion",
        "urgency_days": 90,
    },
    "QF_Defective_Joint": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.10,
        "description": "Joint spalling, cracked collar, or lateral interface defect",
        "collapse_risk_factor": 1.1,
        "repair_action": "Robotic point repair and chemical sealant injection",
        "urgency_days": 90,
    },
    "TL_Seal_Failure": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.10,
        "description": "Displaced or deteriorating rubber elastomeric gasket",
        "collapse_risk_factor": 1.1,
        "repair_action": "Mechanical inner band seal or chemical joint grouting",
        "urgency_days": 90,
    },
    "SL_Infiltration": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.30,
        "description": "Active groundwater intrusion through joints/cracks (bedding washout risk)",
        "collapse_risk_factor": 1.4,
        "repair_action": "Hydrophobic polyurethane chemical grout injection and structural sealing",
        "urgency_days": 30,
    },
    "AJ_Illicit_Tap": {
        "failure_mode": "STRUCTURAL",
        "base_weight": 1.20,
        "description": "Unauthorized lateral tap protruding into the main sewer line",
        "collapse_risk_factor": 1.2,
        "repair_action": "Robotic lateral cutter trimming and structural saddle reconnection",
        "urgency_days": 60,
    },

    # HYDRAULIC & MAINTENANCE DEFECTS
    "CJ_Sediment": {
        "failure_mode": "HYDRAULIC",
        "base_weight": 1.20,
        "description": "Silt, grit, grease, or sludge deposition reducing pipe invert capacity",
        "collapse_risk_factor": 1.0,
        "repair_action": "High-pressure hydrodynamic water jetting & vacuum extraction",
        "urgency_days": 15,
    },
    "SG_Root_Intrusion": {
        "failure_mode": "HYDRAULIC",
        "base_weight": 1.35,
        "description": "Tree root foliage penetrating pipe joint creating hydraulic dam",
        "collapse_risk_factor": 1.2,
        "repair_action": "Robotic chain flail / hydraulic root cutting + chemical foaming herbicide",
        "urgency_days": 15,
    },
    "TJ_Obstacle": {
        "failure_mode": "HYDRAULIC",
        "base_weight": 1.30,
        "description": "Protruding construction debris, rebar, rock, or hardened concrete slurry",
        "collapse_risk_factor": 1.1,
        "repair_action": "Heavy robotic milling tool removal and CCTV clearance verification",
        "urgency_days": 20,
    },
    "JG_Encrustation": {
        "failure_mode": "HYDRAULIC",
        "base_weight": 1.10,
        "description": "Hard mineral encrustation, calcite, or struvite deposit",
        "collapse_risk_factor": 1.0,
        "repair_action": "High-pressure descaling nozzle or robotic percussion milling",
        "urgency_days": 60,
    },
    "ZW_Foreign_Object": {
        "failure_mode": "HYDRAULIC",
        "base_weight": 1.25,
        "description": "Foreign utility line or dropped object penetrating pipe bore",
        "collapse_risk_factor": 1.2,
        "repair_action": "Utility coordination removal and robotic mechanical extraction",
        "urgency_days": 20,
    },
    "CQ_Sagging": {
        "failure_mode": "HYDRAULIC",
        "base_weight": 1.15,
        "description": "Pipe invert sag / belly causing stagnant water ponding and silt trapping",
        "collapse_risk_factor": 1.1,
        "repair_action": "Periodic scheduled flush jetting or localized regrading re-lay",
        "urgency_days": 90,
    },
}


def grade_from_score(score: float) -> Tuple[int, str]:
    """Map a 0-100 severity score to municipal Grades 1-5."""
    if score >= 80.0:
        return 5, "CRITICAL (Immediate Failure Risk)"
    elif score >= 60.0:
        return 4, "SEVERE (High Risk / Prompt Action)"
    elif score >= 40.0:
        return 3, "MODERATE (Medium Risk / Scheduled Repair)"
    elif score >= 20.0:
        return 2, "MILD (Low Risk / Periodic Monitoring)"
    else:
        return 1, "MINOR (Negligible / Acceptable)"


class DefectSeverityAssessor:
    """Calculates explainable severity metrics and repair actions for deduplicated defects."""

    def evaluate_defect(self, defect_data: Dict) -> Dict:
        """
        Evaluate a single deduplicated defect dictionary (from Phase 4 tracker).

        Input keys:
            class_name (str), peak_confidence (float), duration_sec (float),
            max_area_ratio (float), hits (int), defect_id (int)
        """
        cname = defect_data["class_name"]
        rule = DEFECT_RULES.get(cname, {
            "failure_mode": "OPERATIONAL",
            "base_weight": 1.0,
            "description": "Generic underground pipe defect",
            "collapse_risk_factor": 1.0,
            "repair_action": "Standard CCTV re-inspection and maintenance review",
            "urgency_days": 60,
        })

        area_ratio = float(defect_data.get("max_area_ratio", 0.0))
        duration_sec = float(defect_data.get("duration_sec", 0.5))
        confidence = float(defect_data.get("peak_confidence", 0.5))
        hits = int(defect_data.get("hits", 1))

        # Explainable Mathematical Formula:
        # 1. Area Factor: Area ratio is scaled. A defect occupying >15% of frame area is major.
        area_term = min(100.0, area_ratio * 400.0)

        # 2. Persistence / Length Factor: Continuous defects across time (e.g. 5+ seconds) carry higher weight.
        # Logarithmic saturation so a 10s defect doesn't produce infinity.
        import math
        pers_term = min(30.0, 10.0 * math.log(1.0 + duration_sec))

        # 3. Composite Raw Score weighted by engineering defect family weight and detection confidence
        base_w = rule["base_weight"]
        raw_score = (0.70 * area_term + 0.30 * pers_term) * base_w

        # Reliability scaling: confidence dampens uncertain detections
        reliability_factor = 0.5 + 0.5 * confidence
        severity_score = round(min(100.0, max(5.0, raw_score * reliability_factor)), 1)

        grade, grade_desc = grade_from_score(severity_score)

        return {
            "defect_id": defect_data.get("defect_id"),
            "class_name": cname,
            "failure_mode": rule["failure_mode"],
            "description": rule["description"],
            "severity_score": severity_score,
            "severity_grade": grade,
            "grade_description": grade_desc,
            "max_area_percentage": round(area_ratio * 100.0, 2),
            "persistence_seconds": round(duration_sec, 2),
            "detection_confidence": round(confidence, 2),
            "recommended_repair_action": rule["repair_action"],
            "target_resolution_days": rule["urgency_days"] if grade >= 3 else rule["urgency_days"] * 2,
            "thumbnail_path": defect_data.get("thumbnail_path"),
        }
