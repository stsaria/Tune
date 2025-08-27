from dataclasses import dataclass

@dataclass
class NodeInfo:
    ip:str
    port:int
    name:str
    pubKey:str
    def getIPColonPort(self) -> str:
        return f"{self.ip}:{self.port}"

@classmethod
class MyInfo(NodeInfo):
    pivKey:str