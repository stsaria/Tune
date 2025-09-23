import time
from threading import Thread

from src.base import JobProcessor
from src.base.manager.MyInfo import MyInfo
from src.globalNet.manager.Nodes import Nodes
from src.base.ServerAndClient import ServerAndClient
from src.Settings import Key, Settings
from src.globalNet.manager.Messages import MyMessages, OthersMessages
from src.globalNet.model.Message import ReplyMessage
from src.base.model.NodeInfo import NodeInfo
from src.globalNet.Node import Node
from src.base.Protocol import CommuType
from src.base.model.Response import Response, ResponseIdentify
from src.base.util import ed25519, nettet
from src.globalNet.util import msg
from src.base.util import nodeTrans

class Me:
    @classmethod
    def syncer(cls, loopDelay:int=40) -> None:
        while True:
            for n in Nodes.getNodes():
                aN = Node.fromOrginalNode(n)
                Thread(target=aN.syncNode, daemon=True).start()
            msg.dumpMessages(OthersMessages)
            msg.dumpMessages(MyMessages)
            time.sleep(loopDelay)
    @classmethod
    def _getMyIPColonPort(cls) -> str | None:
        nodes = Nodes.getNodesByRandom(limit=5)
        if len(nodes) == 0:
            return None
        ipColonPorts = [Node.fromOrginalNode(n).getMyIpColonPort() for n in nodes]
        if not all(ipColonPorts) or not ipColonPorts[0]:
            return None
        return ipColonPorts[0]
    @classmethod
    def getMyId(cls) -> str | None:
        ipColonPort = cls._getMyIPColonPort()
        if not ipColonPort:
            return None
        return nodeTrans.idFromNodeIAndP(ipColonPort)
