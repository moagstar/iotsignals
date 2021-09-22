import contextlib

from pyinstrument import Profiler

@contextlib.contextmanager
def profile(*args, **kwargs):
    p = Profiler(*args, **kwargs)
    p.start()
    with contextlib.suppress(Exception):
        yield
    p.stop()
    p.print()
