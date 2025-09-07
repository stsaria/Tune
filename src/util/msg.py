import time

from src.model.Message import ReplyMessage
from manager.OthersMessages import OthersMessages
from src.manager.MyMessages import MyMessages
from src.Settings import Settings, Key
from src.typeDefined import MSG

def isNeedDumpMessage(m:MSG):
    expirationSecS = Settings.getInt(Key.EXPIRATION_SECONDS)
    return len(m.content) < Settings.getInt(Key.MIN_MESSAGE_SIZE) or (False if expirationSecS < 0 else (int(time.time()) - m.timestamp > expirationSecS)) or m.timestamp > int(time.time())
def dumpMessages(cls:MyMessages | OthersMessages):
    def d(m): cls.deleteMessage(m)
    for m in cls.getMessages():
        if isNeedDumpMessage(m): d(m)
    sortedMsgS = sorted([m for m in cls.getMessages()], key=lambda m: m.timestamp)
    def leN(t): return len([m for m in sortedMsgS if isinstance(m, t)])
    def pruneMsgs(sMS,maxR,t,maX=None):
        l = leN(t)
        maX = maX if maX else int(l*maxR)
        if l > maX:
            for m in sMS[:l-maX]:
                d(m)
    pruneMsgs(sortedMsgS, Settings.getFloat(Key.MAX_REPLY_RATIO) if leN(ReplyMessage) >= Settings.getInt(Key.MIN_COUNT_FOR_MAX_REPLY_RATIO) else 1, ReplyMessage)
    pruneMsgs(sortedMsgS, 1, (MSG), maX=Settings.getInt(Key.MAX_MESSAGES))