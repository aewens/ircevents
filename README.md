# ircevents

[![Build Status](https://travis-ci.org/aewens/ircevents.svg?branch=master)](https://travis-ci.org/aewens/ircevents)

## usage

### example code
```python
import ircstates, irctokens, ircevents, socket

# Connection settings
NICK = "nickname"
HOST = "127.0.0.1"
POST = 6667

server = ircstates.Server("freenode")
sock   = socket.socket()
events = ircevents.Engine(sock)

sock.connect((HOST, POST))

def _send(text):
    line = irctokens.tokenise(text)
    server.send(line)

def _sent(source, state):
    if not state.get("init"):
        state.set("init", True)
        _send(f"USER {NICK} 0 * :{NICK}")
        _send(f"NICK {NICK}")

    while server.pending():
        send_lines = server.sent(source.send(server.pending()))
        for line in send_lines:
            print(f"< {line.format()}")

@events.when(always_run=True)
def _display(line, state):
    print(f"> {line.format()}")

@events.when(command="PING")
def _ping(line, state)
    _send(f"PONG {line.params[0]}")

@events.when(command="001")
def _join(line, state):
    channels = state.get("channels", list())
    for channel in channels:
        if channel not in server.channels:
            _send(f"JOIN {channel}")

    state.set("joined_channels", True)

# Load ircstates as a state mutation
events.use("ircstates", lambda raw: server.recv(raw))

# Events will be received using 1024 bytes from socket
events.recv_with(lambda source, state: source.recv(1024))

# Before processing new data, send queued data to server
events.pre_process(_sent)

# Define what channels to join
events.ns_set("ircstates", "channels", ["#bots", "#test"])

# Run event loop
events.run()
