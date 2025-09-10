from enum import Enum
import json
from threading import Lock
import time
from socket import IPPROTO_IPV6, IPV6_V6ONLY, SO_REUSEADDR, SOL_SOCKET, socket as Socket
from socket import AF_INET, SOCK_DGRAM, AF_INET6
import uuid

from manager.Nodes import Nodes
from src.Settings import Key, Settings
from src.defined import ENCODE
from src.net.Protocol import Response
from src.net.Protocol import ResponseIdentify, CommuType
from src.util import timestamp

class ExecOp(Enum):
    RESP = 1
    SEND = 2

class MyNet:
    def __init__(self, ipVersion:str, host:str, port:str):
        prot = {
            4: AF_INET,
            6: AF_INET6
        }[ipVersion]
        self._sock:Socket = Socket(prot, SOCK_DGRAM)
        self._sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if prot == AF_INET6: self._sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 1)
        self._sock.bind((host, port))

        self._responses:dict[str: Response] = {}
        self._responsesLock:Lock = Lock()
    def _getResp(self, identify:ResponseIdentify) -> Response | None:
        with self._responsesLock:
            return self._responses.get(identify.hash())
    def _addResp(self, identify:ResponseIdentify, resp:Response):
        with self._responsesLock:
            self._responses[identify.hash()] = resp
    def sendTo(self, data:dict, toIp:str, toPort:int) -> None:
        self._sock.sendto(json.dumps(data).encode(ENCODE), (toIp, toPort))
    def sendToAndRecv(self, data:dict, toIp:str, toPort:int, timeOut) -> Response:
        try:
            identify:ResponseIdentify = ResponseIdentify(toIp, toPort, uuid.uuid4().hex)
            data["id"] = identify.respId
            if isinstance(data["t"], CommuType): data["t"] = data["t"].value
            self.sendTo(data, toIp, toPort)

            st = timestamp.now()
            while timestamp.now()-st < timeOut:
                resp = self._getResp(identify)
                if resp:
                    return resp
                time.sleep(0.03)
            return Response(CommuType.LOC_TIME_OUTED, {})
        except:
            return Response(CommuType.LOC_ERROR, {})
    def serve(self) -> None:
        from src.net.Me import Me
        while True:
            try:
                d, a = self._sock.recvfrom(Settings.getInt(Key.BUFFER))
                if Nodes.isBanned(a[0]):
                    raise
                Nodes.updateNodeTraffic(a[0], d.__sizeof__())
                jS = d.decode(ENCODE)
                j:dict = json.loads(jS)
                for k, v in {"t":int, "d":dict, "id":str}.items():
                    if not isinstance(j[k], v):
                        raise
                r = Me.allotTaskFromReq(j, a)
                if not r: raise
                op, c = r
                match op:
                    case ExecOp.RESP:
                        self._addResp(c[0], c[1])
                    case ExecOp.SEND:
                        self.sendTo(c, a[0], a[1])
            except:
                pass
    def close(self) -> None:
        self._sock.close()