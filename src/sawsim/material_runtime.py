"""Resolve immutable task snapshots into full tensors before model projection."""
import numpy as np
from sawsim.material_library import record_hash
from sawsim.saw2d.materials import Material, oula_transfer, rotation_matrix


def from_record(record):
    return Material(record['rho_kg_m3'], np.array(record['C_pa'],dtype=float),
                    np.array(record['e_c_m2'],dtype=float),np.array(record['eps_f_m'],dtype=float))


def resolve_materials(config):
    ids=[config.substrate_material,config.electrode_material]+[x.material_id for x in config.layers+config.coatings]
    angles=[[config.euler_phi_deg,config.euler_theta_deg,config.euler_psi_deg],[0.,0.,0.]]
    angles += [[x.euler_phi_deg,x.euler_theta_deg,x.euler_psi_deg] for x in config.layers+config.coatings]
    records=[config.material_snapshots[mid] for mid in ids]
    raw=[from_record(record) for record in records]
    active=[]
    for index,(mat,angle) in enumerate(zip(raw,angles)):
        # Keep historical substrate arithmetic, and unrotated passive tensors exact.
        if index==0 or any(angle):
            c,e,eps=oula_transfer(angle,mat.C,mat.e,mat.eps)
            active.append(Material(mat.rho,c,e,eps))
        else:active.append(mat)
    hashes=[record_hash(record) for record in records]
    tensor_data=dict(material_versions=[x['version'] for x in records],material_hashes=hashes,
        material_rotation_matrices=np.stack([rotation_matrix(a) for a in angles]),
        material_euler_angles_deg=angles,source_full_C_pa=np.stack([m.C for m in raw]),
        source_full_e_c_m2=np.stack([m.e for m in raw]),source_full_eps_f_m=np.stack([m.eps for m in raw]))
    provenance=[dict(id=mid,version=rec['version'],sha256=digest,status=rec['status'],
                     reference_frame=rec['reference_frame'],euler_angles_deg=angle)
                for mid,rec,digest,angle in zip(ids,records,hashes,angles)]
    return active,raw[0],tensor_data,provenance


def snapshot_manifest(config):
    ids=[config.substrate_material,config.electrode_material]+[x.material_id for x in config.layers+config.coatings]
    angles=[[config.euler_phi_deg,config.euler_theta_deg,config.euler_psi_deg],[0.,0.,0.]]
    angles += [[x.euler_phi_deg,x.euler_theta_deg,x.euler_psi_deg] for x in config.layers+config.coatings]
    return dict(schema_version='1.0',euler_convention='zxz',datasets=config.material_snapshots,
        hashes={k:record_hash(v) for k,v in config.material_snapshots.items()},
        assignments=[dict(region=label,material_id=mid,euler_angles_deg=a,rotation_matrix=rotation_matrix(a).tolist())
                     for label,mid,a in zip(['substrate','electrode']+['layer_%d'%i for i in range(len(config.layers))]+['coating_%d'%i for i in range(len(config.coatings))],ids,angles)],
        pml_note='PML inherits its assigned region material and rotation; see metadata.geometry.pml_material_id')
