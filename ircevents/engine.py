from .helpers import infinitedict, trap

from collections import namedtuple, defaultdict
from collections.abc import Iterable
from functools import wraps
from threading import Thread, Event
from queue import Queue, Empty
from random import choices
from string import ascii_lowercase

def noop(*args, **kwargs):
    """
    Performs no operation, used as a default placeholder function
    """
    pass

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

class StateManager:
    """
    Used as a proxy for getting/setting values for an object with limited scope
    """

    def __init__(self):
        pass

    def get(self, key, default=None):
        return getattr(self, key, default)

    def set(self, key, value):
        setattr(self, key, value)

class Engine:
    """
    The front facing interface to use for handling events
    """

    def __init__(self, source):
        self._source = source
        self._using = set()

        self._pre_callback = noop
        self._pre_args = tuple()
        self._pre_kwargs = dict()

        self._post_callback = noop
        self._post_args = tuple()
        self._post_kwargs = dict()

        self._recv_callback = noop
        self._recv_args = tuple()
        self._recv_kwargs = dict()

        self._states = defaultdict(lambda: StateManager())
        self._mutations = dict()

        self._namespaces = set()
        self._whens = dict()
        self._whens_funcs = dict()
        self._whens_namespaces = dict()
        self._whens_map = defaultdict(set)

        self._running = Event()
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

    def _apply_mutations(self, raw):
        """
        Applies mutations and passes them on as generator
        """

        for using in self._using:
            mutations = using.callback(raw)

            not_iterable = [
                isinstance(mutations, (str, bytes)),
                not isinstance(mutations, Iterable)
            ]
            if any(not_iterable):
                mutations = [mutations]

            self._mutations[using.namespace] = mutations
            for mutation in mutations:
                yield (using, mutation)

    def _process_mutations(self, raw, requires, skip_whens):
        """
        Run all mutation variables against callbacks to see if applicable
        """

        for (using, mutation) in self._apply_mutations(raw):
            for (key, value) in self._get_variables(mutation):
                for using_whens in self._whens_map[key]:
                    for using_when in using_whens:
                        # Already been triggers, skip
                        if using_when in skip_whens:
                            continue

                        when = self._whens.get(using_when)
                        if when is None:
                            return None

                        when_requires = requires.get(using_when)
                        if when_requires is None:
                            requires[using_when] = set(when._fields)
                            when_requires = requires.get(using_when)

                        # Check if all required fields are found
                        when_requires.remove(key)
                        if len(whens_requires) > 0:
                            continue

                        # If all requirements are found, stop checking this
                        skip_whens.add(using_when)

                        triggered = self._check_when(when)
                        if not triggered:
                            continue

                        state = self._states[namespace]
                        func = self._whens_funcs.get(when_key)
                        if func is None:
                            return None

                        # Run callback using mutation data and state manager
                        func(data, state)

    def _check_when(self, when):
        """
        Checks if mutation state will trigger callback
        """

        trigger_when = True

        # Use magic pair to always trigger callback
        if when.get("always_run") is True:
            return trigger_when

        # Check if conditions match mutation
        for when_key, when_value in when.items():
            when_path = when_key.split("__")
            pointer = data
            for wpath in when_path:
                if not isinstance(pointer, dict):
                    eprint(f"Invalid path: {when_key}")
                    break

                pointer = pointer.get(wpath)

            when_status = False

            # Value can be a function complex checks 
            if callable(when_value):
                when_status = when_value(pointer)

            else:
                when_status = pointer == when_value

            if not when_status:
                trigger_when = False
                break

        return trigger_when

    def ns_get(self, namespace, key, default=None):
        """
        Shortcut to get namespace value outside of callback
        """
        self._states[namespace].get(key, default)

    def ns_set(self, namespace, key, value):
        """
        Shortcut to set namespace value outside of callback
        """
        self._states[namespace].set(key, value)

    def use(self, namespace, callback):
        """
        Defines the mutations that will be applied to the raw text in `process`
        """

        Mutation = namedtuple("Mutation", ["namespace", "callback"])
        self._using.add(Mutation(namespace, callback))
        self._namespaces.add(namespace)

    def when(self, namespace=None, **when_kwargs): 
        """
        Decorator used to flag callback functions that the engine will use
        The namespace decides what scope of object to pass to callback
        The when keyword arguments determine what will trigger the callback
        """

        # Namespaces are optional if only one is given
        if namespace is None and len(self._namespaces) == 1:
            namespace = list(self._namespaces)[0]

        assert namespace in self._namespaces, f"Invalid namespace: {namespace}"

        # Make hashable for set
        whens = dict2tuple(when_kwargs)

        # Extract unique name
        whens_name = get_class_name(whens)

        self._whens[whens_name] = whens

        # Map name to namespace
        self._whens_namespaces[whens_name] = namespace

        # Map keys to name to optimize processing time
        for when_key in whens._fields:
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

        # Clear out previous mutations
        self._mutations = dict()

        requires = dict()
        skip_whens = set()
        self._process_mutations(raw_line, requires, skip_whens)

    def pre_process(self, callback, *args, **kwargs):
        """
        Anything that needs to be run before each new line is processed
        """

        assert callable(callback), f"Expected function but got: {callback}"
        self._pre_callback = callback
        self._pre_args = args
        self._pre_kwargs = kwargs

    def post_process(self, callback, *args, **kwargs):
        """
        Anything that needs to be run after each new line is processed
        """

        assert callable(callback), f"Expected function but got: {callback}"
        self._post_callback = callback
        self._post_args = args
        self._post_kwargs = kwargs

    def recv_with(self, callback, *args, **kwargs):
        """
        What to run against the source to receive data
        """

        assert callable(callback), f"Expected function but got: {callback}"
        self._recv_callback = callback
        self._recv_args = args
        self._recv_kwargs = kwargs

    def stop(self):
        """
        Passes stop signal to event loop in run function
        """

        self._running.set()

    def run(self):
        """
        The event loop that drives the engine
        Will loop indefinitely until the stopped or gets an exception
        """

        # Run until stopped
        while not self._running.is_set():
            # Run pre callback before processing
            self._pre_callback(self._source, *self._pre_args,
                **self._pre_kwargs)

            try:
                # Extract receive data from source using recv callback
                recv_data = self._recv_callback(self._source, *self._recv_args,
                    **self._recv_kwargs)

            except Exception as e:
                # Any exception not handle by callback should break loop 
                eprint(format_exc())
                break

            # Process received data
            self.process(recv_data)

            # Run post callback before processing
            self._post_callback(self._source, *self._post_args,
                **self._post_kwargs)
