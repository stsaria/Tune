from threading import Lock

from src.allNet.MyNet import MyNet

class MyNets:
    _nameAndMyNets:dict[str:MyNet] = {}
    _nameAndMyNetsLock:Lock = Lock()

    @classmethod
    def registerMyNet(cls, name:str, myNet:MyNet) -> None:
        with cls._nameAndMyNetsLock:
            cls._nameAndMyNets[name] = myNet
    @classmethod
    def unregisterMyNet(cls, name:str) -> None:
        with cls._nameAndMyNetsLock:
            if net := cls._nameAndMyNets.pop(name, None):
                net.sockClose()
    @classmethod
    def getMyNetByName(cls, name:str) -> MyNet | None:
        with cls._nameAndMyNetsLock:
            return cls._nameAndMyNets.get(name)