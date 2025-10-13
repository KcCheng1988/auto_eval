"""Use case repository interface"""

from typing import List, Optional, Dict, Any
from abc import abstractmethod
from .base import BaseRepository
from ..domain.models import UseCase
from ..domain.state_machine import UseCaseState


class UseCaseRepository(BaseRepository[UseCase]):
    """Abstract repository for use case operations"""

    @abstractmethod
    def get_by_state(self, state: UseCaseState, limit: int = 100) -> List[UseCase]:
        """Get use cases by state"""
        pass

    @abstractmethod
    def get_by_team_email(self, email: str, limit: int = 100) -> List[UseCase]:
        """Get use cases by team email"""
        pass

    @abstractmethod
    def get_pending_evaluation_queue(self) -> List[UseCase]:
        """Get use cases queued for evaluation, ordered by priority"""
        pass

    @abstractmethod
    def get_stale_use_cases(self, days: int = 7) -> List[UseCase]:
        """Get use cases stuck in same state for too long"""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 100) -> List[UseCase]:
        """Full-text search on use case name"""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        pass
