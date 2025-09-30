from threading import Thread

from src.allNet import JobProcessor
from src.allNet.ServerAndClient import ServerAndClient
from src.Settings import Key, Settings
from src.allNet.model.Response import Response
from src.allNet.util import nettet

class MyNet:
    def __init__(self, jobProcessor:JobProcessor):
        self._v4Ip:str = "0.0.0.0"
        self._v6Ip:str = "::"
        self._port:int = nettet.selectPort()
        self._jobProcessor = jobProcessor

        self._v4Net:ServerAndClient = ServerAndClient(4, self._v4Ip, self._port, self._jobProcessor)
        self._v6Net:ServerAndClient = ServerAndClient(6, self._v6Ip, self._port, self._jobProcessor)
    def getV4Ip(self) -> str:
        return self._v4Ip
    def getV6Ip(self) -> str:
        return self._v6Ip
    def sockClose(self):
        self._v4Net.close()
        self._v6Net.close()
    def _decideNet(self, ip:str):
        return (self._v6Net if ":" in ip else self._v4Net)
    def sendTo(self, data:dict, toIp:str, toPort:int):
        self._decideNet(toIp).sendTo(data, toIp, toPort)
    def sendToAndRecv(self, data:dict, toIp:str, toPort:int) -> Response:
        return self._decideNet(toIp).sendToAndRecv(data, toIp, toPort)
    def serve(self):
        Thread(target=self._v4Net.serve, daemon=True).start()
        Thread(target=self._v6Net.serve, daemon=True).start()