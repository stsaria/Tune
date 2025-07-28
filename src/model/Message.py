from dataclasses import dataclass

from src.net.Node import Node
from src.util import sha256


@dataclass
class Message:
    content:str
    timestamp:int
    def hash(self):
        return sha256.hash(f"{self.content}{self.timestamp}")

@dataclass
class ReplyMessage:
    content:str
    timestamp:int

    fromNode:Node
    fromHash:str
    def hash(self):
        return sha256.hash(f"{self.content}{self.timestamp}{self.fromNode.getNodeInfo().getPubKey()}{self.fromHash}")