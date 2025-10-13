"""State machine for use case lifecycle management"""

from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class UseCaseState(Enum):
    """All possible states in the use case lifecycle"""

    # Initial setup
    TEMPLATE_GENERATION = "template_generation"
    TEMPLATE_SENT = "template_sent"

    # Configuration phase
    AWAITING_CONFIG = "awaiting_config"
    CONFIG_RECEIVED = "config_received"
    CONFIG_VALIDATION_RUNNING = "config_validation_running"
    CONFIG_INVALID = "config_invalid"

    # Quality check phase
    QUALITY_CHECK_RUNNING = "quality_check_running"
    QUALITY_CHECK_FAILED = "quality_check_failed"
    AWAITING_DATA_FIX = "awaiting_data_fix"
    QUALITY_CHECK_PASSED = "quality_check_passed"

    # Evaluation phase
    EVALUATION_QUEUED = "evaluation_queued"
    EVALUATION_RUNNING = "evaluation_running"
    EVALUATION_COMPLETED = "evaluation_completed"
    EVALUATION_FAILED = "evaluation_failed"

    # Terminal states
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


@dataclass
class StateTransitionMetadata:
    """Metadata attached to each state transition"""
    triggered_by: str  # user_id or "system"
    trigger_reason: str
    additional_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StateTransitionRule:
    """Rules for state transitions"""
    from_state: UseCaseState
    to_state: UseCaseState
    condition: Optional[Callable] = None  # Optional validation function
    side_effects: List[Callable] = field(default_factory=list)  # Actions to perform on transition


