"""State machine for model evaluation lifecycle within a use case"""

from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class ModelEvaluationState(Enum):
    """All possible states for a model evaluation within a use case"""

    # Initial states
    REGISTERED = "registered"  # Model registered, waiting for use case to be ready

    # Quality check phase (specific to this model's evaluation)
    QUALITY_CHECK_PENDING = "quality_check_pending"  # Waiting to run QC
    QUALITY_CHECK_RUNNING = "quality_check_running"  # QC in progress
    QUALITY_CHECK_PASSED = "quality_check_passed"    # QC passed, ready for eval
    QUALITY_CHECK_FAILED = "quality_check_failed"    # QC failed, needs data fix
    AWAITING_DATA_FIX = "awaiting_data_fix"          # Waiting for team to fix data

    # Evaluation phase
    EVALUATION_QUEUED = "evaluation_queued"          # Ready to evaluate
    EVALUATION_RUNNING = "evaluation_running"        # Evaluation in progress
    EVALUATION_COMPLETED = "evaluation_completed"    # Evaluation done successfully
    EVALUATION_FAILED = "evaluation_failed"          # Evaluation failed (technical error)

    # Terminal states
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


@dataclass
class ModelStateTransitionMetadata:
    """Metadata for model state transitions"""
    triggered_by: str  # user_id or "system"
    trigger_reason: str
    file_uploaded: Optional[str] = None  # Path to uploaded file if relevant
    quality_issues_count: Optional[int] = None
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelStateTransitionRule:
    """Rules for model state transitions"""
    from_state: ModelEvaluationState
    to_state: ModelEvaluationState
    condition: Optional[Callable] = None
    side_effects: List[Callable] = field(default_factory=list)


