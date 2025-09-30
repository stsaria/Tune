import random

from src.allNet.manager.DB import DB
from src.allNet.model.NodeInfo import NodeInfo
from src.Settings import Key, Settings
from src.globalNet.Node import Node
from src.allNet.util import nodeTrans
from src.defined import GLOBAL_NET_NAME

NODE_TUPLE = tuple[str, str, int, str, int, int, int, int]

class Nodes:
    @classmethod
    def registerNode(cls, node:Node) -> None:
        if cls.getLength() >= Settings.getInt(Key.MAX_NODES): return
        nodeInfo = node.getNodeInfo()
        if cls.isBanned(nodeInfo.ip): return
        elif cls.getNodeByIpAndPort(nodeInfo.ip, nodeInfo.port) or cls.getNodeByPubKey(nodeInfo.pubKey): return
        DB.execAndCommit("""
            INSERT OR REPLACE INTO nodes (pubKey, ip, port, name, uniqueColorR, uniqueColorG, uniqueColorB, startTime, expireTime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nodeInfo.pubKey, nodeInfo.ip, nodeInfo.port, nodeInfo.name, *node.getUniqueColorRGB(), node.getStartTime(), node.getExpireTime()))
    @classmethod
    def unregisterNode(cls, node:Node) -> None:
        nI = node.getNodeInfo()
        DB.execAndCommit("DELETE FROM nodes WHERE pubKey = ? OR (ip = ? AND port = ?)", (nI.pubKey, nI.ip, nI.port))
    @classmethod
    def getNodeByIpAndPort(cls, ip:str, port:int) -> Node | None:
        return cls._sqlNodeToNode(DB.fetchOne("SELECT * FROM nodes WHERE ip = ? AND port = ?",(ip, port)))
    @classmethod
    def getNodeByPubKey(cls, pubKey:str) -> Node | None:
        return cls._sqlNodeToNode(DB.fetchOne("SELECT * FROM nodes WHERE pubKey = ?", (pubKey,)))
    @classmethod
    def getNodeById(cls, nodeId:str) -> Node | None:
        try:
            return cls.getNodeByIpAndPort(*nodeTrans.separateNodeIAndP(nodeId))
        except Exception:
            return None
    
    @classmethod
    def getNodes(cls) -> list[Node]:
        return [N for n in DB.fetchAll("SELECT * FROM nodes") if (N := cls._sqlNodeToNode(n))]
    @classmethod
    def getNodesByRandom(cls, limit:int=1) -> list[Node]:
        return [N for n in DB.fetchAll("SELECT * FROM nodes ORDER BY RANDOM() LIMIT ?", (limit,)) if (N := cls._sqlNodeToNode(n))]
    
    @classmethod
    def getLength(cls) -> int:
        return DB.fetchOne("SELECT COUNT(*) FROM nodes")[0]
    
    @classmethod
    def ban(cls, ip:str) -> None:
        DB.execAndCommit("INSERT OR REPLACE INTO bannedIps (ip) VALUES (?)", (ip,))
    @classmethod
    def unban(cls, ip:str) -> None:
        DB.execAndCommit("DELETE FROM bannedIps WHERE ip = ?", (ip,))
    @classmethod
    def isBanned(cls, ip:str) -> bool:
        return bool(DB.fetchOne("SELECT 1 FROM bannedIps WHERE ip = ?", (ip,))[0])

    @classmethod
    def updateNodeTraffic(cls, ip:str, size:int):
        DB.execAndCommit("INSERT OR REPLACE INTO traffics (ip, size) VALUES (?, ?)", (ip, cls.getNodeTraffic(ip)+size))
    @classmethod
    def getNodeTraffic(cls, ip:str) -> int:
        return cls.getNodesTraffics().get(ip, 0)
    @classmethod
    def getNodesTraffics(cls) -> dict[str, int]:
        return {t[0]:t[1] for t in DB.fetchAll("SELECT * FROM traffics")}
    
    @classmethod
    def getNodeOrGenerateByIAndPOrPubKey(cls, nIAndP:str, pubKey:str) -> Node:
        separatedNIAndP = nodeTrans.separateNodeIAndP(nIAndP)
        return cls.getNodeByIpAndPort(*separatedNIAndP) or cls.getNodeByPubKey(pubKey) or Node(NodeInfo(separatedNIAndP[0], separatedNIAndP[1], "IDK", pubKey))

    @classmethod
    def _sqlNodeToNode(cls, n:NODE_TUPLE) -> Node | None:
        if not n:
            return None
        try:
            return Node(GLOBAL_NET_NAME, NodeInfo(n[1], n[2], n[3], n[0]), (n[4], n[5], n[6]), n[7], n[8])
        except Exception:
            return None

    DB.execAndCommit("""
        CREATE TABLE IF NOT EXISTS nodes (
            pubKey TEXT PRIMARY KEY,
            ip TEXT NOT NULL,
            port INTEGER NOT NULL,
            name TEXT NOT NULL,
            uniqueColorR TEXT NOT NULL,
            uniqueColorG TEXT NOT NULL,
            uniqueColorB TEXT NOT NULL,
            startTime INTEGER NOT NULL,
            expireTime INTEGER NOT NULL
        )
    """)
    DB.execAndCommit("""
        CREATE TABLE IF NOT EXISTS bannedIps (
            ip TEXT PRIMARY KEY
        )
    """)
    DB.execAndCommit("""
        CREATE TABLE IF NOT EXISTS traffics (
            ip TEXT PRIMARY KEY,
            size INTEGER NOT NULL
        )
    """)