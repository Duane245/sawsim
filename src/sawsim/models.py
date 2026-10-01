"""SP model registry; builders own geometry, material/PML assignment and boundaries."""
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable
from sawsim.sp_specs import MODEL_SPECS


@dataclass
class BuiltModel:
    model: Any
    materials: list
    material_indices: Any
    pml_regions: list
    boundary_conditions: tuple
    details: dict
    material_data: dict
    displacement_components: int


@dataclass(frozen=True)
class ModelDefinition:
    id: str
    name: str
    mesh_dimension: int
    displacement_components: int
    builder: Callable


def build_sp_family(config):
    from sawsim import runtime
    import gmsh
    import numpy as np
    from sawsim.saw2d import materials, piezo_fem, sweep, gmsh_io
    from sawsim.material_catalog import get_material_catalog
    spec=MODEL_SPECS[config.model_id]
    try:
        if config.model_id=='sp_single_layer':
            from sawsim.mesh_sp import GM
            GM(config.pitch_um,0,config.electrode_um,config.metal_ratio,config.substrate_um,0,config.mesh_um,0,0)
            info=dict(tag_map={16:0,15:1,22:0},pml_tag=22,pml_thickness_m=2*config.pitch_um*1e-6,
                      period_m=2*config.pitch_um*1e-6,layer_tags=[],coordinate_note='Mesh xy equals ordinary source xy.')
        else:
            from sawsim.sp_meshes import build_mesh
            info=build_mesh(config)
        types=gmsh.model.mesh.getElementTypes(2)
        if set(int(t) for t in types)!={10}:
            raise ValueError('网格必须全部为 Q9 四边形；发现其他二维单元类型: '+str(types))
        msh=gmsh_io.harvest_2d_mesh()
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()
    model=piezo_fem.build_model(msh)
    bottom=float(model.pos_m[model.nodes_with_tag(21,msh.LINES3),1].min())
    pml=[piezo_fem.PMLRegion(tag=info['pml_tag'],kind='y',yp=bottom,ya=bottom+info['pml_thickness_m'])]
    left=model.nodes_with_tag(19,msh.LINES3);right=model.nodes_with_tag(20,msh.LINES3)
    if len(left)!=len(right) or not np.allclose(np.sort(model.pos_m[left,1]),np.sort(model.pos_m[right,1]),rtol=0,atol=1e-14):
        raise ValueError('左右周期边界节点不匹配')
    if not np.allclose(model.pos_m[right,0]-model.pos_m[left,0],info['period_m'],rtol=0,atol=1e-14):
        raise ValueError('周期边界宽度与节距不一致')
    angles=[config.euler_phi_deg,config.euler_theta_deg,config.euler_psi_deg]
    from sawsim.material_runtime import resolve_materials
    chosen,source,library_tensors,provenance=resolve_materials(config)
    ids=[config.substrate_material,config.electrode_material]+[layer.material_id for layer in config.layers+config.coatings]
    # TC-SAW dataset tensors live in the xz plane of their reference frame (also when used in sp_stack).
    is_tc=config.model_id=='sp_tcsaw' or (config.model_id=='sp_stack' and config.substrate_material=='linbo3_tc')
    project=materials.project_xz_plane_strain if is_tc else materials.project_xy_plane_strain
    active=chosen if config.mode_extension else [project(m) for m in chosen]
    if config.eta_eps:
        # Dielectric loss on the piezoelectric material only (passive with the port sign in solver.py).
        active=[materials.Material(m.rho,m.C,m.e,m.eps*(1-1j*config.eta_eps)) if i==0 else m for i,m in enumerate(active)]
    strain=[0,2,4] if is_tc else [0,1,5]
    electric=[0,2] if is_tc else [0,1]
    ndisp=3 if config.mode_extension else 2
    catalog=get_material_catalog()
    entries=config.material_snapshots
    region_ids={str(tag):ids[index] for tag,index in info['tag_map'].items()}
    region_names={tag:entries[mid]['name']+(' PML' if int(tag)==info['pml_tag'] else '') for tag,mid in region_ids.items()}
    tensor_data=dict(substrate_source_C_pa=source.C,substrate_source_e_c_m2=source.e,substrate_source_eps_f_m=source.eps,
        substrate_C_pa=chosen[0].C,substrate_e_c_m2=chosen[0].e,substrate_eps_f_m=chosen[0].eps,substrate_rho_kg_m3=chosen[0].rho,
        electrode_C_pa=chosen[1].C,electrode_e_c_m2=chosen[1].e,electrode_eps_f_m=chosen[1].eps,electrode_rho_kg_m3=chosen[1].rho,
        rotation_matrix=materials.rotation_matrix(angles),euler_angles_deg=angles,substrate_id=config.substrate_material,
        electrode_id=config.electrode_material,mode_extension=config.mode_extension,
        solver_substrate_C_pa=active[0].C,solver_substrate_e_c_m2=active[0].e,solver_substrate_eps_f_m=active[0].eps,
        solver_electrode_C_pa=active[1].C,solver_electrode_e_c_m2=active[1].e,solver_electrode_eps_f_m=active[1].eps,
        solver_voigt_indices=[0,1,2,3,4,5] if config.mode_extension else strain,
        solver_electric_indices=[0,1,2] if config.mode_extension else electric,
        material_ids=ids,full_C_pa=np.stack([m.C for m in chosen]),full_e_c_m2=np.stack([m.e for m in chosen]),
        full_eps_f_m=np.stack([m.eps for m in chosen]),rho_kg_m3=np.array([m.rho for m in chosen]),
        solver_C_pa=np.stack([m.C for m in active]),solver_e_c_m2=np.stack([m.e for m in active]),
        solver_eps_f_m=np.stack([m.eps for m in active]),
        coordinate_mapping='source_xz_to_mesh_xy' if is_tc else 'source_xy_to_mesh_xy')
    tensor_data.update(library_tensors)
    details=dict(material_library=provenance,period_m=info['period_m'],pml_thickness_m=info['pml_thickness_m'],pml_bottom_m=bottom,
        pml_interface_m=bottom+info['pml_thickness_m'],pml_tag=info['pml_tag'],
        pml_material_id=ids[info['tag_map'][info['pml_tag']]],
        pml_material_assignment=('lowest backing layer' if info.get('pml_material_role')=='last_backing' else
                                 'source compatibility: primary piezo material, including under backing layers'),
        periodic_node_pairs=len(left),material_regions=region_names,material_region_ids=region_ids,
        substrate_material=entries[config.substrate_material],electrode_material=entries[config.electrode_material],
        euler_convention=catalog['euler_convention'],euler_angles_deg=angles,bloch_phase_rad=0.0,
        substrate_depth_m=config.substrate_um*1e-6,electrode_thickness_m=config.electrode_um*1e-6,
        electrode_width_m=config.pitch_um*config.metal_ratio*1e-6,layers=[layer.model_dump() for layer in config.layers],
        coatings=[layer.model_dump() for layer in config.coatings],layer_role=spec['layer_role'],layer_tags=info['layer_tags'],coordinate_note=info.get('coordinate_note',''),
        tensor_plane='xz mapped to local mesh xy' if is_tc else 'xy',
        source_component_labels=['ux','uz'] if is_tc else ['ux','uy','uz'][:ndisp],
        loss=dict(beta_dk=config.beta_dk,eta_eps=config.eta_eps,scope='piezoelectric layer and its PML'),mesh_info=info)
    return BuiltModel(model=model,materials=active,material_indices=piezo_fem.material_index(model,info['tag_map']),
        pml_regions=pml,boundary_conditions=sweep.bc_periodic(model,msh.LINES3,ndisp=ndisp),
        details=details,material_data=tensor_data,displacement_components=ndisp)


