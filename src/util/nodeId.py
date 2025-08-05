import base64
import json
from typing import Optional

from src.net.Node import Node
from src.model.NodeInfo import NodeInfo

def nodeIAndPFromId(nodesId:str) -> Optional[str]:
    try:
        idJS = base64.b64decode(nodesId).decode("utf-8")
        idJ = json.loads(idJS)
        node = idJ["node"]
        return f"{node[0]}:{node[1]}"
    except:
        return None

def idFromNodeIAndP(nodeIAndP:str) -> str:
    return base64.b64encode(json.dumps({"node":nodeIAndP.split(":")}).encode("utf-8")).decode("utf-8")