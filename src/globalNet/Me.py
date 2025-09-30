import time
from threading import Lock, Thread

from src.allNet import JobProcessor
from src.allNet.manager.MyInfo import MyInfo
from src.globalNet.manager.Nodes import Nodes
from src.allNet.ServerAndClient import ServerAndClient
from src.Settings import Key, Settings
from src.globalNet.manager.Messages import MyMessages, OthersMessages
from src.globalNet.model.Message import ReplyMessage
from src.allNet.model.NodeInfo import NodeInfo
from src.globalNet.Node import Node
from src.allNet.Protocol import CommuType
from src.allNet.model.Response import Response, ResponseIdentify
from src.allNet.util import ed25519, nettet
from src.globalNet.util import msg
from src.allNet.util import nodeTrans

class Me:
    _stoped:bool = False
    _stopedLock:Lock = Lock()

    @classmethod
    def stop(cls):
        with cls._stopedLock:
            cls._stoped = True

    @classmethod
    def syncer(cls, loopDelaySec:int=40) -> None:
        while True:
            d = 0.1
            for _ in range(loopDelaySec/d):
                with cls._stopedLock:
                    if cls._stoped: break
                time.sleep(d)
            try:
                for n in Nodes.getNodes():
                    aN = Node.getNodeFromAll(n)
                    Thread(target=aN.syncNode, daemon=True).start()
                msg.dumpMessages(OthersMessages)
                msg.dumpMessages(MyMessages)
            except Exception:
                pass
    @classmethod
    def _getMyIPColonPort(cls) -> str | None:
        nodes = Nodes.getNodesByRandom(limit=5)
        if len(nodes) == 0:
            return None
        ipColonPorts = [Node.getNodeFromAll(n).getMyIpColonPort() for n in nodes]
        if not all(ipColonPorts) or not ipColonPorts[0]:
            return None
        return ipColonPorts[0]
    @classmethod
    def getMyId(cls) -> str | None:
        ipColonPort = cls._getMyIPColonPort()
        if not ipColonPort:
            return None
        return nodeTrans.idFromNodeIAndP(ipColonPort)
