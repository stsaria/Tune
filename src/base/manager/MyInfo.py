class MyInfo:
    _name:str=""
    _pivKey:str=""
    _pubKey:str=""
    
    @classmethod
    def setName(cls, name:str):
        cls._name = name
    @classmethod
    def setPivKey(cls, pivKey:str):
        cls._pivKey = pivKey
    def setPubKey(cls, pubKey:str):
        cls._pubKey = pubKey
    @classmethod
    def getName(cls) -> str:
        return cls._name
    @classmethod
    def getPivKey(cls) -> str:
        return cls._pivKey
    @classmethod
    def getPubKey(cls) -> str:
        return cls._pubKey