class UseCaseStateMachine:
    """
    State machine managing use case lifecycle

    Features:
    - Validated state transitions
    - State history tracking
    - Side effects (notifications, logging)
    - Conditional transitions
    - Rollback capability
    """

    # Define all valid transitions
    TRANSITIONS = [
        # Template generation flow
        StateTransitionRule(
            UseCaseState.TEMPLATE_GENERATION,
            UseCaseState.TEMPLATE_SENT
        ),
        StateTransitionRule(
            UseCaseState.TEMPLATE_SENT,
            UseCaseState.AWAITING_CONFIG
        ),

        # Configuration flow
        StateTransitionRule(
            UseCaseState.AWAITING_CONFIG,
            UseCaseState.CONFIG_RECEIVED
        ),
        StateTransitionRule(
            UseCaseState.CONFIG_RECEIVED,
            UseCaseState.CONFIG_VALIDATION_RUNNING
        ),
        StateTransitionRule(
            UseCaseState.CONFIG_VALIDATION_RUNNING,
            UseCaseState.CONFIG_INVALID
        ),
        StateTransitionRule(
            UseCaseState.CONFIG_VALIDATION_RUNNING,
            UseCaseState.QUALITY_CHECK_RUNNING
        ),
        StateTransitionRule(
            UseCaseState.CONFIG_INVALID,
            UseCaseState.AWAITING_CONFIG  # Allow resubmission
        ),

        # Quality check flow
        StateTransitionRule(
            UseCaseState.QUALITY_CHECK_RUNNING,
            UseCaseState.QUALITY_CHECK_FAILED
        ),
        StateTransitionRule(
            UseCaseState.QUALITY_CHECK_RUNNING,
            UseCaseState.QUALITY_CHECK_PASSED
        ),
        StateTransitionRule(
            UseCaseState.QUALITY_CHECK_FAILED,
            UseCaseState.AWAITING_DATA_FIX
        ),
        StateTransitionRule(
            UseCaseState.AWAITING_DATA_FIX,
            UseCaseState.CONFIG_RECEIVED  # Resubmit corrected data
        ),
        StateTransitionRule(
            UseCaseState.QUALITY_CHECK_PASSED,
            UseCaseState.EVALUATION_QUEUED
        ),

        # Evaluation flow
        StateTransitionRule(
            UseCaseState.EVALUATION_QUEUED,
            UseCaseState.EVALUATION_RUNNING
        ),
        StateTransitionRule(
            UseCaseState.EVALUATION_RUNNING,
            UseCaseState.EVALUATION_COMPLETED
        ),
        StateTransitionRule(
            UseCaseState.EVALUATION_RUNNING,
            UseCaseState.EVALUATION_FAILED
        ),
        StateTransitionRule(
            UseCaseState.EVALUATION_FAILED,
            UseCaseState.EVALUATION_QUEUED  # Allow retry
        ),

        # Terminal transitions
        StateTransitionRule(
            UseCaseState.EVALUATION_COMPLETED,
            UseCaseState.ARCHIVED
        ),
    ]

    # Build lookup map for fast access
    _TRANSITION_MAP: Dict[tuple, StateTransitionRule] = None

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
        use_case_id: str,
        initial_state: UseCaseState,
        state_history: Optional[List[tuple]] = None
    ):
        """
        Initialize state machine

        Args:
            use_case_id: Unique identifier
            initial_state: Starting state
            state_history: Optional existing history for reconstruction
        """
        self.__class__._build_transition_map()

        self.use_case_id = use_case_id
        self.current_state = initial_state

        if state_history:
            self.state_history = state_history
        else:
            self.state_history = [(initial_state, datetime.now(), None)]

    def can_transition_to(self, next_state: UseCaseState) -> bool:
        """
        Check if transition is valid

        Args:
            next_state: Target state

        Returns:
            True if transition is allowed
        """
        key = (self.current_state, next_state)
        return key in self._TRANSITION_MAP

    def get_allowed_transitions(self) -> List[UseCaseState]:
        """Get all states that can be transitioned to from current state"""
        allowed = []
        for (from_state, to_state), rule in self._TRANSITION_MAP.items():
            if from_state == self.current_state:
                allowed.append(to_state)
        return allowed

    def transition_to(
        self,
        next_state: UseCaseState,
        metadata: Optional[StateTransitionMetadata] = None,
        force: bool = False
    ) -> bool:
        """
        Transition to new state

        Args:
            next_state: Target state
            metadata: Transition metadata
            force: Skip validation (use with caution)

        Returns:
            True if transition successful

        Raises:
            ValueError: If transition is invalid
        """
        if not force and not self.can_transition_to(next_state):
            allowed = self.get_allowed_transitions()
            raise ValueError(
                f"Invalid transition from {self.current_state.value} to {next_state.value}. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )

        # Get transition rule
        key = (self.current_state, next_state)
        rule = self._TRANSITION_MAP.get(key)

        # Check condition if exists
        if rule and rule.condition and not rule.condition():
            logger.warning(
                f"Transition condition failed for {self.use_case_id}: "
                f"{self.current_state.value} -> {next_state.value}"
            )
            return False

        # Record transition
        old_state = self.current_state
        self.current_state = next_state
        self.state_history.append((next_state, datetime.now(), metadata))

        logger.info(
            f"Use case {self.use_case_id} transitioned: "
            f"{old_state.value} -> {next_state.value}"
        )

        # Execute side effects
        if rule and rule.side_effects:
            for effect in rule.side_effects:
                try:
                    effect(self.use_case_id, old_state, next_state, metadata)
                except Exception as e:
                    logger.error(
                        f"Side effect failed for use case {self.use_case_id}: {e}"
                    )

        return True

    def get_state_duration(self, state: UseCaseState) -> Optional[float]:
        """
        Get total time spent in a specific state (in seconds)

        Args:
            state: State to measure

        Returns:
            Duration in seconds, or None if state never entered
        """
        duration = 0.0
        entered_at = None

        for i, (hist_state, timestamp, _) in enumerate(self.state_history):
            if hist_state == state:
                entered_at = timestamp
            elif entered_at is not None:
                # Exited the state
                duration += (timestamp - entered_at).total_seconds()
                entered_at = None

        # If still in state
        if entered_at is not None:
            duration += (datetime.now() - entered_at).total_seconds()

        return duration if duration > 0 else None

    def get_current_state_duration(self) -> float:
        """Get time spent in current state (in seconds)"""
        if len(self.state_history) == 0:
            return 0.0

        last_transition_time = self.state_history[-1][1]
        return (datetime.now() - last_transition_time).total_seconds()

    def rollback(self, steps: int = 1) -> bool:
        """
        Rollback to previous state

        Args:
            steps: Number of steps to rollback

        Returns:
            True if rollback successful
        """
        if len(self.state_history) <= steps:
            logger.error(f"Cannot rollback {steps} steps, only {len(self.state_history)} in history")
            return False

        # Remove last N states
        for _ in range(steps):
            self.state_history.pop()

        # Set current state to last in history
        self.current_state = self.state_history[-1][0]

        logger.warning(
            f"Use case {self.use_case_id} rolled back {steps} steps to {self.current_state.value}"
        )

        return True

    def is_terminal_state(self) -> bool:
        """Check if current state is terminal (no further transitions)"""
        return self.current_state in [
            UseCaseState.EVALUATION_COMPLETED,
            UseCaseState.ARCHIVED,
            UseCaseState.CANCELLED
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state machine to dict"""
        return {
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
            'is_terminal': self.is_terminal_state()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UseCaseStateMachine':
        """Reconstruct state machine from dict"""
        state_history = [
            (
                UseCaseState(item['state']),
                datetime.fromisoformat(item['timestamp']),
                StateTransitionMetadata(**item['metadata']) if item['metadata'] else None
            )
            for item in data['state_history']
        ]

        return cls(
            use_case_id=data['use_case_id'],
            initial_state=UseCaseState(data['current_state']),
            state_history=state_history
        )


# Example side effects
def log_state_transition(
    use_case_id: str,
    from_state: UseCaseState,
    to_state: UseCaseState,
    metadata: StateTransitionMetadata
):
    """Side effect: Log state transition to activity log"""
    logger.info(f"Logged transition for {use_case_id}: {from_state.value} -> {to_state.value}")
    # In real implementation, would write to database activity_log table


def notify_on_quality_check_failure(
    use_case_id: str,
    from_state: UseCaseState,
    to_state: UseCaseState,
    metadata: StateTransitionMetadata
):
    """Side effect: Send notification when quality check fails"""
    if to_state == UseCaseState.QUALITY_CHECK_FAILED:
        logger.info(f"Triggering quality check failure notification for {use_case_id}")
        # In real implementation, would queue email task
