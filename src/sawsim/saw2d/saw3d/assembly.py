"""Vectorised assembly of the piezoelectric stiffness / mass matrices with PML.

Ports ``formStiffnessMass3D.m`` and the ``elastic_stiffness_matrix*.m`` family
(``AssemblyKM3D_vect``).  The global DOF ordering is ``[u | phi]`` with the u
block interleaved (node ``n`` -> ``3n,3n+1,3n+2``) and the phi block appended.

.. note::
   **Faithful-port quirk.**  The MATLAB strain-displacement matrix writes the
   ``dUz/dy`` entry of the yz-strain row to the wrong slot (index 15 instead of
   16, 1-based) where it is immediately overwritten by ``dUz/dz``.  The yz strain
   therefore ends up with only the ``dUy/dz`` term.  This is reproduced here
   verbatim so the Python results match the MATLAB ``Y11.mat`` reference; see the
   ``vb[14::18]`` line below.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from .elements import quadrature_volume_h27, local_basis_volume_h27

# conditioning scale applied to the u-u / phi-u blocks and the mass matrix
KM_SCALE = 6.723363908816403e-11

# 1-based Gmsh physical-group ids whose PML stretches the x direction
_X_REGIONS = {1, 5, 6, 7, 8, 9, 10, 11}


# --------------------------------------------------------------------- helpers
def _geometry(elem, coord, dhat1, dhat2, dhat3, wf):
    """Jacobian-based physical derivatives and integration weights.

    Returns ``dphi1, dphi2, dphi3`` of shape (n_p, n_int), ``weight`` (n_int,).
    Integration points are element-major: column ``e*n_q + q``.
    """
    n_e, n_p = elem.shape
    n_q = wf.size

    dhp1 = np.tile(dhat1, (1, n_e))               # (n_p, n_int)
    dhp2 = np.tile(dhat2, (1, n_e))
    dhp3 = np.tile(dhat3, (1, n_e))

    # element node coordinates -> (n_p, n_e)
    ce1 = coord[elem, 0].T
    ce2 = coord[elem, 1].T
    ce3 = coord[elem, 2].T
    # repeat each element column n_q times -> (n_p, n_int)
    ci1 = np.repeat(ce1, n_q, axis=1)
    ci2 = np.repeat(ce2, n_q, axis=1)
    ci3 = np.repeat(ce3, n_q, axis=1)

    j11 = np.sum(ci1 * dhp1, axis=0); j12 = np.sum(ci2 * dhp1, axis=0); j13 = np.sum(ci3 * dhp1, axis=0)
    j21 = np.sum(ci1 * dhp2, axis=0); j22 = np.sum(ci2 * dhp2, axis=0); j23 = np.sum(ci3 * dhp2, axis=0)
    j31 = np.sum(ci1 * dhp3, axis=0); j32 = np.sum(ci2 * dhp3, axis=0); j33 = np.sum(ci3 * dhp3, axis=0)

    det = (j11 * (j22 * j33 - j32 * j23)
           - j12 * (j21 * j33 - j23 * j31)
           + j13 * (j21 * j32 - j22 * j31))

    ji11 = (j22 * j33 - j23 * j32) / det; ji12 = -(j12 * j33 - j13 * j32) / det; ji13 = (j12 * j23 - j13 * j22) / det
    ji21 = -(j21 * j33 - j23 * j31) / det; ji22 = (j11 * j33 - j13 * j31) / det; ji23 = -(j11 * j23 - j13 * j21) / det
    ji31 = (j21 * j32 - j22 * j31) / det; ji32 = -(j11 * j32 - j12 * j31) / det; ji33 = (j11 * j22 - j12 * j21) / det

    dphi1 = ji11 * dhp1 + ji12 * dhp2 + ji13 * dhp3
    dphi2 = ji21 * dhp1 + ji22 * dhp2 + ji23 * dhp3
    dphi3 = ji31 * dhp1 + ji32 * dhp2 + ji33 * dhp3

    weight = np.abs(det) * np.tile(wf, n_e)
    return dphi1, dphi2, dphi3, weight


def _u_dofs(elem):
    """(3*n_p, n_e) interleaved u-DOF ids: row r, elem e -> 3*elem[e,r//3]+r%3."""
    n_e, n_p = elem.shape
    node = np.repeat(np.arange(n_p), 3)           # [0,0,0,1,1,1,...]
    comp = np.tile(np.arange(3), n_p)             # [0,1,2,0,1,2,...]
    return 3 * elem[:, node].T + comp[:, None]


def _b_matrix(dphi1, dphi2, dphi3, elem, n_n):
    """Sparse strain-displacement matrix B, shape (6*n_int, 3*n_n)."""
    n_p, n_int = dphi1.shape
    n_e = elem.shape[0]
    n_q = n_int // n_e
    n_b = 18 * n_p

    vb = np.zeros((n_b, n_int), dtype=dphi1.dtype)
    vb[0::18] = dphi1; vb[11::18] = dphi1; vb[16::18] = dphi1
    vb[5::18] = dphi2; vb[7::18] = dphi2
    vb[4::18] = dphi3; vb[9::18] = dphi3
    vb[14::18] = dphi3                       # faithful quirk: overwrites a DPhi2 write

    aux = np.arange(6 * n_int).reshape(6, n_int, order='F')
    ib = np.tile(aux, (3 * n_p, 1))                       # (18*n_p, n_int)

    aux3 = _u_dofs(elem)                                  # (3*n_p, n_e)
    jb = np.kron(aux3, np.ones((6, n_q), dtype=np.int64)) # (18*n_p, n_int)

    return sp.coo_matrix((vb.ravel(), (ib.ravel(), jb.ravel())),
                         shape=(6 * n_int, 3 * n_n)).tocsr()


def _bfi_matrix(dphi1, dphi2, dphi3, elem, n_n):
    """Sparse potential-gradient matrix Bfi, shape (3*n_int, n_n)."""
    n_p, n_int = dphi1.shape
    n_e = elem.shape[0]
    n_q = n_int // n_e
    n_b = 3 * n_p

    vbfi = np.zeros((n_b, n_int), dtype=dphi1.dtype)
    vbfi[0::3] = dphi1
    vbfi[1::3] = dphi2
    vbfi[2::3] = dphi3

    auxfi = np.arange(3 * n_int).reshape(3, n_int, order='F')
    ibfi = np.tile(auxfi, (n_p, 1))                       # (3*n_p, n_int)

    aux3fi = elem.T                                       # (n_p, n_e) node ids
    jbfi = np.kron(aux3fi, np.ones((3, n_q), dtype=np.int64))

    return sp.coo_matrix((vbfi.ravel(), (ibfi.ravel(), jbfi.ravel())),
                         shape=(3 * n_int, n_n)).tocsr()


# ------------------------------------------------------------- PML stretching
def _stretch_alphas(region, elem_ids, elem, coord, pml, omega):
    """Per-element complex stretch factors (alpha1, alpha2, alpha3)."""
    centre = elem[elem_ids, 26]                  # 27th (centre) node of each elem
    one = np.ones(elem_ids.size, dtype=complex)
    a1 = one.copy(); a2 = one.copy(); a3 = one.copy()

    if region in _X_REGIONS or region in (2, 4):
        x1 = coord[centre, 0]
        d_x = pml['dmax'] * (1.0 - (x1 - pml['xp']) ** 2
                             / (pml['xa'] - pml['xp']) ** 2) ** pml['n']
        a1 = 1.0 + d_x / (1j * omega)
    if region == 3 or region in (2, 4):
        z1 = coord[centre, 2]
        d_z = pml['dmax'] * (1.0 - (z1 - pml['zp']) ** 2
                             / (pml['za'] - pml['zp']) ** 2) ** pml['n']
        a3 = 1.0 + d_z / (1j * omega)
    return a1, a2, a3


def _c_stretch(a1, a2, a3):
    """(n,6,6) stretch multiplier for the stiffness tensor."""
    n = a1.size
    s = np.empty((n, 6, 6), dtype=complex)
    r1 = a2 * a3 / a1; r2 = a1 * a3 / a2; r3 = a1 * a2 / a3
    s[:, 0, :] = np.stack([r1, a3, a2, a3, r1, r1], axis=1)
    s[:, 1, :] = np.stack([a3, r2, a1, r2, a3, a3], axis=1)
    s[:, 2, :] = np.stack([a2, a1, r3, a1, a2, a2], axis=1)
    s[:, 3, :] = s[:, 2, :]
    s[:, 4, :] = s[:, 2, :]
    s[:, 5, :] = s[:, 1, :]
    return s


def _e_stretch(a1, a2, a3):
    """(n,3,6) stretch multiplier for the piezoelectric tensor."""
    n = a1.size
    s = np.empty((n, 3, 6), dtype=complex)
    r1 = a2 * a3 / a1; r2 = a1 * a3 / a2; r3 = a1 * a2 / a3
    s[:, 0, :] = np.stack([r1, a3, a2, a2, a2, a3], axis=1)
    s[:, 1, :] = np.stack([a3, r2, a1, a1, a1, r2], axis=1)
    s[:, 2, :] = np.stack([a2, a1, r3, r3, r3, a1], axis=1)
    return s


def _eps_stretch(a1, a2, a3):
    """(n,3,3) stretch multiplier for the permittivity tensor."""
    n = a1.size
    s = np.empty((n, 3, 3), dtype=complex)
    r1 = a2 * a3 / a1; r2 = a1 * a3 / a2; r3 = a1 * a2 / a3
    s[:, 0, :] = np.stack([r1, a3, a2], axis=1)
    s[:, 1, :] = np.stack([a3, r2, a1], axis=1)
    s[:, 2, :] = np.stack([a2, a1, r3], axis=1)
    return s


def _pml_fields(elem, coord, pml_list, omega, n_int):
    """Build C_pml(36,n_int), e_pml(18,n_int), eps_pml(9,n_int), rho_pml(n_int,)."""
    c_pml = np.zeros((36, n_int), dtype=complex)
    e_pml = np.zeros((18, n_int), dtype=complex)
    eps_pml = np.zeros((9, n_int), dtype=complex)
    rho_pml = np.zeros(n_int, dtype=complex)

    for pml in pml_list:
        ids = np.asarray(pml.get('indx', []), dtype=np.int64)
        if ids.size == 0:
            continue
        a1, a2, a3 = _stretch_alphas(pml['region'], ids, elem, coord, pml, omega)

        c_str = pml['C'][None, :, :] * _c_stretch(a1, a2, a3)        # (n,6,6)
        e_str = (pml['e'][None, :, :] * _e_stretch(a1, a2, a3))      # (n,3,6)
        eps_str = pml['eps'][None, :, :] * _eps_stretch(a1, a2, a3)  # (n,3,3)
        rho1 = pml['rho'] * a1 * a2 * a3                              # (n,)

        # flatten each element's tensor to match the MATLAB ``(:)`` ordering.
        # C, eps : column-major of the (6,6)/(3,3) matrix.
        # e      : column-major of the *transposed* (6,3) matrix == C-order of (3,6).
        c_vec = c_str.transpose(0, 2, 1).reshape(ids.size, 36)
        e_vec = e_str.reshape(ids.size, 18)
        eps_vec = eps_str.transpose(0, 2, 1).reshape(ids.size, 9)

        cols = (27 * ids[:, None] + np.arange(27)).ravel()           # (n*27,)
        c_pml[:, cols] = np.repeat(c_vec, 27, axis=0).T
        e_pml[:, cols] = np.repeat(e_vec, 27, axis=0).T
        eps_pml[:, cols] = np.repeat(eps_vec, 27, axis=0).T
        rho_pml[cols] = np.repeat(rho1, 27)

    return c_pml, e_pml, eps_pml, rho_pml


def _v_el(material_list, n_int):
    """Per-material 0/1 indicator over integration points."""
    v = []
    for mat in material_list:
        ids = np.asarray(mat['indx'], dtype=np.int64)
        vi = np.zeros(n_int)
        if ids.size:
            cols = (27 * ids[:, None] + np.arange(27)).ravel()
            vi[cols] = 1.0
        v.append(vi)
    return v


# --------------------------------------------------------------- main routine
def form_stiffness_mass_3d(elem, coord, material_list, pml_list, omega):
    """Assemble the global ``(mass, stiffness)`` pair, both (GDof, GDof) complex.

    Parameters
    ----------
    elem  : (n_e, 27) int   -- 0-based H27 connectivity.
    coord : (n_n, 3) float  -- node coordinates in metres.
    material_list : list of dict with keys ``rho, C, e, eps, indx``.
    pml_list      : list of dict (see initial_pml); ``indx`` may be empty.
    omega : float           -- angular frequency used to freeze the PML stretch.
    """
    n_e, n_p = elem.shape
    n_n = coord.shape[0]

    xi, wf = quadrature_volume_h27()
    hat_p, dh1, dh2, dh3 = local_basis_volume_h27(xi)
    n_q = wf.size
    n_int = n_e * n_q

    dphi1, dphi2, dphi3, weight = _geometry(elem, coord, dh1, dh2, dh3, wf)

    c_pml, e_pml, eps_pml, rho_pml = _pml_fields(elem, coord, pml_list, omega, n_int)
    v_el = _v_el(material_list, n_int)

    # ---- stiffness tensors at every integration point
    elast_c = c_pml.copy()
    elast_e = e_pml.copy()
    elast_eps = eps_pml.copy()
    rho_elem = rho_pml.copy()
    for mat, vi in zip(material_list, v_el):
        elast_c += mat['C'].flatten('F')[:, None] * vi[None, :]
        elast_e += mat['e'].T.flatten('F')[:, None] * vi[None, :]
        elast_eps += mat['eps'].flatten('F')[:, None] * vi[None, :]
        rho_elem += mat['rho'] * vi

    b = _b_matrix(dphi1, dphi2, dphi3, elem, n_n)        # (6*n_int, 3*n_n)
    bfi = _bfi_matrix(dphi1, dphi2, dphi3, elem, n_n)    # (3*n_int, n_n)

    aux = np.arange(6 * n_int).reshape(6, n_int, order='F')
    auxfi = np.arange(3 * n_int).reshape(3, n_int, order='F')

    # ---- D matrices (block-diagonal over integration points)
    id_uu = np.tile(aux, (6, 1)); jd_uu = np.kron(aux, np.ones((6, 1), dtype=np.int64))
    d_uu = sp.coo_matrix(((elast_c * weight[None, :]).ravel(),
                          (id_uu.ravel(), jd_uu.ravel())),
                         shape=(6 * n_int, 6 * n_int)).tocsr()

    id_uf = np.tile(aux, (3, 1)); jd_uf = np.kron(auxfi, np.ones((6, 1), dtype=np.int64))
    d_uf = sp.coo_matrix(((elast_e * weight[None, :]).ravel(),
                          (id_uf.ravel(), jd_uf.ravel())),
                         shape=(6 * n_int, 3 * n_int)).tocsr()

    id_ff = np.tile(auxfi, (3, 1)); jd_ff = np.kron(auxfi, np.ones((3, 1), dtype=np.int64))
    d_ff = sp.coo_matrix(((elast_eps * weight[None, :]).ravel(),
                          (id_ff.ravel(), jd_ff.ravel())),
                         shape=(3 * n_int, 3 * n_int)).tocsr()

    k_uu = (b.T @ d_uu @ b)          # (3*n_n, 3*n_n)
    k_ufi = (b.T @ d_uf @ bfi)       # (3*n_n, n_n)
    k_fifi = (bfi.T @ d_ff @ bfi)    # (n_n, n_n)

    # ---- consistent mass matrix (u-u block only)
    wrho = (weight * rho_elem).reshape(n_e, n_q)
    m_e = np.einsum('iq,jq,eq->eij', hat_p, hat_p, wrho)   # (n_e, n_p, n_p)
    mass = _scatter_mass(m_e, elem, n_n)

    # ---- conditioning scale & block assembly
    g_dofu = 3 * n_n
    g_dof = 4 * n_n
    k_uu = k_uu * KM_SCALE
    # MATLAB ``stiffnessufi'`` is a conjugate transpose; the PML makes k_ufi
    # complex so the conjugation must be kept to reproduce the reference.
    k_fiu = k_ufi.conj().T * KM_SCALE
    stiffness = sp.bmat([[k_uu, k_ufi], [k_fiu, -k_fifi]], format='csr')

    mass = (mass * KM_SCALE).tocsr()
    # pad mass to (GDof, GDof)
    mass = sp.csr_matrix((mass.data, mass.indices, mass.indptr), shape=(g_dof, g_dof))
    return mass, stiffness


def _scatter_mass(m_e, elem, n_n):
    """Scatter per-element (n_p,n_p) mass blocks into a (4*n_n,4*n_n) sparse matrix."""
    n_e, n_p, _ = m_e.shape
    aux3 = _u_dofs(elem)                                  # (3*n_p, n_e)

    ii, jj = np.meshgrid(np.arange(n_p), np.arange(n_p), indexing='ij')
    ii = ii.ravel(); jj = jj.ravel()                      # node pairs
    # for each node pair and each shared component c
    rows = []; cols = []; vals = []
    for c in range(3):
        rows.append(aux3[3 * ii + c, :])                  # (n_p*n_p, n_e)
        cols.append(aux3[3 * jj + c, :])
        vals.append(m_e[:, ii, jj].T)                     # (n_p*n_p, n_e)
    rows = np.concatenate(rows).ravel()
    cols = np.concatenate(cols).ravel()
    vals = np.concatenate(vals).ravel()
    return sp.coo_matrix((vals, (rows, cols)), shape=(4 * n_n, 4 * n_n))
