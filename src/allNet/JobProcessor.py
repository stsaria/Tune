from abc import ABC, abstractmethod

from src.allNet.ExecOp import ExecOp

class JobProcessor(ABC):
    @abstractmethod
    @classmethod
    def recved(self, data:bytes, addr:tuple[str, int]) -> tuple[ExecOp, dict] | None:
        pass
