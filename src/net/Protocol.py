from dataclasses import dataclass
from enum import Enum

class CommuType(Enum):
    HELLO = 0
    RESPONSE = 1



    LOC_TIME_OUTED = 200

    ERR_I_DONT_KNOW_YOUR_REQ_TYPE = 300

@dataclass
class Response:
    respType:CommuType
    mainData:dict

@dataclass
class ResponseIdentify:
    ip:str
    port:int
    respId:str