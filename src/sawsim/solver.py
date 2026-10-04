"""Unified FEM pipeline and standalone CLI; model builders live in models.py."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR'] = str(ROOT / '.mplconfig')
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key] = '1'
import json
import time
import sys
import hashlib
from importlib.metadata import version, PackageNotFoundError
import numpy as np
from sawsim import runtime
from sawsim.config import SimulationConfig, ProgressEvent, ResultManifest
from sawsim.models import MODEL_REGISTRY
from sawsim.saw2d import piezo_fem, sweep, viz
from sawsim.frequency_tasks import charge_stream, worker_count


def dependency_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed (not required by local NumPy FEM)"


def atomic_json(path, data):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    tmp.replace(path)


def publish_mesh(out, details, **arrays):
    """Publish a complete immutable mesh before assembly/sweep, never a partial ZIP."""
    out=Path(out)
    temporary=out/'.mesh.npz.tmp'
    with temporary.open('wb') as stream:
        np.savez_compressed(stream,**arrays)
    temporary.replace(out/'mesh.npz')
    dimension=3 if 'hexas27' in arrays else 2
    atomic_json(out/'mesh_preview.json',dict(mesh_dimension=dimension,geometry=details,
        mesh_view_axes=[0,2] if dimension==3 else [0,1],
        mesh_view_note=details.get('mesh_view_note','二维 x-y 网格' if dimension==2 else '周期薄片网格')))


def run_simulation(config, output_dir, on_progress=None, should_cancel=None, *, mesh_only=False):
    """Accept dict/SimulationConfig; return manifest dict. Cancellation raises InterruptedError."""
    model_id = config.get('model_id') if isinstance(config, dict) else getattr(config, 'model_id', None)
    if model_id == 'hct_tcsaw':
        raise ValueError('finite-length (HCT) models are not included in the open-source package')
    cfg = config if isinstance(config, SimulationConfig) else SimulationConfig.model_validate(config)
    if cfg.model_id.startswith('sp_2p5d_'):
        from sawsim.hex_solver import run_hex_simulation
        return run_hex_simulation(cfg,output_dir,on_progress,should_cancel,mesh_only=mesh_only)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Backend may pre-save input.json. Never overwrite previous numerical artifacts.
    if any((out / name).exists() for name in ('admittance.npz','manifest.json','mesh.npz')):
        raise FileExistsError('输出目录已有计算结果，请使用新的输出目录')
    atomic_json(out / 'input.json', cfg.model_dump())
    started = time.time()
    def check_cancel():
        if (out / 'cancel').exists() or (should_cancel is not None and should_cancel()):
            raise InterruptedError('任务已取消')
    def progress(stage, done=0, stage_id='mesh', frequency_hz=None):
        check_cancel()
        event = ProgressEvent(stage=stage, stage_id=stage_id, completed=done,
                              total=1 if mesh_only else cfg.points, elapsed_seconds=round(time.time()-started,2),
                              frequency_hz=frequency_hz).model_dump()
        atomic_json(out / 'progress.json', event)
        if on_progress is not None:
            on_progress(event)
        check_cancel()
    progress('生成网格')
    definition = MODEL_REGISTRY[cfg.model_id]
    built = definition.builder(cfg)
    from sawsim.material_runtime import snapshot_manifest
    atomic_json(out/'material_snapshot.json',snapshot_manifest(cfg))
    model = built.model
    np.savez_compressed(out/'material_data.npz', **built.material_data)
    publish_mesh(out,built.details,position_m=model.pos_m,quads=model.quads,material_tags=model.elem_tag)
    viz.plot_mesh(model,str(out/'mesh.png'),title=cfg.model_id+' mesh',tag_labels={int(tag):mid+(' PML' if int(tag)==built.details['pml_tag'] else '') for tag,mid in built.details['material_region_ids'].items()})
    if mesh_only:
        check_cancel()
        atomic_json(out/'metadata.json', dict(
            task_kind='mesh', model_id=cfg.model_id, nodes=int(model.N),
            elements=int(model.ne), mesh_dimension=definition.mesh_dimension,
            displacement_components=built.displacement_components,
            mode_extension=cfg.mode_extension, geometry=built.details,
            elapsed_seconds=time.time()-started, units={'position': 'm'},
            solver_version='0.7.0', euler_convention=cfg.euler_convention, euler_angles_deg=[cfg.euler_phi_deg,cfg.euler_theta_deg,cfg.euler_psi_deg], euler_angle_labels=['alpha','beta','gamma'], euler_rotation='Rz(alpha) Rx(beta) Rz(gamma)', input_file='input.json'))
        artifacts = [dict(name=name, kind='image' if name.endswith('.png') else 'data',
                          media_type='image/png' if name.endswith('.png') else
                          ('application/json' if name.endswith('.json') else 'application/octet-stream'))
                     for name in ['input.json', 'material_snapshot.json', 'metadata.json', 'material_data.npz',
                                  'mesh.npz', 'mesh.png', 'manifest.json']]
        manifest = ResultManifest(model_id=cfg.model_id, artifacts=artifacts).model_dump()
        atomic_json(out/'manifest.json', manifest)
        progress('网格构建完成', 1, stage_id='complete')
        return manifest
    progress('组装矩阵',stage_id='assembly')
    fre = np.linspace(cfg.start_ghz*1e9,cfg.stop_ghz*1e9,cfg.points)
    assemble = piezo_fem.assemble if cfg.mode_extension else piezo_fem.assemble_ME0
    K,M = assemble(model,built.materials,built.material_indices,built.pml_regions,2*np.pi*fre[-1])
    check_cancel()
    engine = sweep.FrequencySolver(K,M,*built.boundary_conditions)
    if cfg.beta_dk:
        # Rayleigh stiffness damping (beta_dK) of the piezoelectric material only (also its PML where the PML is piezo): elastic K_uu.
        from sawsim.saw2d.materials import Material
        damping=[Material(m.rho,m.C,0*m.e,0*m.eps) if i==0 else Material(m.rho,0*m.C,0*m.e,0*m.eps)
                 for i,m in enumerate(built.materials)]
        D,_=assemble(model,damping,built.material_indices,built.pml_regions,2*np.pi*fre[-1])
        engine.set_damping(D,cfg.beta_dk)
    charges=[]
    with charge_stream(engine,fre,cfg.voltage) as results:
        for i,f in enumerate(fre):
            progress('扫频',i,stage_id='sweep',frequency_hz=float(f))
            q = next(results)
            if not np.isfinite(q):
                raise ValueError('求解结果包含非有限值')
            charges.append(complex(q))
            y = -1j*2*np.pi*fre[:i+1]*np.array(charges)/cfg.voltage
            atomic_json(out/'curve.json',dict(frequency_ghz=(fre[:i+1]*1e-9).tolist(),real=y.real.tolist(),imag=y.imag.tolist(),magnitude=np.abs(y).tolist()))
            progress('扫频',i+1,stage_id='sweep',frequency_hz=float(f))
    progress('生成结果',cfg.points,stage_id='postprocess')
    q=np.array(charges); y=-1j*2*np.pi*fre*q/cfg.voltage  # passive sign: Re Y >= 0 for a lossy port
    np.savez_compressed(out/'admittance.npz',frequency_hz=fre,charge=q,admittance=y)
    np.savetxt(out/'admittance.csv',np.column_stack([fre,y.real,y.imag,np.abs(y)]),delimiter=',',header='frequency_hz,real_y,imag_y,abs_y',comments='')
    peak=int(np.argmax(np.abs(y)))
    disp,_,_=engine.solve(2*np.pi*fre[peak],V=cfg.voltage)
    n=model.N
    ndisp=built.displacement_components
    labels=['ux','uy','uz'][:ndisp]
    u=np.column_stack([disp[i*n:(i+1)*n] for i in range(ndisp)])*piezo_fem.SCALE
    phi=disp[ndisp*n:(ndisp+1)*n]
    if not np.isfinite(disp).all():
        raise ValueError('场结果包含非有限值')
    np.savez_compressed(out/'fields.npz',position_m=model.pos_m,displacement_m=u,potential_v=phi,frequency_hz=fre[peak],quads=model.quads,mode_extension=cfg.mode_extension,mesh_dimension=2,displacement_components=ndisp,component_labels=labels)
    viz.plot_y11(fre,np.abs(y),str(out/'Y11.png'),title=cfg.model_id+' admittance')
    check_cancel()
    viz.plot_nodal_field(model,np.linalg.norm(u,axis=1),str(out/'disp_field.png'),title='Displacement magnitude',cbar_label='|u| / m')
    viz.plot_nodal_field(model,phi.real,str(out/'phi_field.png'),title='Potential real part',cbar_label='V')
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'solver.py',ROOT/'frequency_tasks.py',ROOT/'config.py',ROOT/'material_runtime.py',*sorted((ROOT/'material_library').glob('*.py')),ROOT/'models.py',ROOT/'material_catalog.py',ROOT/'mesh_sp.py',ROOT/'sp_specs.py',*sorted((ROOT/'sp_meshes').glob('*.py')),*sorted((ROOT/'saw2d').glob('*.py'))]}
    atomic_json(out/'metadata.json',dict(frequency_count=cfg.points,frequency_workers=worker_count(cfg.points),pml_reference_frequency_hz=float(fre[-1]),nodes=int(n),elements=int(model.ne),dofs=int(K.shape[0]),peak_frequency_ghz=float(fre[peak]*1e-9),peak_is_boundary=peak in (0,len(fre)-1),elapsed_seconds=time.time()-started,python=sys.version,source_hashes=hashes,model='%s Q9 / ME%d, %d displacement components' % (cfg.model_id,cfg.mode_extension,ndisp),backend='PARDISO' if sweep._HAVE_PARDISO else 'SciPy SuperLU',mesh_dimension=definition.mesh_dimension,displacement_components=ndisp,component_labels=labels,mode_extension=cfg.mode_extension,out_of_plane_wavenumber_per_m=0.0,kinematics=('local mesh z = source y; d/d(local z)=0; local uz=source uy=0; source Ey=0' if built.details.get('tensor_plane','').startswith('xz') else ('d/dz=0; uz=0 plane strain, Ez=0' if not cfg.mode_extension else 'd/dz=0; ux,uy,uz active, Ez=0')),model_id=cfg.model_id,geometry=built.details,versions={name:dependency_version(name) for name in ['numpy','scipy','gmsh','pydantic','matplotlib']},units={'frequency':'Hz','position':'m','displacement':'m','potential':'V','admittance':'S/m (unit out-of-plane aperture)','charge':'C/m'},field_selection='maximum sampled admittance magnitude',admittance_convention='passive: Y = -i w Q_reaction / V (Re Y >= 0 for a lossy port; before 2.1 the opposite sign)',loss=dict(beta_dk=cfg.beta_dk,eta_eps=cfg.eta_eps,scope='piezoelectric layer (and a PML made of its material)'),substrate_material=cfg.substrate_material,electrode_material=cfg.electrode_material,euler_angles_deg=[cfg.euler_phi_deg,cfg.euler_theta_deg,cfg.euler_psi_deg],euler_convention=cfg.euler_convention,euler_angle_labels=['alpha','beta','gamma'],euler_rotation='Rz(alpha) Rx(beta) Rz(gamma)',material_data_file='material_data.npz',solver_version='0.7.0',coordinate_note=built.details['coordinate_note'],tensor_plane=built.details['tensor_plane'],source_component_labels=built.details['source_component_labels']))
    check_cancel()
    artifacts=[]
    for path in sorted(out.iterdir()):
        if path.name in {'input.json','material_snapshot.json','metadata.json','curve.json','admittance.csv','admittance.npz','fields.npz','material_data.npz','mesh.npz','mesh.png','Y11.png','disp_field.png','phi_field.png'}:
            media={'.json':'application/json','.csv':'text/csv','.png':'image/png','.npz':'application/octet-stream'}[path.suffix]
            artifacts.append(dict(name=path.name,kind='image' if path.suffix=='.png' else 'data',media_type=media))
    artifacts.append(dict(name='manifest.json',kind='manifest',media_type='application/json'))
    manifest=ResultManifest(model_id=cfg.model_id,artifacts=artifacts).model_dump()
    atomic_json(out/'manifest.json',manifest)
    progress('完成',cfg.points,stage_id='complete')
    return manifest


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mesh-only', action='store_true', help='构建网格（HCT 同时组装基本块），不执行扫频')
    p.add_argument('--legacy-euler', action='store_true', help='导入旧任务角度；缺少约定标记时换算为当前 ZXZ 约定 ZXZ')
    args=p.parse_args()
    data=json.loads(args.config.read_text())
    if args.legacy_euler:
        from sawsim.config import config_from_saved
        data=config_from_saved(data)
    run_simulation(data,args.output,mesh_only=args.mesh_only)
