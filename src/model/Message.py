from dataclasses import dataclass
from src.util import sha256

Node = any

@dataclass
class RootMessage:
    from src.net.Node import Node
    content:str
    timestamp:int
    author:Node=None
    def hash(self):
        return sha256.hash(f"{self.content}{self.timestamp}")

@dataclass
class ReplyMessage:
    content:str
    timestamp:int

    fromNode:Node
    fromHash:str

    author:Node=None
    def hash(self):
        return sha256.hash(f"{self.content}{self.timestamp}{self.fromNode.getNodeInfo().getPubKey()}{self.fromHash}")