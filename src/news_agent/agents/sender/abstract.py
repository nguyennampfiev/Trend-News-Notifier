from abc import ABC, abstractmethod


class AbstractSender(ABC):
    """
    Abstract base class for sender agents.
    """

    @abstractmethod
    async def send(self, recipient: str, content: dict) -> bool:
        """
        Send content to a specified recipient.

        Args:
            content (str): The content to be sent.
            recipient (str): The recipient's identifier (e.g., email, phone number).

        Returns:
            bool: True if the content was sent successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def configure(self, settings: dict) -> None:
        """
        Configure the sender with necessary settings.

        Args:
            settings (dict): A dictionary of configuration settings.
        """
        pass
