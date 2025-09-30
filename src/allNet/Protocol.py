from enum import Enum

class CommuType(Enum):
    HELLO = 0
    RESPONSE = 1
    PING = 2

    ERR_I_DONT_KNOW_YOUR_REQ_TYPE = 10

    GET_NODES = 100
    GET_RAND_MESSAGE = 101
    GET_MESSAGE = 102
    GET_MY_IP_AND_PORT = 103
    GET_DELEGATE_MESSAGE = 104
    INVITE_TO_DIRECT_NET = 105

    SEND_MESSAGE = 200
    SEND_VOICE = 201

    LOC_TIME_OUTED = 320
    LOC_ERROR = 321