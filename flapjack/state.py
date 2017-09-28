import copy
import functools
import os.path
import pickle

from . import config

"""Flapjack maintains a state file. This is stored in the workdir
instead of XDG_CACHE_DIR so that you can maintain multiple Flapjack
checkouts if you are hacking on more than one runtime."""

_FILENAME = os.path.join(config.workdir(), 'state.dat')


class _State:
    def __init__(self):
        self.open_modules = []


@functools.lru_cache()
def _read_state():
    try:
        with open(_FILENAME, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        default_state = _State()
        _write_state(default_state)
        return copy.deepcopy(default_state)


def _write_state(state):
    with open(_FILENAME, 'wb') as f:
        pickle.dump(state, f)
    _read_state.cache_clear()


def get_open_modules():
    return copy.deepcopy(_read_state().open_modules)


def set_open_modules(modules):
    state = _read_state()
    state.open_modules = copy.deepcopy(modules)
    _write_state(state)
