"""Bounded, ordered frequency solves; existing FEM engines remain unchanged."""
from contextlib import contextmanager
import multiprocessing as mp
import os
import numpy as np

_engine = None
_voltage = None
_hex = False


def worker_count(points):
    configured = os.environ.get('SAW_SWEEP_WORKERS')
    workers = int(configured) if configured is not None else (8 if points > 41 else 1)
    if not 1 <= workers <= 8:
        raise ValueError('SAW_SWEEP_WORKERS must be an integer from 1 to 8')
    if 'fork' not in mp.get_all_start_methods():
        return 1
    return min(workers, points, os.cpu_count() or 1)


def _initialize(engine, voltage, is_hex):
    global _engine, _voltage, _hex
    _engine, _voltage, _hex = engine, voltage, is_hex


def _charge(frequency):
    kwargs = {'voltage': _voltage} if _hex else {'V': _voltage}
    return complex(_engine.solve(2*np.pi*frequency, **kwargs)[1])


@contextmanager
def charge_stream(engine, frequencies, voltage, *, is_hex=False):
    """Yield charges in frequency order; clean up workers on failure/cancellation.

    Fork workers inherit the already assembled read-only matrices. Each engine's
    existing backend handles its process-local factorization. Only scalar
    charges return to the parent; full fields are solved once at the peak.
    """
    count = worker_count(len(frequencies))
    if count == 1:
        kwargs = {'voltage': voltage} if is_hex else {'V': voltage}
        yield (complex(engine.solve(2*np.pi*f, **kwargs)[1]) for f in frequencies)
        return
    pool = mp.get_context('fork').Pool(count, initializer=_initialize,
                                       initargs=(engine, voltage, is_hex))
    try:
        yield pool.imap(_charge, frequencies, chunksize=1)
    except BaseException:
        pool.terminate()
        raise
    else:
        pool.close()
    finally:
        pool.join()
