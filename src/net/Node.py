from socket import socket as Socket
from socket import AF_INET, SOCK_DGRAM

from src.net import Response
from src.net.Presets import Presets


class Node:
    def __init__(self, ip:str, port:int, mySock:Socket):
        self.ip:str = ip
        self.port:int = port
        self.mySock:Socket = mySock
    def sendAndRecv(self, ):
    def getSock(self) -> Socket:
        sock:Socket = Socket(AF_INET, SOCK_DGRAM)
        sock.settimeout(2)
        return sock
    def hello(self, myName:str, myPubKey:str) -> Response:
        sock:Socket = self.getSock()
        sock.sendto(Presets.hello(myName, myPubKey), (self.ip, self.port))
        r,
