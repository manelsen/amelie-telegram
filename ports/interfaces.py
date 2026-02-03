from abc import ABC, abstractmethod

class MessagingPort(ABC):
    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def send_message(self, chat_id: str, text: str):
        pass

class VisionModelPort(ABC):
    @abstractmethod
    async def describe_image(self, image_bytes: bytes) -> str:
        pass
