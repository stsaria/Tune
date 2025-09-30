import time

from src.globalNet.model.Message import ReplyMessage, RootMessage
from src.globalNet.manager.Messages import MyMessages, OthersMessages
from src.Settings import Settings, Key
from src.allNet.util import timestamp

def isNeedDumpMessage(m:ReplyMessage | RootMessage):
    expirationSecS = Settings.getInt(Key.EXPIRATION_SECONDS)
    now = timestamp.now()
    return len(m.content) < Settings.getInt(Key.MIN_MESSAGE_SIZE) or (False if expirationSecS < 0 else (now - m.timestamp > expirationSecS)) or m.timestamp > now
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
    pruneMsgs(sortedMsgS, 1, (ReplyMessage | RootMessage), maX=Settings.getInt(Key.MAX_MESSAGES))