"""Domain enums"""

from enum import Enum


class TaskType(Enum):
    """Types of evaluation tasks"""
    ENTITY_EXTRACTION = "entity_extraction"
    CLASSIFICATION = "classification"
    CLASSIFICATION_AND_EXTRACTION = "classification_and_extraction"
    SUMMARIZATION = "summarization"
    CONTEXT_REWRITING = "context_rewriting"


class IssueSeverity(Enum):
    """Severity levels for quality issues"""
    ERROR = "error"        # Blocks evaluation
    WARNING = "warning"    # Doesn't block, but should be reviewed
    INFO = "info"          # Informational only
