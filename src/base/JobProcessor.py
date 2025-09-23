from abc import ABC, abstractmethod

class JobProcessor(ABC):
    @abstractmethod
    def recved(self, data:bytes, addr:tuple[str, int]) -> None:
        pass
