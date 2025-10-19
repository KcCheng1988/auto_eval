"""
Domain layer - Core business models and logic

This package contains:
- Domain models (entities and value objects)
- State machines (workflow management)
- Business enums

Import structure:
    from proposed_architecture.domain import UseCase, Model, EvaluationResult
    from proposed_architecture.domain import QualityIssue, ActivityLog
    from proposed_architecture.domain import TaskType, IssueSeverity
    from proposed_architecture.domain import UseCaseState, UseCaseStateMachine
    from proposed_architecture.domain import ModelEvaluationState, ModelEvaluationStateMachine
"""

# Domain models
from .use_case import UseCase
from .model import Model
from .evaluation_result import EvaluationResult
from .quality_check import QualityIssue
from .activity_log import ActivityLog

# Enums
from .enums import TaskType, IssueSeverity

# State machines and states
from .state_machine import (
    UseCaseState,
    UseCaseStateMachine,
    StateTransitionMetadata,
    StateTransitionRule
)
from .model_state_machine import (
    ModelEvaluationState,
    ModelEvaluationStateMachine,
    ModelStateTransitionMetadata,
    ModelStateTransitionRule
)

__all__ = [
    # Domain models
    'UseCase',
    'Model',
    'EvaluationResult',
    'QualityIssue',
    'ActivityLog',

    # Enums
    'TaskType',
    'IssueSeverity',

    # Use case state machine
    'UseCaseState',
    'UseCaseStateMachine',
    'StateTransitionMetadata',
    'StateTransitionRule',

    # Model evaluation state machine
    'ModelEvaluationState',
    'ModelEvaluationStateMachine',
    'ModelStateTransitionMetadata',
    'ModelStateTransitionRule',
]
