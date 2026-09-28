"""Display-only exterior extraction from saved Gmsh Hex27 connectivity."""
import numpy as np

# Gmsh type 12 local numbering. Each row is outward corners, edge midpoints,
# then face centre, in the same order as a Gmsh Quad9.
HEX27_FACES = np.array([
    [0, 3, 2, 1, 9, 13, 11, 8, 20],
    [4, 5, 6, 7, 16, 18, 19, 17, 25],
    [0, 1, 5, 4, 8, 12, 16, 10, 21],
    [1, 2, 6, 5, 11, 14, 18, 12, 23],
    [2, 3, 7, 6, 13, 15, 19, 14, 24],
    [3, 0, 4, 7, 9, 10, 17, 15, 22],
], dtype=np.int64)


def exterior_hex27_faces(hexas27, material_tags):
    """Return actual outer Quad9 faces with their owning volume material tags.

    Shared cell faces, including internal material interfaces, are removed.
    Pair by corner IDs and verify all nine IDs match to reject nonconformity.
    No new nodes, geometry, mesh generation or FEM computation is introduced.
    """
    cells = np.asarray(hexas27)
    tags = np.asarray(material_tags)
    if cells.ndim != 2 or cells.shape[1] != 27 or len(tags) != len(cells):
        raise ValueError('Invalid Hex27 connectivity or material tag count')
    seen = {}
    for cell, tag in zip(cells, tags):
        for local_face in HEX27_FACES:
            face = cell[local_face]
            key = tuple(sorted(face[:4]))
            if key not in seen:
                seen[key] = [face, int(tag), 1]
            else:
                previous = seen[key]
                if previous[2] != 1 or set(previous[0]) != set(face):
                    raise ValueError('Nonconforming or nonmanifold Hex27 face')
                previous[2] = 2
    exterior = [value for value in seen.values() if value[2] == 1]
    return (np.asarray([v[0] for v in exterior], dtype=np.int64).reshape(-1, 9),
            np.asarray([v[1] for v in exterior], dtype=np.int64))
