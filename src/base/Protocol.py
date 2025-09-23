from enum import Enum

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