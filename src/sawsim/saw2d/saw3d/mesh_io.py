"""Gmsh ``.m`` mesh reader.

The original MATLAB pipeline generates the mesh with a Gmsh Python script that
writes a MATLAB ``.m`` file containing a struct ``msh`` with fields ``nbNod``,
``POS``, ``QUADS9`` and ``HEXAS27``.  This module parses that same ``.m`` file so
the Python solver uses *exactly* the same mesh as the MATLAB code (no dependency
on the installed Gmsh version).

The returned :class:`Mesh` keeps node ids / element connectivity **0-based**.
The last column of ``QUADS9`` / ``HEXAS27`` is the Gmsh physical-group tag and is
kept separately in ``quad_tag`` / ``hex_tag``.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import numpy as np


@dataclass
class Mesh:
    nb_nod: int                 # number of nodes
    pos: np.ndarray             # (N, 3) node coordinates, mesh units (micrometres)
    quads9: np.ndarray          # (Nq, 9) int, 0-based connectivity of 9-node quads
    quad_tag: np.ndarray        # (Nq,)   int, physical-group tag of each quad
    hexas27: np.ndarray         # (Nh, 27) int, 0-based connectivity of 27-node hexes
    hex_tag: np.ndarray         # (Nh,)   int, physical-group tag of each hex


_HEADER = re.compile(r"msh\.(\w+)\s*=\s*\[")


def read_gmsh_m(path: str) -> Mesh:
    """Parse a Gmsh-exported MATLAB ``.m`` mesh file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()

    nb_nod = int(re.search(r"msh\.nbNod\s*=\s*(\d+)", text).group(1))

    blocks: dict[str, np.ndarray] = {}
    for m in _HEADER.finditer(text):
        name = m.group(1)
        start = m.end()
        end = text.index("]", start)
        rows = []
        for line in text[start:end].splitlines():
            line = line.strip().rstrip(";").strip()
            if not line:
                continue
            rows.append([float(x) for x in line.split()])
        if rows:
            blocks[name] = np.array(rows)

    pos = blocks["POS"][:, :3].astype(float)

    quads = blocks["QUADS9"]
    quads9 = quads[:, :9].astype(np.int64) - 1          # -> 0-based
    quad_tag = quads[:, 9].astype(np.int64)

    hexas = blocks["HEXAS27"]
    hexas27 = hexas[:, :27].astype(np.int64) - 1        # -> 0-based
    hex_tag = hexas[:, 27].astype(np.int64)

    return Mesh(nb_nod=nb_nod, pos=pos, quads9=quads9, quad_tag=quad_tag,
                hexas27=hexas27, hex_tag=hex_tag)
