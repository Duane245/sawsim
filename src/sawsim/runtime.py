"""Optional GL shim libraries for headless Linux (Gmsh needs libGLU/libOpenGL).

Set SAWSIM_VENDOR_LIB_DIR to a directory containing libOpenGL.so.0 / libGLU.so.1, or install
the system packages (Debian/Ubuntu: apt install libglu1-mesa libopengl0).
"""
import ctypes, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(Path(os.environ.get('SAWSIM_HOME', str(Path.home() / '.sawsim'))) / 'mplconfig'))
_dirs = [Path(d) for d in os.environ.get('SAWSIM_VENDOR_LIB_DIR', '').split(os.pathsep) if d] + [ROOT / 'vendor' / 'usr' / 'lib' / 'x86_64-linux-gnu']
for _d in _dirs:
    for _name in ('libOpenGL.so.0', 'libGLU.so.1'):
        _p = _d / _name
        if _p.exists():
            try:
                ctypes.CDLL(str(_p), mode=ctypes.RTLD_GLOBAL)
            except OSError:
                pass

# Quiet Gmsh unless SAWSIM_GMSH_VERBOSE is set (Gmsh prints meshing progress to the terminal).
try:
    import gmsh as _gmsh
    _orig_init = _gmsh.initialize
    def _quiet_initialize(*a, **k):
        _orig_init(*a, **k)
        if not os.environ.get('SAWSIM_GMSH_VERBOSE'):
            _gmsh.option.setNumber('General.Terminal', 0)
            _gmsh.option.setNumber('General.Verbosity', 0)
    _gmsh.initialize = _quiet_initialize
except Exception:  # gmsh missing or GL libs absent: solver will report it later
    pass
