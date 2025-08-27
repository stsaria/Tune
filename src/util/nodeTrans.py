import base64
import json
import re
from typing import Optional

from src.defined import ENCODE

def nodeIAndPFromId(nodesId:str) -> Optional[str]:
    try:
        idJS = base64.b64decode(nodesId).decode(ENCODE)
        idJ = json.loads(idJS)
        node = idJ["node"]
        return f"{node[0]}:{node[1]}"
    except:
        return None

def idFromNodeIAndP(nodeIAndP:str) -> str:
    return base64.b64encode(json.dumps({"node":nodeIAndP.split(":")}).encode(ENCODE)).decode(ENCODE)

def separateNodeIAndP(nodeIAndP:str) -> tuple[str, int]:
    port = int(nodeIAndP.split(":")[-1])
    ip = re.sub(f":{port}$", "", nodeIAndP)
    return ip, port