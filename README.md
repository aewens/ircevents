# ircstates

[![Build Status](https://travis-ci.org/aewens/ircevents.svg?branch=master)](https://travis-ci.org/aewens/ircevents)

## usage

### example code
```python
import ircstates, ircevents, socket

NICK = "nickname"
CHAN = "#chan"
HOST = "127.0.0.1"
POST = 6667

server = ircstates.Server("freenode")
sock   = socket.socket()

sock.connect((HOST, POST))

def _send(s):
    line = irctokens.tokenise(s)
    server.send(line)

_send("USER test 0 * :test")
_send("NICK test321")

while True:
    while server.pending():
        send_lines = server.sent(sock.send(server.pending()))
        for line in send_lines:
            print(f"> {line.format()}")

    recv_lines = server.recv(sock.recv(1024))
    for line in recv_lines:
        print(f"< {line.format()}")

        # user defined behaviors...
        if line.command == "001" and not "#test321" in server.channels:
            _send("JOIN #test321")
```
