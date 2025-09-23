from src.base.model.NodeInfo import NodeInfo
from src.base.ServerAndClient import ServerAndClient
from src.base.Node import Node as OrgNode

class Node(OrgNode):
    def __init__(self, serverAndClient:ServerAndClient, nodeInfo:NodeInfo):
        super().__init__(serverAndClient, nodeInfo)