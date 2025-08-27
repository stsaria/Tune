import traceback
from typing import Generator, Any

from src.Settings import Key, Settings
from src.manager.Nodes import Nodes
from src.model.Message import ReplyMessage, RootMessage
from src.net.Node import Node
from src.net.Protocol import CommuType
from src.util import ed25519
from src.typeDefined import MSG, MSGS


class AdvNode:
    def __init__(self, node:Node):
        self._node = node
    def getNodes(self) -> Generator["Node", Any, list[Any] | None]:
        resp = self._node.sendToAndRecv({"t":CommuType.GET_NODES, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return []
        for nIAndP in resp.mainData.get("nodes", __default=[]):
            try:
                n = Node.nodeFromIAndP(nIAndP)
                if not n: raise
                yield n
            except:
                pass
    def getMessage(self, messageHash:str=None, isDelegate:bool=False) -> MSG | None:
        if messageHash:
            req = {"t": CommuType.GET_MESSAGE, "d":{"hash":messageHash}}
        elif messageHash and isDelegate and delegatePub:
            req = {"t": CommuType.GET_DELEGATE_MESSAGE, "d":{"hash":messageHash}}
        else:
            req = {"t": CommuType.GET_RAND_MESSAGE, "d":{}}
        resp = self._node.sendToAndRecv(req)
        if resp.respType != CommuType.RESPONSE:
            return None
        mData = resp.mainData
        try:
            c = mData["c"]
            ts = int(mData["ts"])
            if "from" in mData.keys():
                match mData["from"]:
                    case Settings.get(Key.IMYME_ADDR):
                        fromNode = self._node
                        isFromDelegate = True
                    case _:
                        fromNode = Nodes.getNodeFromPubKey(mData["fromPub"])
                        isFromDelegate = False
                if not fromNode:
                    n = Node.nodeFromIAndP(mData["from"])
                    Nodes.registerNode(n)
                    n.hello()
                    if n.getNodeInfo().pubKey != mData["fromPub"]: return None
                    fromNode = n
                message = ReplyMessage(content=c, timestamp=ts, fromNode=fromNode, fromHash=resp.mainData["fromHash"], author=self._node, isFromDelegate=isFromDelegate)
            else:
                message = RootMessage(content=c, timestamp=ts, author=self._node)
            if not ed25519.verify(message.hash(), mData["sig"], (mData["dgPub"] if isDelegate else self._node.getNodeInfo().pubKey)):
                return None
            return message
        except:
            return None
    def getMessagesFromHashRecur(self, messageHash:str, i=0) -> MSGS | None:
        if i >= Settings.getInt(Key.MESSAGES_RECURS):
            return []
        m = self.getMessage(messageHash=messageHash)
        messages = [m]
        if not m:
            return []
        elif isinstance(m, ReplyMessage):
            messages += m.fromNode.getMessagesFromHashRecur(m.hash(), i=i+1)
        return messages
    def getMyIpColonPort(self) -> str | None:
        from src.net.Me import Me
        resp = self._node.sendToAndRecv({"t":CommuType.GET_MY_IP_AND_PORT, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return None
        ipColonPort = resp.mainData["ipColonPort"]
        if not ed25519.verify(ipColonPort, resp.mainData["sig"], self._node.getNodeInfo().pubKey):
            return None
        return ipColonPort