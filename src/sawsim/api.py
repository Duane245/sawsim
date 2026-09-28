"""Public Python API: Model -> sweep -> Result."""
from __future__ import annotations
import json, shutil, tempfile
from pathlib import Path
from typing import Callable, Optional
import numpy as np

from sawsim.config import SimulationConfig
from sawsim.sp_specs import MODEL_SPECS


class Model:
    """A unit-cell model: template id plus any SimulationConfig fields.

    >>> m = Model("sp_double_layer", pitch_um=1.085, points=101)
    """
    def __init__(self, model_id: str = "sp_single_layer", **params):
        self.config = SimulationConfig.model_validate(dict(params, model_id=model_id))

    @classmethod
    def from_json(cls, path) -> "Model":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**data)

    @staticmethod
    def templates() -> dict:
        return {k: v["name"] for k, v in MODEL_SPECS.items()}

    def to_dict(self) -> dict:
        return self.config.model_dump()

    def __repr__(self):
        c = self.config
        return f"Model({c.model_id!r}, pitch_um={c.pitch_um}, points={c.points}, {c.start_ghz}-{c.stop_ghz} GHz)"


class Result:
    """Results of one sweep, backed by an output directory (curve.json, metadata.json, images, npz)."""
    def __init__(self, output_dir):
        self.dir = Path(output_dir)
        self.manifest = self._load("manifest.json")
        self.metadata = self._load("metadata.json")
        self.curve = self._load("curve.json")

    def _load(self, name):
        p = self.dir / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    @property
    def frequency_ghz(self) -> np.ndarray:
        return np.asarray(self.curve.get("frequency_ghz", []), dtype=float)

    @property
    def admittance(self) -> np.ndarray:
        return np.asarray(self.curve.get("real", []), dtype=float) + 1j * np.asarray(self.curve.get("imag", []), dtype=float)

    @property
    def magnitude(self) -> np.ndarray:
        return np.abs(self.admittance)

    @property
    def peak_frequency_ghz(self) -> Optional[float]:
        return self.metadata.get("peak_frequency_ghz")

    def artifact(self, name: str) -> Path:
        return self.dir / name

    def save(self, target) -> Path:
        """Copy the whole result directory to `target` (created if needed)."""
        target = Path(target)
        if target.resolve() != self.dir.resolve():
            shutil.copytree(self.dir, target, dirs_exist_ok=True)
        return target

    def __repr__(self):
        return f"Result({self.dir}, {len(self.frequency_ghz)} points, peak={self.peak_frequency_ghz} GHz)"


def sweep(model: Model | SimulationConfig | dict, output_dir=None, *, mesh_only: bool = False,
          on_progress: Optional[Callable] = None) -> Result:
    """Run the frequency sweep (or only build the mesh) and return a Result.

    If output_dir is None a fresh temporary directory is used.
    """
    from sawsim.solver import run_simulation
    cfg = model.config if isinstance(model, Model) else model
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="sawsim_"))
    out.mkdir(parents=True, exist_ok=True)
    run_simulation(cfg, str(out), on_progress=on_progress, mesh_only=mesh_only)
    return Result(out)
