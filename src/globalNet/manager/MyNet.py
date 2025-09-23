from threading import Thread

from src.base import JobProcessor
from src.base.manager.MyInfo import MyInfo
from src.base.ServerAndClient import ServerAndClient
from src.Settings import Key, Settings
from src.base.model.Response import Response
from src.base.util import ed25519, nettet

class MyNet:
    _v4Ip:str = "0.0.0.0"
    _v6Ip:str = "::"
    _port:int = nettet.selectPort()
    _jobProcessor = JobProcessor()

    _v4Net:ServerAndClient = ServerAndClient(4, _v4Ip, _port, _jobProcessor)
    _v6Net:ServerAndClient = ServerAndClient(6, _v6Ip, _port, _jobProcessor)

    pivKey = Settings.get(Key.PRIVATE_KEY)

    MyInfo.setPivKey(pivKey)
    MyInfo.setPubKey(ed25519.getPubKeyByPivKey(pivKey))

    @classmethod
    def getV4Ip(cls) -> str:
        return cls._v4Ip
    @classmethod
    def getV6Ip(cls) -> str:
        return cls._v6Ip
    @classmethod
    def sockClose(cls):
        cls._v4Net.close()
        cls._v6Net.close()
    @classmethod
    def sendToAndRecv(cls, data:dict, toIp:str, toPort:int) -> Response:
        return (cls._v6Net if ":" in toIp else cls._v4Net).sendToAndRecv(data, toIp, toPort, Settings.getInt(Key.SOCK_TIME_OUT))
    @classmethod
    def serve(cls):
        Thread(target=cls._v4Net.serve, daemon=True).start()
        Thread(target=cls._v6Net.serve, daemon=True).start()