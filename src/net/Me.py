import json
import time
import uuid
from socket import socket as Socket
from socket import AF_INET, SOCK_DGRAM
from threading import Lock

from src.manager.MyMessages import MyMessages
from src.manager.Nodes import Nodes
from src.model.Message import ReplyMessage
from src.model.NodeInfo import NodeInfo
from src.net.Protocol import Response
from src.net.Protocol import ResponseIdentify, CommuType
from src.util import ed25519, nettet


class Me:
    def __init__(self, name:str, ip:str="0.0.0.0", buffer:int=4096):
        self._ip:str = ip

        self._port:int = nettet.selectPort(1024, 65535)
        self._sock:Socket = Socket(AF_INET, SOCK_DGRAM)
        self._sock.settimeout(4)
        self._sock.bind((self._ip, self._port))

        self._responses:dict[ResponseIdentify: Response] = {}
        self._responsesLock:Lock = Lock()

        self._buffer:int = buffer

        self._name = name

        hexs = ed25519.generate()
        self._pivKey:str = hexs[0]
        self._pubKey:str = hexs[1]

        Nodes.setMe(self)
    def getName(self) -> str:
        return self._name
    def getPubKey(self) -> str:
        return self._pubKey
    def _getResp(self, identify:ResponseIdentify) -> Response | None:
        with self._responsesLock:
            for k, v in self._responses:
                resp:Response = v
                if k == identify:
                    return resp
        return None
    def _addResp(self, identify:ResponseIdentify, resp:Response):
        with self._responsesLock:
            self._responses[identify] = resp
    def sendToAndRecv(self, data:dict, toIp:str, toPort:int, timeOut:int=4) -> Response:
        identify:ResponseIdentify = ResponseIdentify(toIp, toPort, uuid.uuid4().hex)
        data["id"] = identify.respId
        self._sock.sendto(json.dumps(data).encode("utf-8"), (toIp, toPort))

        st = time.time()
        while time.time()-st >= timeOut:
            resp = self._getResp(identify)
            if resp:
                return resp
            time.sleep(0.03)
        return Response(CommuType.LOC_TIME_OUTED, {})
    def __hello(self, mData:dict, addr:tuple[str, int]) -> dict:
        Nodes.registerNode(NodeInfo(addr[0], addr[1], mData["name"], mData["pub"]))
        return {"name":self._name, "pub":self._pubKey}
    def __getNodes(self) -> dict:
        nodes = Nodes.getNodesFromRandom(sampleK=13)
        return {"nodes": [n.getNodeInfo().getIpColonPort() for n in nodes]}
    def __getMessage(self) -> dict:
        message = MyMessages.getRandomMessage()
        h = message.hash()
        m = {"c":message.content, "ts":message.timestamp, "hash":h, "sig": ed25519.sign(h, self._pivKey)}
        if type(message) == ReplyMessage:
            fNI = message.fromNode.getNodeInfo()
            m["from"] = fNI.getIpColonPort()
            m["fromPub"] = fNI.pubKey
            m["fromHash"] = message.fromHash
        return m
    def _allotTaskFromReq(self, data:dict, addr:tuple[str, int]) -> None:
        r:dict = {"t":CommuType.RESPONSE, "d":{}, "id":data["id"]}
        match data["t"]:
            case CommuType.HELLO:
                r["d"] = self.__hello(data["d"], addr)
            case CommuType.GET_NODES:
                r["d"] = self.__getNodes()
            case CommuType.GET_RAND_MESSAGE:
                r["d"] = self.__getMessage()
            case _:
                r["t"] = CommuType.ERR_I_DONT_KNOW_YOUR_REQ_TYPE
        self._sock.sendto(json.dumps(r).encode("utf-8"), addr)
    def serve(self) -> None:
        while True:
            try:
                d, a = self._sock.recvfrom(self._buffer)
                jS = d.decode("utf-8")
                j:dict = json.loads(jS)
                for k, v in {"t":int, "d":dict, "id":str}:
                    if type(j[v]) != v:
                        raise
                if "id" in j.keys():
                    resType: CommuType | None = None
                    for e in CommuType:
                        if e.value == j["t"]: resType = e
                    if not resType: continue
                    self._addResp(ResponseIdentify(a[0], a[1], j["id"]), Response(resType, j["d"]))
                    continue
                self._allotTaskFromReq(j, a)
            except:
                pass
    def sync(self, loopDelay:int=40) -> None:
        while True:
            try:
                
            except:
                pass
            time.sleep(loopDelay)

