"""SawSim: piezoelectric coupled FEM for SAW resonator unit cells."""
__version__ = "2.0.2"

from sawsim import runtime as _runtime  # noqa: F401,E402  (GL shims before gmsh is imported anywhere)

from sawsim.config import SimulationConfig  # noqa: E402
from sawsim.api import Model, sweep, Result  # noqa: E402

__all__ = ["SimulationConfig", "Model", "sweep", "Result", "__version__"]
