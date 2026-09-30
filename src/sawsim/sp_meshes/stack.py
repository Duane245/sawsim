"""sp_stack: structured Q9 mesh for an arbitrary 2D stack (generalises quad.py).

Cell (2 x pitch wide, one + and one - electrode), bottom to top:
    PML | backing layers (last .. first) | piezo layer | electrodes (+ embedding coating) | coatings

* x: 9 cuts at the electrode edges and centres -> 8 strips, each meshed with
  ceil(width / h) elements, identical on every horizontal line (conforming, periodic).
* y: every material band is meshed with ceil(height / h_band) elements.  Near the surface
  (depth <= 2 pitch = one wavelength, where the SAW lives) h_band = h = mesh_um; deeper
  bands use h_deep = max(h, min(4 h, pitch / 2)); bands crossing that depth are split.
* The first coating embeds the electrodes (its thickness is measured from the piezo
  surface and must exceed the electrode thickness), as in the TC-SAW template.
* The bottom PML (2 x pitch) uses the material of the lowest backing layer, or the piezo
  material when there is no backing.

Physical groups follow the SP convention: 15 electrode, 16 piezo, 22.. backings, then
coatings, then PML; lines 17 (+), 18 (-), 19 left, 20 right, 21 bottom.
"""
import math

import gmsh


def _split(bands, depth):
    """Split (tag, top, bottom, deep) bands (y down-positive depths) at `depth`."""
    out = []
    for tag, top, bot in bands:
        if top < depth < bot - 1e-12:
            out += [(tag, top, depth), (tag, depth, bot)]
        else:
            out.append((tag, top, bot))
    return out


def GM(pitch, MR, Hidt, H_piezo, backings, coatings, mesh_um, pml_pitches=2.0):
    p, h, d = pitch, mesh_um, Hidt
    w = 2 * p
    h_deep = max(h, min(4 * h, p / 2))
    near = 2 * p
    nb, nc = len(backings), len(coatings)
    tag_backing = [22 + i for i in range(nb)]
    tag_coating = [22 + nb + j for j in range(nc)]
    tag_pml = 22 + nb + nc

    # ---- vertical bands below the surface, as depths (top, bottom) >= 0
    bands, z = [(16, 0.0, H_piezo)], H_piezo
    for tag, t in zip(tag_backing, backings):
        bands.append((tag, z, z + t))
        z += t
    bands = _split(bands, near)
    pml_h = pml_pitches * p
    below = [(tag, -bot, -top, max(1, math.ceil((bot - top) / (h if bot <= near + 1e-12 else h_deep) - 1e-9)))
             for tag, top, bot in bands]
    below.append((tag_pml, -(z + pml_h), -z, max(8, math.ceil(pml_h / h_deep - 1e-9))))
    below.sort(key=lambda b: b[1])                         # bottom first
    # ---- bands above the surface: electrode band, then coatings
    above = [('E', 0.0, d, max(1, math.ceil(d / h - 1e-9)))]
    if nc:
        top = coatings[0]
        above.append((tag_coating[0], d, top, max(1, math.ceil((top - d) / h - 1e-9))))
        for tag, t in zip(tag_coating[1:], coatings[1:]):
            above.append((tag, top, top + t, max(1, math.ceil(t / h - 1e-9))))
            top += t
    levels = [b[1] for b in below] + [0.0] + [b[2] for b in above]
    rows = [b[3] for b in below] + [b[3] for b in above]
    band_tag = [b[0] for b in below] + [b[0] for b in above]
    surface_level = len(below)                            # index of y = 0
    electrode_band = surface_level                        # band between y=0 and y=d

    xs = [0, p * (1 - MR) / 2, p / 2, p * (1 + MR) / 2, p, p * (3 - MR) / 2, 1.5 * p, p * (3 + MR) / 2, w]
    cols = [max(1, math.ceil((xs[i + 1] - xs[i]) / h - 1e-9)) for i in range(8)]
    electrode_strips = {1: 15, 2: 15, 5: 15, 6: 15}

    gmsh.initialize()
    gmsh.model.add('SAW_PeriodBC1_stack')
    geo = gmsh.model.geo
    points, hlines, vlines = {}, {}, {}

    def pt(li, xi):
        if (li, xi) not in points:
            points[(li, xi)] = geo.addPoint(xs[xi], levels[li], 0, p)
        return points[(li, xi)]

    def hl(li, xi):
        if (li, xi) not in hlines:
            hlines[(li, xi)] = geo.addLine(pt(li, xi), pt(li, xi + 1))
            geo.mesh.setTransfiniteCurve(hlines[(li, xi)], cols[xi] + 1)
        return hlines[(li, xi)]

    def vl(bi, xi):
        if (bi, xi) not in vlines:
            vlines[(bi, xi)] = geo.addLine(pt(bi, xi), pt(bi + 1, xi))
            geo.mesh.setTransfiniteCurve(vlines[(bi, xi)], rows[bi] + 1)
        return vlines[(bi, xi)]

    groups = {}
    for bi, tag in enumerate(band_tag):
        for xi in range(8):
            if bi == electrode_band:
                material = electrode_strips.get(xi, tag_coating[0] if nc else None)
                if material is None:
                    continue                               # free surface between bare electrodes
            else:
                material = tag
            loop = geo.addCurveLoop([hl(bi, xi), vl(bi, xi + 1), -hl(bi + 1, xi), -vl(bi, xi)])
            s = geo.addPlaneSurface([loop])
            geo.mesh.setTransfiniteSurface(s)
            geo.mesh.setRecombine(2, s)
            groups.setdefault(material, []).append(s)
    geo.synchronize()

    for tag, surfaces in groups.items():
        gmsh.model.addPhysicalGroup(2, surfaces, tag)
    s0, s1 = surface_level, surface_level + 1
    gmsh.model.addPhysicalGroup(1, [hl(s0, 1), hl(s0, 2), vl(s0, 1), vl(s0, 3), hl(s1, 1), hl(s1, 2)], 17)
    gmsh.model.addPhysicalGroup(1, [hl(s0, 5), hl(s0, 6), vl(s0, 5), vl(s0, 7), hl(s1, 5), hl(s1, 6)], 18)
    gmsh.model.addPhysicalGroup(1, [vlines[k] for k in sorted(vlines) if k[1] == 0], 19)
    gmsh.model.addPhysicalGroup(1, [vlines[k] for k in sorted(vlines) if k[1] == 8], 20)
    gmsh.model.addPhysicalGroup(1, [hl(0, xi) for xi in range(8)], 21)

    gmsh.option.setNumber('Mesh.RecombineAll', 1)
    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.setOrder(2)
    return dict(tag_backing=tag_backing, tag_coating=tag_coating, tag_pml=tag_pml, pml_thickness_um=pml_h,
                rows=rows, cols=cols, h_near=h, h_deep=h_deep)
