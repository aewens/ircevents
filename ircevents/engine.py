from .helpers import infinitedict, trap

from collections import namedtuple
from functools import wraps
from threading import Thread, Event
from queue import Queue, Empty
from random import choices
from string import ascii_lowercase

def noop(source):
    """
    Performs no operation, used as a default placeholder function
    """
    return None

def dict2tuple(dictionary):
    """
    A dict cannot be hashed by a set, but a namedtuple can
    A random name is used to make the namedtuple easier to track
    """
    name = "".join(choices(ascii_lowercase, k=8))
    ntuple = namedtuple(name, dictionary.keys())
    return ntuple(**dictionary)

def get_class_name(obj):
    """
    Dunders in python are ugly, this gets the class name of an object
    """
    return obj.__class__.__name__

class Engine:
    def __init__(self, source):
        """
        """
        self._source = source
        self._using = set()

        self._recv_callback = noop

        self._namespaces = set()
        self._whens = set()
        self._whens_funcs = dict()
        self._whens_namespaces = dict()
        self._whens_map = defaultdict(set)

        self._events = Queue()
        self._actions = Queue()

    def _get_variables(self, obj):
        """
        Filters out variables from objects into a generator
        """

        for attr_name in dir(obj):
            # Ignores all dunder / private attributes
            if attr_name.startswith("_"):
                continue

            # Ignores functions since we only want variables
            attribute = getattr(obj, attr_name, None)
            if callable(attribute):
                continue

            # Returns both the key and value to return like a dict
            yield (attr_name, attribute)

    def use(self, namespace, callback):
        """
        Defines the mutations that will be applied to the raw text in `process`
        """

        Mutation = namedtuple("Mutation", ["name", "callback"])
        self._using.add(Mutation(namespace, callback))

    def when(self, namespace, **when_kwargs): 
        """
        Decorator used to flag callback functions that the engine will use
        The namespace decides what scope of object to pass to callback
        The when keyword arguments determine what will trigger the callback
        """

        assert namespace in self._namespaces, f"Invalid namespace: {namespace}"

        # Make hashable for set
        whens = dict2tuple(when_kwargs)

        # Extract unique name
        whens_name = get_class_name(whens)

        self._whens.add(whens)

        # Map name to namespace
        self._whens_namespaces[whens_name] = namespace

        # Map keys to name to optimize processing time
        for when_key in whens.keys():
            self._whens_map[when_key].add(whens_name)

        def decorator_when(func):
            # Map name to callback function to run when triggered
            self._whens_funcs[whens_name] = func

            # Pass along function without calling it
            return func

        return decorator_when

    def process(self, raw_line):
        """
        Applies mutations to the raw IRC text and checks it against callbacks
        """

        mutations = dict()
        requires = dict()
        triggered_whens = set()

        # Apply mutations
        for using in self._using:
            mutation = using.callback(raw_line)
            mutations[using.namespace] = mutation 
            for (key, value} in self._get_variables(mutation):
                for using_whens in self._whens_map[key]:
                    for using_when in using_whens:
                        # Already been triggers, skip
                        if using_when in triggered_whens:
                            continue

                        # Check if all required fields are found
                        whens_requires = requires.get(using_when)
                        if whens_requires is None:
                            requires[using_whens] = set(self._whens._fields)
                            whens_requires = requires.get(using_whens)

                        whens_requires.remove(key)

                        # If all requirements are found, trigger callback
                        if len(whens_requires) == 0:
                            triggered_whens.add(using_whens)