class ModelEvaluationStateMachine:
    """
    State machine for individual model evaluation lifecycle

    Each model registered under a use case has its own state machine.
    This allows:
    - Multiple models to be evaluated independently
    - Different models to be in different states
    - Model-specific quality checks and evaluations
    - Independent retries and fixes for each model
    """

    # Define all valid transitions
    TRANSITIONS = [
        # Initial registration to quality check
        ModelStateTransitionRule(
            ModelEvaluationState.REGISTERED,
            ModelEvaluationState.QUALITY_CHECK_PENDING
        ),

        # Quality check flow
        ModelStateTransitionRule(
            ModelEvaluationState.QUALITY_CHECK_PENDING,
            ModelEvaluationState.QUALITY_CHECK_RUNNING
        ),
        ModelStateTransitionRule(
            ModelEvaluationState.QUALITY_CHECK_RUNNING,
            ModelEvaluationState.QUALITY_CHECK_PASSED
        ),
        ModelStateTransitionRule(
            ModelEvaluationState.QUALITY_CHECK_RUNNING,
            ModelEvaluationState.QUALITY_CHECK_FAILED
        ),

        # Quality check failure handling
        ModelStateTransitionRule(
            ModelEvaluationState.QUALITY_CHECK_FAILED,
            ModelEvaluationState.AWAITING_DATA_FIX
        ),
        ModelStateTransitionRule(
            ModelEvaluationState.AWAITING_DATA_FIX,
            ModelEvaluationState.QUALITY_CHECK_PENDING  # Rerun QC after fix
        ),

        # From passed QC to evaluation
        ModelStateTransitionRule(
            ModelEvaluationState.QUALITY_CHECK_PASSED,
            ModelEvaluationState.EVALUATION_QUEUED
        ),

        # Evaluation flow
        ModelStateTransitionRule(
            ModelEvaluationState.EVALUATION_QUEUED,
            ModelEvaluationState.EVALUATION_RUNNING
        ),
        ModelStateTransitionRule(
            ModelEvaluationState.EVALUATION_RUNNING,
            ModelEvaluationState.EVALUATION_COMPLETED
        ),
        ModelStateTransitionRule(
            ModelEvaluationState.EVALUATION_RUNNING,
            ModelEvaluationState.EVALUATION_FAILED
        ),

        # Retry failed evaluation
        ModelStateTransitionRule(
            ModelEvaluationState.EVALUATION_FAILED,
            ModelEvaluationState.EVALUATION_QUEUED  # Allow retry
        ),

        # Terminal transitions
        ModelStateTransitionRule(
            ModelEvaluationState.EVALUATION_COMPLETED,
            ModelEvaluationState.ARCHIVED
        ),
    ]

    # Build lookup map
    _TRANSITION_MAP: Dict[tuple, ModelStateTransitionRule] = None

    @classmethod
    def _build_transition_map(cls):
        """Build transition lookup map"""
        if cls._TRANSITION_MAP is None:
            cls._TRANSITION_MAP = {}
            for rule in cls.TRANSITIONS:
                key = (rule.from_state, rule.to_state)
                cls._TRANSITION_MAP[key] = rule

    def __init__(
        self,
        model_id: str,
        use_case_id: str,
        initial_state: ModelEvaluationState,
        state_history: Optional[List[tuple]] = None
    ):
        """
        Initialize model state machine

        Args:
            model_id: Model identifier
            use_case_id: Parent use case identifier
            initial_state: Starting state
            state_history: Optional existing history
        """
        self.__class__._build_transition_map()

        self.model_id = model_id
        self.use_case_id = use_case_id
        self.current_state = initial_state

        if state_history:
            self.state_history = state_history
        else:
            self.state_history = [(initial_state, datetime.now(), None)]

    def can_transition_to(self, next_state: ModelEvaluationState) -> bool:
        """Check if transition is valid"""
        key = (self.current_state, next_state)
        return key in self._TRANSITION_MAP

    def get_allowed_transitions(self) -> List[ModelEvaluationState]:
        """Get all states that can be transitioned to from current state"""
        allowed = []
        for (from_state, to_state), rule in self._TRANSITION_MAP.items():
            if from_state == self.current_state:
                allowed.append(to_state)
        return allowed

    def transition_to(
        self,
        next_state: ModelEvaluationState,
        metadata: Optional[ModelStateTransitionMetadata] = None,
        force: bool = False
    ) -> bool:
        """
        Transition to new state

        Args:
            next_state: Target state
            metadata: Transition metadata
            force: Skip validation

        Returns:
            True if transition successful
        """
        if not force and not self.can_transition_to(next_state):
            allowed = self.get_allowed_transitions()
            raise ValueError(
                f"Invalid transition for model {self.model_id}: "
                f"{self.current_state.value} -> {next_state.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        # Get transition rule
        key = (self.current_state, next_state)
        rule = self._TRANSITION_MAP.get(key)

        # Check condition
        if rule and rule.condition and not rule.condition():
            logger.warning(
                f"Transition condition failed for model {self.model_id}: "
                f"{self.current_state.value} -> {next_state.value}"
            )
            return False

        # Record transition
        old_state = self.current_state
        self.current_state = next_state
        self.state_history.append((next_state, datetime.now(), metadata))

        logger.info(
            f"Model {self.model_id} (use case {self.use_case_id}) transitioned: "
            f"{old_state.value} -> {next_state.value}"
        )

        # Execute side effects
        if rule and rule.side_effects:
            for effect in rule.side_effects:
                try:
                    effect(self.model_id, self.use_case_id, old_state, next_state, metadata)
                except Exception as e:
                    logger.error(f"Side effect failed for model {self.model_id}: {e}")

        return True

    def is_terminal_state(self) -> bool:
        """Check if in terminal state"""
        return self.current_state in [
            ModelEvaluationState.EVALUATION_COMPLETED,
            ModelEvaluationState.ARCHIVED,
            ModelEvaluationState.CANCELLED
        ]

    def is_blocked(self) -> bool:
        """Check if model is blocked waiting for action"""
        return self.current_state in [
            ModelEvaluationState.AWAITING_DATA_FIX,
            ModelEvaluationState.QUALITY_CHECK_FAILED
        ]

    def can_start_evaluation(self) -> bool:
        """Check if model can start evaluation"""
        return self.current_state in [
            ModelEvaluationState.QUALITY_CHECK_PASSED,
            ModelEvaluationState.EVALUATION_QUEUED
        ]

    def get_current_state_duration(self) -> float:
        """Get time spent in current state (seconds)"""
        if len(self.state_history) == 0:
            return 0.0
        last_transition_time = self.state_history[-1][1]
        return (datetime.now() - last_transition_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'model_id': self.model_id,
            'use_case_id': self.use_case_id,
            'current_state': self.current_state.value,
            'state_history': [
                {
                    'state': state.value,
                    'timestamp': timestamp.isoformat(),
                    'metadata': metadata.__dict__ if metadata else None
                }
                for state, timestamp, metadata in self.state_history
            ],
            'current_state_duration_seconds': self.get_current_state_duration(),
            'is_terminal': self.is_terminal_state(),
            'is_blocked': self.is_blocked()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelEvaluationStateMachine':
        """Reconstruct from dict"""
        state_history = [
            (
                ModelEvaluationState(item['state']),
                datetime.fromisoformat(item['timestamp']),
                ModelStateTransitionMetadata(**item['metadata']) if item['metadata'] else None
            )
            for item in data['state_history']
        ]

        return cls(
            model_id=data['model_id'],
            use_case_id=data['use_case_id'],
            initial_state=ModelEvaluationState(data['current_state']),
            state_history=state_history
        )


# Side effects for model state transitions

def log_model_state_transition(
    model_id: str,
    use_case_id: str,
    from_state: ModelEvaluationState,
    to_state: ModelEvaluationState,
    metadata: ModelStateTransitionMetadata
):
    """Log model state transition"""
    logger.info(
        f"Model {model_id} transition logged: {from_state.value} -> {to_state.value}"
    )
    # In real implementation, write to activity_log table


def notify_on_quality_check_failure(
    model_id: str,
    use_case_id: str,
    from_state: ModelEvaluationState,
    to_state: ModelEvaluationState,
    metadata: ModelStateTransitionMetadata
):
    """Notify team when quality check fails for a model"""
    if to_state == ModelEvaluationState.QUALITY_CHECK_FAILED:
        logger.info(f"Triggering QC failure notification for model {model_id}")
        # Queue email notification


def trigger_evaluation_on_qc_pass(
    model_id: str,
    use_case_id: str,
    from_state: ModelEvaluationState,
    to_state: ModelEvaluationState,
    metadata: ModelStateTransitionMetadata
):
    """Automatically queue evaluation when QC passes"""
    if to_state == ModelEvaluationState.QUALITY_CHECK_PASSED:
        logger.info(f"Auto-queueing evaluation for model {model_id}")
        # Automatically transition to EVALUATION_QUEUED
