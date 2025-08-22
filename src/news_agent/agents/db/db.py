from abc import ABC, abstractmethod
from typing import Dict, List


class AbstractTrendDB(ABC):
    """Abstract interface for trend persistence"""

    @abstractmethod
    def save_trend(self, topic: str, summary: str, url: str, source: str):
        """Save a trend to the database"""
        pass

    @abstractmethod
    def get_unsent_trends(self) -> List[Dict]:
        """Return all trends where notified=False"""
        pass

    @abstractmethod
    def mark_as_sent(self, trend_id: int):
        """Mark a trend as sent/notified"""
        pass
