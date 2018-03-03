try:
    from _pydevd_reload import *
    _use_c = True
except ImportError:
    from pydevd_reload import *
    _use_c = False
