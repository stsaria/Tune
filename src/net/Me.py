import json
import time
import traceback
import uuid
from socket import socket as Socket
from socket import AF_INET, SOCK_DGRAM
from threading import Lock, Thread

from src.net.MyNet import ExecOp, MyNet
from src.Settings import Key, Settings
from src.defined import ENCODE
from src.manager.OthersMessages import OthersMessages
from src.manager.MyMessages import MyMessages
from src.manager.Nodes import Nodes
from src.model.Message import ReplyMessage, RootMessage, DelegateMessaege
from src.model.NodeInfo import NodeInfo
from src.net.Node import Node
from src.net.AdvNode import AdvNode
from src.net.Protocol import Response
from src.net.Protocol import ResponseIdentify, CommuType
from src.util import ed25519, nettet
from src.util import msg
from src.typeDefined import MSG
from src.util import nodeTrans


class Me:
    _v4Ip:str = "0.0.0.0"
    _v6Ip:str = "::"
    _port:int = nettet.selectPort(1024, 65535)

    _v4Net:MyNet = MyNet(4, _v4Ip, _port)
    _v6Net:MyNet = MyNet(6, _v6Ip, _port)

    _name = ""
    hexs = ed25519.generate()
    _pivKey:str = hexs[0]
    _pubKey:str = hexs[1]

    @classmethod
    def getV4Ip(cls) -> str:
        return cls._v4Ip
    @classmethod
    def getV6Ip(cls) -> str:
        return cls._v6Ip
    @classmethod
    def getPort(cls) -> int:
        return cls._port
    @classmethod
    def getName(cls) -> str:
        return cls._name
    @classmethod
    def setName(cls, name:str):
        cls._name = name
    @classmethod
    def sockClose(cls):
        cls._v4Net.close()
        cls._v6Net.close()
    @classmethod
    def getPubKey(cls) -> str:
        return cls._pubKey
    @classmethod
    def getPivKey(cls) -> str:
        return cls._pivKey
    @classmethod
    def sendToAndRecv(cls, data:dict, toIp:str, toPort:int) -> Response:
        return (cls._v6Net if ":" in toIp else cls._v4Net).sendToAndRecv(data, toIp, toPort, Settings.getInt(Key.SOCK_TIME_OUT))
    @classmethod
    def serve(cls):
        Thread(target=cls._v4Net.serve, daemon=True).start()
        Thread(target=cls._v6Net.serve, daemon=True).start()
    @classmethod
    def __hello(cls, mData:dict, addr:tuple[str, int]) -> dict:
        Nodes.registerNode(Node(NodeInfo(addr[0], addr[1], mData["name"], mData["pub"])))
        return {"name":cls._name, "pub":cls._pubKey}
    @classmethod
    def __getNodes(cls, addr:tuple[str, int]) -> dict:
        nodes = Nodes.getNodesFromRandom(exclusionIp=addr[0], sampleK=13)
        return {"nodes": [n.getNodeInfo().getIPColonPort() for n in nodes]}
    @classmethod
    def __getMessage(cls, addr:tuple[str, int], msgHash:str=None) -> dict:
        message = MyMessages.getMessageFromHash(msgHash) if msgHash else MyMessages.getRandomMessage()
        h = message.hash()
        m = {"c":message.content, "ts":message.timestamp, "hash":h, "sig": ed25519.sign(h, cls._pivKey)}
        if isinstance(message, ReplyMessage):
            fNI = message.fromNode.getNodeInfo()
            m["from"] = Settings.get(Key.YOUYOURYOU_ADDR) if addr[0] == fNI.ip else fNI.getIPColonPort()
            m["fromPub"] = fNI.pubKey
            m["fromHash"] = message.fromHash
        return m
    @classmethod
    def __getDelegateMessage(cls, msgHash:str) -> dict:
        dgMessage = MyMessages.getMessageFromHash(msgHash, isDelegate=True)
        return {"c":dgMessage.content, "ts":dgMessage.timestamp, "hash":dgMessage.hash(), "sig": dgMessage.sig, "dgPub": dgMessage.delegatePub}
    @classmethod
    def allotTaskFromReq(cls, data:dict, addr:tuple[str, int]) -> tuple[ExecOp, any] | None:
        r:dict = {"t":CommuType.RESPONSE.value, "d":{}, "id":data["id"]}
        match data["t"]:
            case CommuType.HELLO.value:
                r["d"] = cls.__hello(data["d"], addr)
            case CommuType.GET_NODES.value:
                r["d"] = cls.__getNodes(addr)
            case CommuType.GET_RAND_MESSAGE.value:
                r["d"] = cls.__getMessage(addr)
            case CommuType.RESPONSE.value:
                resType: CommuType | None = None
                for e in CommuType:
                    if e.value == data["t"]: resType = e
                if not resType: return 
                return (ExecOp.RESP, (ResponseIdentify(addr[0], addr[1], data["id"]), Response(resType, data["d"])))
            case CommuType.PING.value:
                pass
            case CommuType.GET_MY_IP_AND_PORT.value:
                r["d"] = {"ipColonPort":f"{addr[0]}:{addr[1]}", "sig":ed25519.sign(f"{addr[0]}:{addr[1]}", cls._pivKey)}
            case CommuType.GET_MESSAGE.value:
                print(data["d"])
                r["d"] = cls.__getMessage(addr, data["d"]["hash"])
            case CommuType.GET_DELEGATE_MESSAGE.value:
                r["d"] = cls.__getDelegateMessage(data["d"]["hash"])
            case _:
                r["t"] = CommuType.ERR_I_DONT_KNOW_YOUR_REQ_TYPE.value
        return ExecOp.SEND, r
    @classmethod
    def syncer(cls, loopDelay:int=40) -> None:
        while True:
            for n in Nodes.getNodes():
                aN = AdvNode(n)
                Thread(target=aN.syncNode, daemon=True).start()
            msg.dumpMessages(OthersMessages)
            msg.dumpMessages(MyMessages)
            time.sleep(loopDelay)
    @classmethod
    def _getMyIPColonPort(cls) -> str | None:
        nodes = Nodes.getNodesFromRandom(sampleK=5)
        if len(nodes) == 0:
            return None
        ipColonPorts = [AdvNode(n).getMyIpColonPort() for n in nodes]
        if not all(ipColonPorts) or not ipColonPorts[0]:
            return None
        return ipColonPorts[0]
    @classmethod
    def getMyId(cls) -> str | None:
        ipColonPort = cls._getMyIPColonPort()
        if not ipColonPort:
            return None
        return nodeTrans.idFromNodeIAndP(ipColonPort)
    @classmethod
    def banNodeFromId(cls, id:str) -> None:
        n = Nodes.getNodeFromId(id)
        if not n:
            return
        Nodes.banIp(n.getNodeInfo().ip)
        OthersMessages.deleteMessagesFromIp(n.getNodeInfo().ip)
    @classmethod
    def postReplyMessage(cls, content:str, fromMessage:MSG) -> None:
        if not fromMessage.author or not fromMessage.author.getNodeInfo().pubKey: return
        elif isinstance(fromMessage, ReplyMessage): return
        ts = int(time.time())
        fromHash = fromMessage.hash()
        if "y" in Settings.get(Key.COPY_REPLY_FROM_MSGS).lower():
            MyMessages.addDelegateMessage(fromMessage)
            fromAddr = Settings.get(Key.IMYME_ADDR)
            fromPub = fromMessage.author.getNodeInfo().pubKey
        else:
            fromAddr = fromMessage.author.getNodeInfo().getIPColonPort()
            fromPub = fromMessage.author.getNodeInfo().pubKey
        MyMessages.addMessage(ReplyMessage(content=content, timestamp=ts, fromHash=fromHash, fromAddr=fromAddr, fromPub=fromPub))