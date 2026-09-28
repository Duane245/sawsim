"""Reference-element data for the 27-node hexahedron (``H27``).

Ports ``quadrature_volume.m``, ``local_basis_volume.m`` and ``sortSF27.m`` for the
``H27`` element used by the 3-D SAW solver.

The H27 shape functions are products of three 1-D quadratic factors

    m(t) = t*(t-1)      (corner at t = -1)
    p(t) = t*(t+1)      (corner at t = +1)
    z(t) = (t+1)*(t-1)  (mid-node at t =  0)

This factored form is algebraically identical to the fully expanded
``naturalDerivatives`` blocks in ``local_basis_volume.m`` (product rule), but far
less error prone.  ``sortSF27`` then reorders the 27 functions to the node
numbering used by the Gmsh ``.m`` export.
"""

from __future__ import annotations

import numpy as np

_G = 0.774596669241483           # sqrt(3/5)
_W5 = 0.555555555555556          # 5/9
_W8 = 0.888888888888889          # 8/9

# (sign*scale, factor in xi1, xi2, xi3) for the 27 raw shape functions,
# in the order used inside local_basis_volume.m before sortSF27.
_TABLE = [
    (1 / 8, 'm', 'm', 'm'), (1 / 8, 'p', 'm', 'm'), (1 / 8, 'p', 'p', 'm'),
    (1 / 8, 'm', 'p', 'm'), (1 / 8, 'm', 'm', 'p'), (1 / 8, 'p', 'm', 'p'),
    (1 / 8, 'p', 'p', 'p'), (1 / 8, 'm', 'p', 'p'),
    (-1 / 4, 'z', 'm', 'm'), (-1 / 4, 'p', 'z', 'm'), (-1 / 4, 'z', 'p', 'm'),
    (-1 / 4, 'm', 'z', 'm'), (-1 / 4, 'm', 'm', 'z'), (-1 / 4, 'p', 'm', 'z'),
    (-1 / 4, 'p', 'p', 'z'), (-1 / 4, 'm', 'p', 'z'), (-1 / 4, 'z', 'm', 'p'),
    (-1 / 4, 'p', 'z', 'p'), (-1 / 4, 'z', 'p', 'p'), (-1 / 4, 'm', 'z', 'p'),
    (1 / 2, 'z', 'z', 'm'), (1 / 2, 'z', 'm', 'z'), (1 / 2, 'p', 'z', 'z'),
    (1 / 2, 'z', 'p', 'z'), (1 / 2, 'm', 'z', 'z'), (1 / 2, 'z', 'z', 'p'),
    (-1.0, 'z', 'z', 'z'),
]

# sortSF27.m: A[i] = a[_PERM[i]]   (0-based)
_PERM = np.array([6, 5, 4, 7, 2, 1, 0, 3,
                  17, 18, 14, 16, 13, 19, 12, 15, 9, 10, 8, 11,
                  25, 22, 23, 21, 24, 20, 26])


def _factor(name, t):
    if name == 'm':
        return t * (t - 1.0)
    if name == 'p':
        return t * (t + 1.0)
    return (t + 1.0) * (t - 1.0)        # 'z'


def _dfactor(name, t):
    if name == 'm':
        return 2.0 * t - 1.0
    if name == 'p':
        return 2.0 * t + 1.0
    return 2.0 * t                      # 'z'


def quadrature_volume_h27():
    """27-point (3x3x3) Gauss rule. Returns ``(xi, wf)`` with shapes (3, 27), (27,)."""
    g = [-_G, 0.0, _G]
    w = [_W5, _W8, _W5]
    xi = np.zeros((3, 27))
    wf = np.zeros(27)
    k = 0
    for k3 in range(3):
        for k2 in range(3):
            for k1 in range(3):
                xi[:, k] = (g[k1], g[k2], g[k3])
                wf[k] = w[k1] * w[k2] * w[k3]
                k += 1
    return xi, wf


def local_basis_volume_h27(xi):
    """Shape functions and natural derivatives of the H27 element.

    Parameters
    ----------
    xi : (3, n_q) array -- quadrature-point coordinates.

    Returns
    -------
    hat_p, dhat_p1, dhat_p2, dhat_p3 : each (27, n_q), already sortSF27-ordered.
    """
    xi1, xi2, xi3 = xi[0, :], xi[1, :], xi[2, :]
    n_q = xi.shape[1]

    shape = np.zeros((27, n_q))
    d1 = np.zeros((27, n_q))
    d2 = np.zeros((27, n_q))
    d3 = np.zeros((27, n_q))

    for k, (coef, f1, f2, f3) in enumerate(_TABLE):
        a1, a2, a3 = _factor(f1, xi1), _factor(f2, xi2), _factor(f3, xi3)
        shape[k] = coef * a1 * a2 * a3
        d1[k] = coef * _dfactor(f1, xi1) * a2 * a3
        d2[k] = coef * a1 * _dfactor(f2, xi2) * a3
        d3[k] = coef * a1 * a2 * _dfactor(f3, xi3)

    return shape[_PERM], d1[_PERM], d2[_PERM], d3[_PERM]
