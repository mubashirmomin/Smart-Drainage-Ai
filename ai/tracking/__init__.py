"""
ai/tracking - Video frame processing, defect tracking, deduplication, and quality assessment.
"""
from ai.tracking.quality import VideoQualityAssessor
from ai.tracking.deduplicator import DefectDeduplicator, DefectRecord
from ai.tracking.video_analyzer import SewerVideoAnalyzer

__all__ = ["VideoQualityAssessor", "DefectDeduplicator", "DefectRecord", "SewerVideoAnalyzer"]
