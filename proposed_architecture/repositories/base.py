"""Abstract base repository interfaces"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with common CRUD operations

    Generic type T represents the domain model
    """

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity"""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity"""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        pass

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all entities with pagination"""
        pass
