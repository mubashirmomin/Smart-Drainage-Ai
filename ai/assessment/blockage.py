"""
ai/assessment/blockage.py - Hydraulic Blockage Risk & Discharge Capacity Engine

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Purpose: Evaluates municipal stormwater and sewer hydraulic conveyance capacity from CCTV detections.
Calculates:
1. Cross-sectional flow impediment percentage (%) caused by sediment, root dams, and obstacles.
2. Estimated discharge capacity reduction (Manning's flow reduction factor).
3. Monsoon surcharge and urban flooding vulnerability tier (LOW, MODERATE, HIGH, SEVERE).
4. Immediate hydrodynamic jetting / root clearing dispatch recommendations.
"""

from typing import Dict, List


# Multipliers for flow obstruction based on hydraulic turbulence and sediment geometry
BLOCKAGE_COEFFICIENTS = {
    "CJ_Sediment": 1.25,        # Invert sediment bed alters wetted perimeter and Manning roughness
    "SG_Root_Intrusion": 1.45,   # Fibrous root curtains trap debris and create major flow dams
    "TJ_Obstacle": 1.50,         # Rigid obstruction creates local turbulent choke and backwater
    "JG_Encrustation": 1.10,     # Circumferential mineral scale narrows hydraulic radius
    "ZW_Foreign_Object": 1.35,   # Utilities/foreign objects snag ragging and solids
    "CQ_Sagging": 1.20,          # Belly holds dead water volume and triggers accelerated silting
}


class HydraulicBlockageAssessor:
    """Calculates hydraulic conveyance impediment and urban overflow risks."""

    def evaluate_blockage(self, evaluated_defects: List[Dict]) -> Dict:
        """
        Evaluate hydraulic blockage from list of evaluated defect dictionaries.
        """
        blockage_defects = [
            d for d in evaluated_defects
            if d.get("class_name") in BLOCKAGE_COEFFICIENTS
        ]

        if not blockage_defects:
            return {
                "blockage_percentage": 0.0,
                "blockage_severity_tier": "NORMAL / UNRESTRICTED",
                "estimated_flow_loss_pct": 0.0,
                "monsoon_overflow_risk": "MINIMAL",
                "flow_impeding_defects_count": 0,
                "primary_blockage_cause": "NONE",
                "immediate_cleaning_required": False,
                "recommended_hydraulic_action": "Pipe is hydraulically clear. Standard routine monitoring.",
            }

        # Calculate peak cross-sectional reduction
        # Area percentage is from bounding box relative to frame
        max_choke_pct = 0.0
        weighted_choke_pct = 0.0
        causes = {}

        for d in blockage_defects:
            cname = d["class_name"]
            coeff = BLOCKAGE_COEFFICIENTS.get(cname, 1.0)
            area_pct = d.get("max_area_percentage", 0.0)

            # Hydraulic obstruction calculation (area ratio multiplied by obstruction turbulence factor)
            effective_choke = min(95.0, area_pct * coeff * 1.5)
            if effective_choke > max_choke_pct:
                max_choke_pct = effective_choke

            weighted_choke_pct += effective_choke * 0.4
            causes[cname] = causes.get(cname, 0) + 1

        # Composite blockage percentage bounded between [0.0, 95.0]
        final_blockage_pct = round(min(95.0, max(max_choke_pct, weighted_choke_pct)), 1)

        # Discharge capacity loss calculation based on Manning's open channel flow reduction
        # Flow reduction scales super-linearly with cross-sectional loss
        flow_loss_pct = round(min(98.0, final_blockage_pct * 1.15), 1)

        # Risk classification
        if final_blockage_pct >= 60.0:
            tier = "CRITICAL CHOKE (>60% Blocked)"
            monsoon_risk = "SEVERE (Immediate Monsoon Overflow / Surcharging Hazard)"
            action = "EMERGENCY: Dispatch high-capacity jetter-vacuum suction unit immediately."
            immediate_cleaning = True
        elif final_blockage_pct >= 40.0:
            tier = "SUBSTANTIAL OBSTRUCTION (40-60% Blocked)"
            monsoon_risk = "HIGH (Vulnerable to Street-Level Inundation During Peak Rain)"
            action = "HIGH PRIORITY: Schedule hydrodynamic jetting and root cutting within 14 days."
            immediate_cleaning = True
        elif final_blockage_pct >= 20.0:
            tier = "MODERATE RESTRICTION (20-40% Blocked)"
            monsoon_risk = "MODERATE (Capacity Deficit during High Intensity Storms)"
            action = "SCHEDULED: Include in upcoming municipal pre-monsoon desilting drive."
            immediate_cleaning = False
        else:
            tier = "MINOR RESTRICTION (<20% Blocked)"
            monsoon_risk = "LOW (Negligible Hydraulic Impact)"
            action = "MONITOR: Re-inspect during annual CCTV review cycle."
            immediate_cleaning = False

        primary_cause = max(causes, key=causes.get) if causes else "NONE"

        return {
            "blockage_percentage": final_blockage_pct,
            "blockage_severity_tier": tier,
            "estimated_flow_loss_pct": flow_loss_pct,
            "monsoon_overflow_risk": monsoon_risk,
            "flow_impeding_defects_count": len(blockage_defects),
            "primary_blockage_cause": primary_cause,
            "immediate_cleaning_required": immediate_cleaning,
            "recommended_hydraulic_action": action,
        }
