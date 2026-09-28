"""Dynamic material catalog, with legacy constants retained for compatibility."""
from copy import deepcopy

SUBSTRATES = [
    {'id':'sp_baseline','name':'压电基板 · 基准数据集 I',
     'description':'复用原单层 SP 完整张量，密度 7450 kg/m³。保留历史数值；原代码 LN 标签不能作为已核实的材料身份。'},
    {'id':'linbo3_tc','name':'LiNbO₃ · TC-SAW 数据集',
     'description':'复用原 TC-SAW 完整 6×6/3×6/3×3 张量，密度 4628 kg/m³。源数据已在其参考器件坐标系；输入欧拉角是相对该参考系的附加旋转，不代表已核实晶圆切型。'},
]
ELECTRODES = [
    {'id':'al_hex35','name':'Al 铝（ν = 0.35）','description':'各向同性：E = 70 GPa，ν = 0.35，ρ = 2700 kg/m³；e = 0，ε = ε₀I。用于 2.5D 四层模板，与 ν = 0.33 数据集并列保留。'},
    {'id':'al','name':'Al 铝（ν = 0.33）','description':'各向同性：E = 70 GPa，ν = 0.33，ρ = 2700 kg/m³；e = 0，ε = ε₀I。'},
    {'id':'cu','name':'Cu 铜','description':'各向同性：E = 120 GPa，ν = 0.34，ρ = 8960 kg/m³；e = 0，ε = ε₀I。'},
]
LAYER_MATERIALS = [
    {'id':'si_cubic_hex','name':'Si 硅 · 立方各向异性','description':'立方晶系：C11 = 166、C12 = 64、C44 = 80 GPa；ρ = 2330 kg/m³，εr = 11.68。'},
    {'id':'polysi_160','name':'Poly-Si 多晶硅（E = 160 GPa）','description':'各向同性：E = 160 GPa，ν = 0.22，ρ = 2320 kg/m³，εr = 4.5。用于 2.5D 四层模板。'},
    {'id':'si_aniso_hex','name':'Si 硅 · 各向异性全张量','description':'完整 6×6 刚度张量；ρ = 2330 kg/m³，εr = 11.8。用于 2.5D 四层模板。'},
    {'id':'si_isotropic','name':'Si 硅 · 各向同性近似','description':'各向同性近似：E = 170 GPa，ν = 0.28，ρ = 2329 kg/m³，εr = 11.7。'},
    {'id':'sio2','name':'SiO₂ 二氧化硅','description':'各向同性：E = 70 GPa，ν = 0.17，ρ = 2200 kg/m³，εr = 4.2。'},
    {'id':'polysi','name':'Poly-Si 多晶硅（E = 169 GPa）','description':'各向同性：E = 169 GPa，ν = 0.22，ρ = 2320 kg/m³，εr = 4.5。'},
    {'id':'sin','name':'Si₃N₄ 氮化硅','description':'各向同性：E = 160 GPa，ν = 0.23，ρ = 3100 kg/m³，εr = 9.7。'},
]

EULER_CONVENTION = {
    'id':'zxz',
    'description':'内禀 ZXZ 欧拉角：α、β、γ（API 字段 phi、theta、psi）将所选材料数据的源参考系映射至器件全局坐标系。角度单位为度；旋转作用于压电衬底及使用该材料的 PML。各向同性电极不受角度影响。TC-SAW 源数据已经过参考系旋转；统一角度约定不会自动对齐不同源晶轴、模型坐标或命名晶圆切型。',
    'formula':'A = Rz(α) Rx(β) Rz(γ); C′ = M C Mᵀ, e′ = A e Mᵀ, ε′ = A ε Aᵀ; Rz(t)=[[cos(t),-sin(t),0],[sin(t),cos(t),0],[0,0,1]], Rx(t)=[[1,0,0],[0,cos(t),-sin(t)],[0,sin(t),cos(t)]]; M is the Voigt stress transformation [xx,yy,zz,yz,xz,xy].',
    'units':'deg',
    'legacy_conversion':'(α, β, γ) = (-ψ_old, -θ_old, -φ_old)',
    'reference':'内禀 ZXZ 欧拉角（z-x′-z″），与主流有限元软件的旋转坐标系定义一致；矩阵形式见 formula 字段。',
}


def get_material_catalog():
    from sawsim.material_library import list_records, record_hash
    records = list_records()
    # list_records sorts numeric-aware versions ascending; expose one current
    # choice per id. Explicit historical versions remain available in registry.
    latest = {record['id']: record for record in records}
    catalog = {'substrates': [], 'electrodes': [], 'layers': [],
               'euler_convention': deepcopy(EULER_CONVENTION)}
    groups = {'substrate': 'substrates', 'electrode': 'electrodes', 'layer': 'layers'}
    for record in latest.values():
        entry = dict(record, hash=record_hash(record),
                     versions=[r['version'] for r in records if r['id'] == record['id']])
        for role in record['roles']:
            catalog[groups[role]].append(deepcopy(entry))
    return catalog
