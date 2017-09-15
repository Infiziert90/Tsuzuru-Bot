import sys
import pickle
import signal
import atexit

from dicts import AttrDict


persist_file = "faggot_dict.pkl"

try:
    with open(persist_file, "rb") as f:
        glob = AttrDict(pickle.load(f))
except:
    glob = AttrDict()


def write(*_):
    with open(persist_file, "wb") as f:
        pickle.dump(dict(glob), f, protocol=pickle.HIGHEST_PROTOCOL)


atexit.register(write)
signal.signal(signal.SIGINT, lambda *_: sys.exit())
signal.signal(signal.SIGTERM, lambda *_: sys.exit())
