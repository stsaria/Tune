from dataclasses import dataclass

from src.base.Protocol import CommuType
from src.util import sha256

@dataclass
class Response:
    respType:CommuType
    mainData:dict

@dataclass
class ResponseIdentify:
    ip:str
    port:int
    respId:str
    def hash(self):
        return sha256.hash(f"{self.ip}{self.port}{self.respId}")