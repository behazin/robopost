from abc import ABC, abstractmethod
from ..models import Article, Platform

class BasePublisher(ABC):

    @staticmethod
    @abstractmethod
    def publish(credentials: dict, article: Article):
        """Publishes the article to the specific platform."""
        pass

def get_publisher(platform: Platform) -> "BasePublisher" | None:
    """
    Factory function to get the publisher class for a given platform.
    This approach with local imports inside the function prevents circular dependencies.
    """
    from .telegram_publisher import TelegramPublisher
    from .wordpress_publisher import WordpressPublisher

    if platform == Platform.TELEGRAM:
        return TelegramPublisher
    if platform == Platform.WORDPRESS:
        return WordpressPublisher
    
    # To add a new publisher, implement the class and add it here.
    return None