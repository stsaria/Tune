import json
import random
import time
import uuid
from socket import socket as Socket
from socket import AF_INET, SOCK_DGRAM
from threading import Lock
from typing import Any

from src.net.Response import Response
from src.net.Presets import Presets
from src.net.Response import ResponseIdentify, ResponseType

class Me:
    def __init__(self, ip:str="0.0.0.0", buffer:int=4096):
        self._ip:str = ip

        self._port:int = self._selectPort()
        self._sock:Socket = Socket(AF_INET, SOCK_DGRAM)
        self._sock.settimeout(4)
        self._sock.bind((self._ip, self._port))

        self._responses:dict[ResponseIdentify: Response] = {}
        self._responsesLock = Lock()
        self._buffer = buffer
    def _selectPort(self) -> int:
        while True:
            port = random.randint(1024, 65535)
            resp = Socket().connect_ex(("127.0.0.1", port))
            if resp != 0: return port
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
        return Response(ResponseType.LOC_TIME_OUTED, {})
    def _allotTaskFromReq(self, data:dict, address) -> None:
        pass
    def serve(self):
        while True:
            try:
                d, a = self._sock.recvfrom(self._buffer)
                jS = d.decode("utf-8")
                j:dict = json.loads(jS)
                if [type(j.get("t")), type(j.get("d"))] != [int, dict]:
                    continue
                if "id" in j.keys():
                    resType:ResponseType | None = None
                    for e in ResponseType:
                        if e.value == j["t"]: resType = e
                    if not resType: continue
                    self._addResp(ResponseIdentify(a[0], a[1], j["id"]), Response(resType, j["d"]))
                    continue
                self._allotTaskFromReq(j, a)
            except:
                pass

