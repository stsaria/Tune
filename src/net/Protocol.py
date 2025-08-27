from dataclasses import dataclass
from enum import Enum

from src.util import sha256


class CommuType(Enum):
    HELLO = 0
    RESPONSE = 1
    PING = 2

    GET_NODES = 100
    GET_RAND_MESSAGE = 101
    GET_MESSAGE = 102
    GET_MY_IP_AND_PORT = 103
    GET_DELEGATE_MESSAGE = 104

    LOC_TIME_OUTED = 200
    LOC_ERROR = 201

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
    def hash(self):
        return sha256.hash(f"{self.ip}{self.port}{self.respId}")