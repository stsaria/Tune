from dataclasses import dataclass

@dataclass
class NodeInfo:
    ip:str
    port:int
    pubKey:str
    def getIpColonPort(self) -> str:
        return f"{self.ip}:{self.port}"