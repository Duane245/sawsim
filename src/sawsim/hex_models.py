"""Original Hex27 periodic thin-slice builders, adapted to project configurations."""
from dataclasses import dataclass
import numpy as np
from sawsim import runtime
import gmsh
from sawsim.saw2d import materials
from sawsim.saw2d.saw3d import harvest_3d_mesh,find_saw_boundary_3ds,boundary_idx_vect_3ds
from sawsim.sp_hex_meshes import build_mesh


@dataclass
class HexModel:
    mesh: object
    position_m: np.ndarray
    material_type: list
    pml: list
    boundary: object
    material_data: dict
    details: dict
    preview_quads: np.ndarray
    preview_tags: np.ndarray


def _front_faces(mesh,position):
    y0=float(position[:,1].min())
    on_front=np.isclose(position[:,1],y0,rtol=0,atol=1e-14)
    owners={}
    for hexa,tag in zip(mesh.hexas27,mesh.hex_tag):
        nodes=hexa[on_front[hexa]]
        if len(nodes)==9:owners[frozenset(nodes.tolist())]=int(tag)
    faces=[];tags=[];seen=set()
    for face in mesh.quads9:
        key=frozenset(face.tolist())
        if key in owners and key not in seen:
            faces.append(face);tags.append(owners[key]);seen.add(key)
    if len(faces)!=len(owners) or not faces:raise ValueError('Cannot recover complete y=0 front section from Hex27 mesh')
    return np.array(faces,dtype=int),np.array(tags,dtype=int)


def _check_pair(sets,position,a,b,axis,span):
    left=sets[a];right=sets[b];other=[i for i in range(3) if i!=axis]
    def ordered(nodes):
        coordinates=np.round(position[nodes][:,other],14)
        return nodes[np.lexsort((coordinates[:,1],coordinates[:,0]))]
    left=ordered(left);right=ordered(right)
    if len(left)!=len(right) or not np.allclose(position[left][:,other],position[right][:,other],rtol=0,atol=1e-13):
        raise ValueError('Hex27 periodic boundary coordinates do not match: '+a+'/'+b)
    if not np.allclose(np.abs(position[right,axis]-position[left,axis]),span,rtol=0,atol=1e-13):
        raise ValueError('Hex27 periodic span does not match geometry: '+a+'/'+b)


def build_hex_model(config):
    try:
        info=build_mesh(config)
        if set(int(t) for t in gmsh.model.mesh.getElementTypes(3))!={12}:
            raise ValueError('2.5D thin-slice model requires only Hex27 volume elements')
        mesh=harvest_3d_mesh()
    finally:
        if gmsh.isInitialized():gmsh.finalize()
    position=mesh.pos*1e-6
    sets=find_saw_boundary_3ds(mesh)
    _check_pair(sets,position,'L','R',0,info['period_m'])
    _check_pair(sets,position,'front','back',1,info['aperture_m'])
    bottom=float(position[sets['bottom'],2].min())
    angles=[config.euler_phi_deg,config.euler_theta_deg,config.euler_psi_deg]
    from sawsim.material_runtime import resolve_materials
    chosen,source,library_tensors,provenance=resolve_materials(config)
    ids=[config.substrate_material,config.electrode_material]+[layer.material_id for layer in config.layers]
    missing=set(int(t) for t in mesh.hex_tag)-set(info['tag_map'])
    if missing:raise ValueError('Unmapped Hex27 material tags: '+str(missing))
    material_type=[dict(rho=chosen[index].rho,C=chosen[index].C,e=chosen[index].e,eps=chosen[index].eps,
                        indx=np.where(mesh.hex_tag==tag)[0])
                   for tag,index in info['tag_map'].items() if tag!=info['pml_tag']]
    pml_index=info['tag_map'][info['pml_tag']];pml_mat=chosen[pml_index]
    pml=[dict(region=1,indx=np.array([],dtype=np.int64)),dict(region=2,indx=np.array([],dtype=np.int64)),
         dict(region=3,indx=np.where(mesh.hex_tag==info['pml_tag'])[0],za=bottom+info['pml_thickness_m'],zp=bottom,
              xa=0.,xp=0.,dmax=1e11,n=3,rho=pml_mat.rho,C=pml_mat.C,e=pml_mat.e,eps=pml_mat.eps)]
    faces,face_tags=_front_faces(mesh,position)
    tensor_data=dict(material_ids=ids,rho_kg_m3=[m.rho for m in chosen],
                     full_C_pa=np.stack([m.C for m in chosen]),full_e_c_m2=np.stack([m.e for m in chosen]),
                     full_eps_f_m=np.stack([m.eps for m in chosen]),
                     substrate_source_C_pa=source.C,substrate_source_e_c_m2=source.e,substrate_source_eps_f_m=source.eps,
                     rotation_matrix=materials.rotation_matrix(angles),euler_angles_deg=angles,
                     mode_extension=1,coordinate_mapping='source_xyz_to_mesh_xyz',pml_material_id=ids[pml_index])
    tensor_data.update(library_tensors)
    details=dict(info,material_library=provenance,material_region_ids={str(tag):ids[index] for tag,index in info['tag_map'].items()},
                 material_regions={str(tag):ids[index]+(' PML' if tag==info['pml_tag'] else '') for tag,index in info['tag_map'].items()},
                 pml_bottom_m=bottom,pml_interface_m=bottom+info['pml_thickness_m'],pml_material_id=ids[pml_index],
                 layers=[layer.model_dump() for layer in config.layers],euler_angles_deg=angles,
                 substrate_material=config.substrate_material,electrode_material=config.electrode_material,
                 mesh_view_axes=[0,2],mesh_view_note='真实前截面 y=0，横轴x、纵轴z；不是三维体渲染。',
                 source_compatibility_notes=['Original Hex27 strain matrix omits du_z/dy in gamma_yz; retained for source regression.',
                     'Original PML Voigt stretch and two-stage periodic condensation retained; not independently validated as general 3D.'])
    return HexModel(mesh,position,material_type,pml,boundary_idx_vect_3ds(sets,position,3*mesh.nb_nod),tensor_data,details,faces,face_tags)
