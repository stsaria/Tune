from dataclasses import dataclass
from enum import Enum

class ResponseType(Enum):
    HELLO = 0
    LOC_TIME_OUTED = 100

@dataclass
class Response:
    respType:ResponseType
    mainData:dict

@dataclass
class ResponseIdentify:
    ip:str
    port:int
    respId:str