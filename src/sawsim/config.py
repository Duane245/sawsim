"""Validated SP family inputs; lengths in µm, frequency in GHz, angles in degrees."""
from copy import deepcopy
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field, model_validator, ConfigDict


class LayerConfig(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    material_id: str
    thickness_um: float = Field(gt=0, le=30)
    euler_phi_deg: float = Field(0.0, ge=-360, le=360)
    euler_theta_deg: float = Field(0.0, ge=-360, le=360)
    euler_psi_deg: float = Field(0.0, ge=-360, le=360)


class SimulationConfig(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    model_id: str = 'sp_single_layer'
    mode_extension: int = Field(1, ge=0, le=1, strict=True)
    substrate_material: str = 'sp_baseline'
    electrode_material: str = 'al'
    layers: List[LayerConfig] = Field(default_factory=list)
    coatings: List[LayerConfig] = Field(default_factory=list)
    material_snapshots: Dict[str, dict] = Field(default_factory=dict, max_length=12)
    # phi/theta/psi are intrinsic ZXZ alpha/beta/gamma, in degrees. Convention id 'zxz'; legacy ids accepted as aliases.
    euler_convention: Literal['zxz'] = 'zxz'
    euler_phi_deg: float = Field(0.0, ge=-360, le=360)
    euler_theta_deg: float = Field(-42.0, ge=-360, le=360)
    euler_psi_deg: float = Field(0.0, ge=-360, le=360)
    aperture_um: Optional[float] = Field(None, gt=0)
    pitch_um: float = Field(1.085, gt=0)
    electrode_um: float = Field(0.17, gt=0)
    substrate_um: float = Field(8, gt=0)
    metal_ratio: float = Field(0.5, gt=0, lt=1)
    mesh_um: float = Field(0.5, gt=0)
    start_ghz: float = Field(1.5, gt=0)
    stop_ghz: float = Field(2.7, gt=0)
    points: int = Field(41, ge=3, le=1201, strict=True)
    voltage: float = Field(1.0, gt=0)

    @model_validator(mode='before')
    @classmethod
    def model_defaults(cls, data):
        if not isinstance(data, dict):
            return data
        from sawsim.sp_specs import MODEL_SPECS
        model_id = data.get('model_id','sp_single_layer')
        if not isinstance(model_id,str) or model_id not in MODEL_SPECS:
            raise ValueError('未知模型: ' + str(model_id))
        defaults = deepcopy(MODEL_SPECS[model_id]['defaults'])
        if data.get('euler_convention') in ('reference_zxz', 'zxz_intrinsic'):
            data = dict(data, euler_convention='zxz')
        if data.get('euler_convention') == 'legacy_zxz':
            keys = ('euler_phi_deg', 'euler_theta_deg', 'euler_psi_deg')
            old_defaults = dict(zip(keys, [-defaults[k] for k in reversed(keys)]))
            try:
                angles = [float(data.get(k, old_defaults[k])) for k in keys]
            except (TypeError, ValueError):
                raise ValueError('旧欧拉角必须为有限数值，单位度')
            data = dict(data, **dict(zip(keys, [-v for v in reversed(angles)])))
            data['euler_convention'] = 'zxz'
        return dict(defaults, **data)

    @model_validator(mode='after')
    def validate_model(self):
        from sawsim.sp_specs import MODEL_SPECS
        from sawsim.material_library import get_record
        from sawsim.material_library.schema import MaterialRecord
        references=[(self.substrate_material,'substrate'),(self.electrode_material,'electrode')]
        references += [(layer.material_id,'layer') for layer in self.layers+self.coatings]
        used={mid for mid,role in references}
        if set(self.material_snapshots)-used:
            raise ValueError('材料快照包含未使用的材料 ID')
        snapshots={}
        for mid,role in references:
            try:
                record=MaterialRecord.model_validate(self.material_snapshots[mid] if mid in self.material_snapshots else get_record(mid)).model_dump()
            except KeyError:
                raise ValueError('未知材料: '+mid)
            if record['id']!=mid or role not in record['roles']:
                raise ValueError('材料 ID 或适用区域不匹配: '+mid)
            snapshots[mid]=record
        self.material_snapshots=snapshots
        spec=MODEL_SPECS[self.model_id]
        if self.model_id.startswith('sp_2p5d_'):
            if self.aperture_um is None:
                raise ValueError('2.5D 薄片模型需要 aperture_um')
        elif self.aperture_um is not None:
            raise ValueError('aperture_um 仅适用于 2.5D Hex27 薄片模型')
        if self.mode_extension not in spec['supported_mode_extensions']:
            raise ValueError('该模型不支持所选 ME 模式')
        if spec.get('layer_count_range'):
            lo,hi=spec['layer_count_range']
            if not lo<=len(self.layers)<=hi:
                raise ValueError('该模型的背衬层数须在 %d–%d 之间' % (lo,hi))
        elif len(self.layers)!=spec['layer_count']:
            raise ValueError('该模型需要 %d 个附加层' % spec['layer_count'])
        clo,chi=spec.get('coating_count_range',[0,0])
        if not clo<=len(self.coatings)<=chi:
            raise ValueError('该模型不支持覆盖层（coatings）' if chi==0 else '覆盖层数须在 %d–%d 之间' % (clo,chi))
        if self.model_id=='sp_stack' and self.substrate_material=='linbo3_tc' and self.mode_extension!=0:
            raise ValueError('linbo3_tc（TC-SAW xz 平面数据）只支持 mode_extension=0')
        if self.coatings and self.coatings[0].thickness_um<=self.electrode_um:
            raise ValueError('第一层覆盖层从压电表面起算并包埋电极，厚度必须大于电极厚度')
        for layer in self.layers+self.coatings:
            lower=spec.get('layer_thickness_min_um',0.01)
            upper=spec.get('layer_thickness_max_um',20.0)
            if not lower<=layer.thickness_um<=upper:
                raise ValueError('附加层厚度超出允许范围 [%s,%s] µm' % (lower,upper))
        for field in spec['numeric_fields']:
            value=getattr(self,field['key'])
            if not field['min']<=value<=field['max']:
                raise ValueError('%s 超出允许范围 [%s,%s]' % (field['key'],field['min'],field['max']))
        if self.model_id=='sp_tcsaw' and self.layers[0].thickness_um<=self.electrode_um:
            raise ValueError('TC 内侧包覆层厚度必须大于电极厚度')
        if self.stop_ghz<=self.start_ghz:
            raise ValueError('结束频率必须大于起始频率')
        return self


def config_from_saved(data):
    """Import saved tasks: pre-0.6 inputs without a marker use legacy ZXZ.

    New unmarked API/CLI inputs use the current ZXZ convention; use this only for historical imports.
    """
    cfg=SimulationConfig.model_validate(dict(
        data, euler_convention=data.get('euler_convention', 'legacy_zxz')))
    if not data.get('material_snapshots'):
        # Pre-library tasks used the initial immutable historical datasets.
        from sawsim.material_library import get_record
        for mid,record in list(cfg.material_snapshots.items()):
            if record['status']=='legacy':
                cfg.material_snapshots[mid]=get_record(mid,'1.0.0')
    return cfg


Config=SimulationConfig


class ProgressEvent(BaseModel):
    stage: str
    stage_id: str
    completed: int = Field(ge=0)
    total: int = Field(ge=1)
    elapsed_seconds: float = Field(ge=0)
    frequency_hz: Optional[float] = None


class Artifact(BaseModel):
    name: str
    kind: str
    media_type: str


class ResultManifest(BaseModel):
    schema_version: Literal['1.0'] = '1.0'
    model_id: str
    artifacts: List[Artifact]


from sawsim.models import list_models
MODEL_TEMPLATES=list_models()
