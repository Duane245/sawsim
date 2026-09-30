"""Build full material records (C 6x6, e 3x6, eps 3x3; SI, stress-charge form) from the
independent constants of common crystal classes, in the crystal's own axes (IEEE-style,
Z = symmetry axis).  Orientation is applied later with the ZXZ Euler angles of the config.

Units of the constants passed in: stiffness in GPa, e in C/m^2, relative permittivity,
density in kg/m^3.
"""
from __future__ import annotations

EPS0 = 8.8541878128e-12

SYMMETRIES = {
    'isotropic': dict(required=['E_gpa', 'nu'], optional=['eps_r'],
                      note='elastic E (GPa) and Poisson ratio nu; non-piezoelectric'),
    'cubic': dict(required=['C11', 'C12', 'C44'], optional=['eps_r'],
                  note='m3m (e.g. Si); non-piezoelectric'),
    'hexagonal_6mm': dict(required=['C11', 'C12', 'C13', 'C33', 'C44', 'e15', 'e31', 'e33', 'eps11', 'eps33'],
                          optional=[], note='6mm (AlN, ZnO, GaN); C66 = (C11-C12)/2'),
    'trigonal_3m': dict(required=['C11', 'C12', 'C13', 'C14', 'C33', 'C44', 'e15', 'e22', 'e31', 'e33',
                                  'eps11', 'eps33'],
                        optional=[], note='3m (LiNbO3, LiTaO3); C66 = (C11-C12)/2, +C14/+e22 sign convention '
                                          'as in linbo3_bouchy_2022'),
}


def _zeros(n, m):
    return [[0.0] * m for _ in range(n)]


def tensors(symmetry: str, k: dict):
    """(C_pa, e_c_m2, eps_f_m) for the given symmetry and constants dict."""
    if symmetry not in SYMMETRIES:
        raise ValueError('symmetry must be one of %s' % sorted(SYMMETRIES))
    missing = [x for x in SYMMETRIES[symmetry]['required'] if x not in k]
    if missing:
        raise ValueError('missing constants for %s: %s' % (symmetry, missing))
    G = 1e9
    C, e = _zeros(6, 6), _zeros(3, 6)
    if symmetry == 'isotropic':
        E, nu = k['E_gpa'] * G, k['nu']
        lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
        for i in range(3):
            for j in range(3):
                C[i][j] = lam + (2 * mu if i == j else 0)
            C[i + 3][i + 3] = mu
        er = k.get('eps_r', 1.0)
        eps = [[er * EPS0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    elif symmetry == 'cubic':
        for i in range(3):
            for j in range(3):
                C[i][j] = (k['C11'] if i == j else k['C12']) * G
            C[i + 3][i + 3] = k['C44'] * G
        er = k.get('eps_r', 1.0)
        eps = [[er * EPS0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    else:
        c11, c12, c13, c33, c44 = (k[x] * G for x in ('C11', 'C12', 'C13', 'C33', 'C44'))
        c66 = (c11 - c12) / 2
        C[0][0] = C[1][1] = c11
        C[0][1] = C[1][0] = c12
        C[0][2] = C[2][0] = C[1][2] = C[2][1] = c13
        C[2][2] = c33
        C[3][3] = C[4][4] = c44
        C[5][5] = c66
        e[0][4] = e[1][3] = k['e15']
        e[2][0] = e[2][1] = k['e31']
        e[2][2] = k['e33']
        if symmetry == 'trigonal_3m':
            c14 = k['C14'] * G
            C[0][3] = C[3][0] = c14
            C[1][3] = C[3][1] = -c14
            C[4][5] = C[5][4] = c14
            e[0][5] = -k['e22']
            e[1][0] = -k['e22']
            e[1][1] = k['e22']
        eps = [[0.0] * 3 for _ in range(3)]
        eps[0][0] = eps[1][1] = k['eps11'] * EPS0
        eps[2][2] = k['eps33'] * EPS0
    return C, e, eps


def build_record(*, id: str, name: str, symmetry: str, constants: dict, rho_kg_m3: float, roles,
                 source: str, description: str = '', version: str = '1.0.0',
                 reference_frame: str = '') -> dict:
    """A complete user material record, ready for material_library.import_record."""
    C, e, eps = tensors(symmetry, constants)
    shown = ', '.join('%s=%s' % (key, constants[key]) for key in sorted(constants))
    return dict(
        id=id, version=version, name=name,
        description=description or '%s record built from independent constants: %s; rho=%s kg/m3.'
        % (symmetry, shown, rho_kg_m3),
        roles=list(roles), status='user', source=source,
        reference_frame=reference_frame or ('Crystal axes, Z = symmetry axis; orientation via ZXZ Euler angles.'
                                            if symmetry not in ('isotropic',) else
                                            'Isotropic; orientation-independent.'),
        temperature_k=None, symmetry=symmetry, constitutive='stress_charge', voigt_order='xx,yy,zz,yz,xz,xy',
        units={'rho': 'kg/m^3', 'C': 'Pa', 'e': 'C/m^2', 'eps': 'F/m'},
        rho_kg_m3=float(rho_kg_m3), C_pa=C, e_c_m2=e, eps_f_m=eps)
