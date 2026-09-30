"""JSON-only SP model metadata. Geometry units µm, frequency GHz, voltage V."""
from copy import deepcopy

_BASE = dict(pitch_um=1.085, electrode_um=.17, substrate_um=8., metal_ratio=.5,
             mesh_um=.5, start_ghz=1.5, stop_ghz=2.7, points=41, voltage=1.,
             substrate_material='sp_baseline', electrode_material='al',
             euler_convention='zxz', euler_phi_deg=0., euler_theta_deg=-42., euler_psi_deg=0., mode_extension=1, layers=[])

def _fields(piezo_min, piezo_max, mesh_min=.25, mesh_max=.8):
    return [dict(key=k,label=label,min=lo,max=hi,step=step) for k,label,lo,hi,step in [
        ('pitch_um','节距 (µm)',.8,1.5,.001),('electrode_um','电极厚度 (µm)',.08,.3,.001),
        ('substrate_um','主压电层厚度 (µm)',piezo_min,piezo_max,.01),
        ('metal_ratio','金属化比',.3,.7,.01),('mesh_um','网格尺寸 (µm)',mesh_min,mesh_max,.01),
        ('start_ghz','起始频率 (GHz)',.5,5,.01),('stop_ghz','结束频率 (GHz)',.5,5,.01),
        ('points','频点数',3,1201,1),('voltage','激励电压 (V)',.01,10,.01)]]

MODEL_SPECS = {}

def _add(identifier, name, piezo, layers, role='backing', tc=False):
    defaults=deepcopy(_BASE)
    defaults.update(model_id=identifier,substrate_um=piezo,layers=[dict(material_id=m,thickness_um=h) for m,h in layers])
    if tc:
        defaults.update(pitch_um=.9968,electrode_um=.16633,metal_ratio=.46,mesh_um=.1,
                        start_ghz=1.6,stop_ghz=2.,substrate_material='linbo3_tc',electrode_material='cu',
                        euler_theta_deg=0.,mode_extension=0)
    MODEL_SPECS[identifier]=dict(name=name,defaults=defaults,layer_role=role,layer_count=len(layers),
        supported_mode_extensions=[0] if tc else [0,1],
        numeric_fields=_fields(4 if tc or not layers else .1,30 if tc else (12 if not layers else 3),.08 if tc else .25,.25 if tc else .8),
        layer_thickness_min_um=.02,layer_thickness_max_um=15.,
        notes=('TC 局部网格 x/y 对应材料全局 x/z；内涂层厚度须大于电极厚度；PML厚度=4倍节距。' if tc else '底部 PML 沿用主压电材料，厚度=2倍节距。'))

_add('sp_single_layer','SP 单层',8,[])
_add('sp_double_layer','SP 双层',.6,[('si_isotropic',8.33)])
_add('sp_triple_layer','SP 三层',.6,[('sio2',.5),('polysi',6.9)])
_add('sp_quad_layer','SP 四层',.6,[('sio2',.5),('polysi',1.),('si_isotropic',7.83)])
_add('sp_tcsaw','SP TC-SAW',15.9488,[('sio2',.72144),('sin',.04)],role='coating',tc=True)

for _field in MODEL_SPECS['sp_tcsaw']['numeric_fields']:
    if _field['key'] in ('pitch_um','electrode_um','substrate_um'):
        _field['step'] = .00001
MODEL_SPECS['sp_tcsaw']['notes'] += ' 底部 PML 沿用主压电材料。'

# Original SP_3D examples: 3D Hex27 slabs with two zero-phase periodic pairs.
for _suffix,_name,_piezo,_layers in [
    ('single','单层',6.51,[]),
    ('double','双层',.6,[('si_cubic_hex',6.51)]),
    ('triple','三层',.6,[('sio2',.5),('polysi',6.51)]),
    ('quad','四层',.6,[('sio2',.5),('polysi_160',1.),('si_aniso_hex',6.)])]:
    _id='sp_2p5d_'+_suffix+'_layer'
    _add(_id,'2.5D SP '+_name+'（Hex27）',_piezo,_layers)
    _spec=MODEL_SPECS[_id]
    _spec['supported_mode_extensions']=[1]
    _spec['mesh_dimension']=3
    _spec['element_family']='Hex27'
    _start,_stop={'single':(1.5,2.7),'double':(1.75,2.),'triple':(1.6,2.),'quad':(1.8,2.1)}[_suffix]
    _spec['defaults'].update(start_ghz=_start,stop_ghz=_stop)
    _spec['defaults'].update(euler_theta_deg=48.,mesh_um=.2 if _suffix=='quad' else .217,
                            aperture_um=.25 if _suffix=='quad' else .217)
    if _suffix=='quad':
        _spec['defaults'].update(pitch_um=1.,electrode_material='al_hex35')
    for _field in _spec['numeric_fields']:
        if _field['key']=='mesh_um':_field.update(min=.1,max=.5,step=.001)
    _spec['numeric_fields'].append(dict(key='aperture_um',label='周期薄片宽度 (µm)',min=.05,max=.5,step=.001))
    _spec['notes']='3D Hex27 薄片，左右与前后均为零相位周期约束；准确称 2.5D，不是任意三维器件。PML 使用最下方背衬材料；无背衬时使用主压电材料。'

# Generic 2D stack: 0-6 backing layers under the piezo layer, 0-3 coatings over the electrodes.
_add('sp_stack','SP 通用叠层（Q9，0–6 背衬层 + 0–3 覆盖层）',8,[])
_stack=MODEL_SPECS['sp_stack']
_stack.update(layer_count=None,layer_count_range=[0,6],coating_count_range=[0,3],
              layer_thickness_min_um=.005,layer_thickness_max_um=100.,
              numeric_fields=[dict(key=k,label=label,min=lo,max=hi,step=step) for k,label,lo,hi,step in [
                  ('pitch_um','节距 (µm)',.1,20,.0001),('electrode_um','电极厚度 (µm)',.005,2,.0001),
                  ('substrate_um','主压电层厚度 (µm)',.05,100,.001),('metal_ratio','金属化比',.15,.85,.01),
                  ('mesh_um','网格尺寸 (µm)',.01,1,.001),('start_ghz','起始频率 (GHz)',.02,20,.001),
                  ('stop_ghz','结束频率 (GHz)',.02,20,.001),('points','频点数',3,1201,1),('voltage','激励电压 (V)',.01,10,.01)]],
              notes='通用二维叠层：layers 为压电层下方的背衬层（自上而下，0–6 层），coatings 为电极上方的覆盖层（由内向外，0–3 层，'
                    '第一层从压电表面起算并包埋电极，须厚于电极）。结构化 Q9 网格：表面以下 2 倍节距内单元尺寸 = mesh_um，更深处放宽。'
                    '底部 PML 厚 2 倍节距，材料取最下层背衬（无背衬时取压电材料）。仅衬底可为压电材料。'
                    '衬底为 linbo3_tc 时沿用 TC-SAW 数据集的 xz 平面映射。')

for _id,_spec in MODEL_SPECS.items():
    if _id.startswith('sp_2p5d_'):
        _spec['notes'] += ' 源兼容 Hex27 内核保留历史 γyz 项缺失，尚非通用三维精度认证。'
