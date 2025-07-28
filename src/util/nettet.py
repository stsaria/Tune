import random
from socket import socket as Socket

def selectPort(n:int, l:int) -> int:
    while True:
        port = random.randint(n, l)
        resp = Socket().connect_ex(("127.0.0.1", port))
        if resp != 0: return port