from typing import Generator, Any

from src.manager.Nodes import Nodes
from src.model.Message import ReplyMessage, RootMessage
from src.net.Node import Node
from src.net.Protocol import CommuType
from src.util import ed25519


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
    def getRandomMessage(self) -> RootMessage | ReplyMessage | None:
        resp = self._node.sendToAndRecv({"t": CommuType.GET_RAND_MESSAGE, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return None
        mData = resp.mainData
        try:
            c = mData["c"]
            ts = int(mData["ts"])
            if "from" in mData.keys():
                fromNode = Nodes.getNodeFromPubKey(mData["fromPub"])
                replyFromSafe = True
                if not fromNode:
                    node = Node.nodeFromIAndP(mData["from"])
                    if not node: return None
                    fromNode = node
                    fromNode.hello()
                    if fromNode.getNodeInfo().pubKey != mData["fromPub"]:
                        replyFromSafe = False
                    Nodes.registerNode(node)
                message = ReplyMessage(c, ts, fromNode, resp.mainData["fromHash"], fromSafe=replyFromSafe, author=self)
            else:
                message = RootMessage(c, ts, author=self._node)
            if not ed25519.verify(message.hash(), mData["sig"], self._node.getNodeInfo().pubKey):
                message = None
            return message
        except:
            return None
    def getMessage(self, messageHash:str=None) -> RootMessage | ReplyMessage | None:
        if messageHash:
            req = {"t": CommuType.GET_MESSAGE, "d":{"hash":messageHash}}
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
                fromNode = Nodes.getNodeFromPubKey(mData["fromPub"])
                if not fromNode:
                    n = Node.nodeFromIAndP(mData["from"])
                    if not n: return None
                    Nodes.registerNode(n)
                    n.hello()
                    if fromNode.getNodeInfo().pubKey != mData["fromPub"]:
                        return None
                    fromNode = n
                message = ReplyMessage(c, ts, fromNode, resp.mainData["fromHash"], author=self)
            else:
                message = RootMessage(c, ts, author=self._node)
            if not ed25519.verify(message.hash(), mData["sig"], self._node.getNodeInfo().pubKey):
                return None
            return message
        except:
            return None
    def getMessagesFromHashRecur(self, messageHash:str) -> list[RootMessage | ReplyMessage] | None:
        m = self.getMessage(messageHash=messageHash)
        messages = [m]
        if not m:
            return []
        elif type(m) == ReplyMessage:
            messages += m.fromNode.getMessagesFromHashRecur(m.hash())
        return messages
    def getMyIpColonPort(self) -> str | None:
        from src.net.Me import Me
        resp = self.sendToAndRecv({"t":CommuType.GET_MY_IP_AND_PORT, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return None
        ipColonPort = resp.mainData["ipColonPort"]
        if not ed25519.verify(ipColonPort, resp.mainData["sig"], self._node.getNodeInfo().pubKey):
            return None
        return ipColonPort