def build_sp_single_layer(config):
    return build_sp_family(config)


def build_sp_double_layer(config):
    return build_sp_family(config)


def build_sp_triple_layer(config):
    return build_sp_family(config)


def build_sp_quad_layer(config):
    return build_sp_family(config)


def build_sp_tcsaw(config):
    return build_sp_family(config)


def build_sp_stack(config):
    return build_sp_family(config)


def build_hex_model(config):
    from sawsim.hex_models import build_hex_model as build
    return build(config)


_BUILDERS={'sp_single_layer':build_sp_single_layer,'sp_double_layer':build_sp_double_layer,
           'sp_triple_layer':build_sp_triple_layer,'sp_quad_layer':build_sp_quad_layer,'sp_tcsaw':build_sp_tcsaw,'sp_stack':build_sp_stack}
MODEL_REGISTRY={key:ModelDefinition(key,spec['name'],3 if key.startswith('sp_2p5d_') else 2,
                2+spec['defaults'].get('mode_extension',1),build_hex_model if key.startswith('sp_2p5d_') else _BUILDERS[key])
                for key,spec in MODEL_SPECS.items()}


def list_models():
    return [dict(deepcopy(MODEL_SPECS[m.id]),id=m.id,mesh_dimension=m.mesh_dimension,
                 displacement_components=m.displacement_components) for m in MODEL_REGISTRY.values()]
