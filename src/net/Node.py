from socket import socket as Socket
from socket import AF_INET, SOCK_DGRAM

from src.model.NodeInfo import NodeInfo
from src.net import Protocol
from src.net.Me import Me
from src.net.Presets import Presets


class Node:
    def __init__(self, nodeInfo:NodeInfo, me:Me):
        self._nodeInfo = nodeInfo
        self._me:Me = me
    def getNodeInfo(self) -> NodeInfo:
        return self._nodeInfo
    def sendAndRecv(self, ):
    def getSock(self) -> Socket:
        sock:Socket = Socket(AF_INET, SOCK_DGRAM)
        sock.settimeout(2)
        return sock
    def hello(self, myName:str, myPubKey:str) -> Response:
        sock:Socket = self.getSock()
        sock.sendto(Presets.hello(myName, myPubKey), (self._nodeInfo.ip, self._nodeInfo.port))
        r,
