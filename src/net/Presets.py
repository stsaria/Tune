import json


class Presets:
    @classmethod
    def _toFormat(cls, d:dict) -> bytes:
        return json.dumps(d).encode()
    @classmethod
    def hello(cls, name:str, pubKey:str) -> bytes:
        return cls._toFormat({"t":"0", "d":{"name":name, "pub":pubKey}})