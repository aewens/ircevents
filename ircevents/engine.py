from .helpers import infinitedict

from collections import namedtuple
from threading import Thread, Event
from queue import Queue, Empty

def noop(source):
    return None

class Engine:
    def __init__(self, source):
        self._source = source
        self._using = list()
        self._mutations = infinitedict()

        self._recv_callback = noop

        self._events = Queue()
        self._actions = Queue()

    def use(self, name, callback):
        Mutation = namedtuple("Mutation", ["name", "callback"])
        self._using.append(Mutation(name, callback))

    def recv_with(self, callback):
        assert callable(callback), f"Expected function but got: {callback}"
        self._recv_callback = callback

    def run(self):
        NotImplemented
