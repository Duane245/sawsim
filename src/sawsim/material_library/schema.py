"""Material records in SI units; validation intentionally imports no NumPy."""
from math import isfinite, sqrt
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

UNITS = {'rho': 'kg/m^3', 'C': 'Pa', 'e': 'C/m^2', 'eps': 'F/m'}


def _matrix(matrix, n, m, name):
    if len(matrix) != n or any(len(row) != m for row in matrix):
        raise ValueError('%s must have shape %sx%s' % (name, n, m))
    if any(not isfinite(x) for row in matrix for x in row):
        raise ValueError('%s must contain finite numbers' % name)


def _positive_definite(matrix, name):
    n = len(matrix)
    scale = max(abs(x) for row in matrix for x in row)
    if scale == 0:
        raise ValueError('%s must be positive definite' % name)
    if any(abs(matrix[i][j]-matrix[j][i]) > scale*1e-12 for i in range(n) for j in range(n)):
        raise ValueError('%s must be symmetric (relative tolerance 1e-12)' % name)
    # Normalize for safe finite intermediate arithmetic, without altering records.
    L = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            value = matrix[i][j]/scale - sum(L[i][k]*L[j][k] for k in range(j))
            if i == j:
                if not isfinite(value) or value <= 0:
                    raise ValueError('%s must be positive definite' % name)
                L[i][j] = sqrt(value)
            else:
                L[i][j] = value/L[j][j]


class MaterialRecord(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    id: str = Field(pattern=r'^[a-z][a-z0-9_]{0,63}$')
    version: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$')
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=8000)
    roles: List[Literal['substrate', 'electrode', 'layer']] = Field(min_length=1, max_length=3)
    status: Literal['legacy', 'literature', 'user']
    source: str = Field(min_length=1, max_length=8000)
    reference_frame: str = Field(min_length=1, max_length=4000)
    temperature_k: Optional[float] = Field(default=None, gt=0)
    symmetry: str = Field(min_length=1, max_length=100)
    constitutive: Literal['stress_charge']
    voigt_order: Literal['xx,yy,zz,yz,xz,xy']
    units: Dict[str, str]
    rho_kg_m3: float = Field(gt=0)
    C_pa: List[List[float]]
    e_c_m2: List[List[float]]
    eps_f_m: List[List[float]]

    @field_validator('name', 'description', 'source', 'reference_frame', 'symmetry')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('text fields must not be blank')
        return value

    @field_validator('rho_kg_m3', 'temperature_k', 'C_pa', 'e_c_m2', 'eps_f_m', mode='before')
    @classmethod
    def numeric_only(cls, value):
        def check(item):
            if isinstance(item, (list, tuple)):
                for child in item:
                    check(child)
            elif item is not None and (isinstance(item, bool) or not isinstance(item, (int, float))):
                raise ValueError('material values must be numeric, not strings or booleans')
        check(value)
        return value

    @model_validator(mode='after')
    def validate_tensors(self):
        if self.units != UNITS:
            raise ValueError('units must exactly match SI: '+str(UNITS))
        if len(set(self.roles)) != len(self.roles):
            raise ValueError('roles must be unique')
        _matrix(self.C_pa, 6, 6, 'C_pa')
        _matrix(self.e_c_m2, 3, 6, 'e_c_m2')
        _matrix(self.eps_f_m, 3, 3, 'eps_f_m')
        if set(self.roles) & {'electrode', 'layer'} and any(x != 0 for row in self.e_c_m2 for x in row):
            raise ValueError('electrode and layer roles currently require zero piezoelectric tensor e_c_m2')
        _positive_definite(self.C_pa, 'C_pa')
        _positive_definite(self.eps_f_m, 'eps_f_m')
        return self
