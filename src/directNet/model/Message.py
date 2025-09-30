from dataclasses import dataclass

from src.allNet.util import sha256

@dataclass
class Message:
    content: str
    timestamp: int
    def hash(self):
        return sha256.hash(f"{self.content}{self.timestamp}")