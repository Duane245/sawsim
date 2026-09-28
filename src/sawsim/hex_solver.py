"""Bounded Hex27 thin-slice pipeline; original source-compatible operators."""
import time
import sys
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from sawsim.config import ProgressEvent,ResultManifest
from sawsim.hex_models import build_hex_model
from sawsim.saw2d.saw3d import form_stiffness_mass_3d,build_periodic_operators,FrequencySolver3D,KM_SCALE
from sawsim.saw2d.saw3d.bc_solve import _HAVE_PARDISO
from sawsim.frequency_tasks import charge_stream, worker_count
ROOT=Path(__file__).resolve().parent
MAX_HEX_ELEMENTS=2000
MAX_HEX_NODES=30000


def _front_plot(built,path,title,values=None):
    polygons=built.position_m[built.preview_quads[:,:4]][:,:,[0,2]]*1e6
    fig,ax=plt.subplots(figsize=(5,10))
    if values is None:
        palette=['#4C72B0','#C44E52','#55A868','#8172B2','#CCB974','#64B5CD']
        groups={}
        for tag,label in built.details['material_regions'].items():
            groups.setdefault(label,[]).append(int(tag))
        for index,(label,tags) in enumerate(groups.items()):
            group=np.isin(built.preview_tags,tags)
            if not group.any():continue
            collection=PolyCollection(polygons[group],facecolors=palette[index%len(palette)],edgecolors='#172b3b',linewidths=.45,label=label)
            ax.add_collection(collection)
        ax.legend(loc='upper center',bbox_to_anchor=(.5,-.08),fontsize=7)
    else:
        collection=PolyCollection(polygons,array=np.asarray(values)[built.preview_quads[:,:4]].mean(axis=1),cmap='turbo',edgecolors='face')
        ax.add_collection(collection);fig.colorbar(collection,ax=ax,shrink=.7)
    ax.autoscale_view();ax.set_aspect('equal');ax.set_xlabel('x / um');ax.set_ylabel('z / um')
    ax.set_title(title+'\nFront section y=0 (not volume rendering)',fontsize=9)
    fig.tight_layout();fig.savefig(path,dpi=130,bbox_inches='tight');plt.close(fig)


def run_hex_simulation(cfg,output_dir,on_progress=None,should_cancel=None,*,mesh_only=False):
    from sawsim.solver import atomic_json,dependency_version,publish_mesh
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    if any((out/name).exists() for name in ['manifest.json','mesh.npz','admittance.npz']):
        raise FileExistsError('输出目录已有计算结果，请使用新的输出目录')
    atomic_json(out/'input.json',cfg.model_dump());started=time.time()
    def check():
        if (out/'cancel').exists() or (should_cancel is not None and should_cancel()):raise InterruptedError('任务已取消')
    def progress(stage,done=0,stage_id='mesh',frequency_hz=None):
        check()
        event=ProgressEvent(stage=stage,stage_id=stage_id,completed=done,total=1 if mesh_only else cfg.points,
                            elapsed_seconds=round(time.time()-started,2),frequency_hz=frequency_hz).model_dump()
        atomic_json(out/'progress.json',event)
        if on_progress is not None:on_progress(event)
        check()
    progress('生成 2.5D Hex27 薄片网格')
    built=build_hex_model(cfg);check();mesh=built.mesh;n=mesh.nb_nod;ne=len(mesh.hexas27)
    publish_mesh(out,built.details,position_m=built.position_m,hexas27=mesh.hexas27,material_tags=mesh.hex_tag,
                        quads=built.preview_quads,preview_material_tags=built.preview_tags,mesh_view_axes=[0,2])
    np.savez_compressed(out/'material_data.npz',**built.material_data)
    _front_plot(built,out/'mesh.png',cfg.model_id+' mesh')
    from sawsim.material_runtime import snapshot_manifest
    atomic_json(out/'material_snapshot.json',snapshot_manifest(cfg))
    aperture=built.details['aperture_m']
    meta=dict(model_id=cfg.model_id,model='2.5D periodic thin slice / Hex27',mesh_dimension=3,displacement_components=3,
              component_labels=['ux','uy','uz'],mode_extension=1,kinematics='2.5D periodic thin slice',
              aperture_m=aperture,aperture_um=aperture*1e6,nodes=int(n),elements=int(ne),dofs=int(4*n),
              geometry=built.details,mesh_view_axes=[0,2],mesh_view_note=built.details['mesh_view_note'],
              substrate_material=cfg.substrate_material,electrode_material=cfg.electrode_material,
              euler_angles_deg=[cfg.euler_phi_deg,cfg.euler_theta_deg,cfg.euler_psi_deg],euler_convention=cfg.euler_convention,euler_angle_labels=['alpha','beta','gamma'],euler_rotation='Rz(alpha) Rx(beta) Rz(gamma)',
              backend='PARDISO' if _HAVE_PARDISO else 'SciPy SuperLU',solver_version='0.7.0',
              units={'frequency':'Hz','position':'m','displacement':'m','potential':'V','charge':'C/m reaction',
                     'admittance':'S/m','raw_charge_c':'C reaction','raw_admittance_s':'S','aperture_m':'m'},
              normalization='charge=raw_charge_c/aperture_m; admittance=raw_admittance_s/aperture_m; curve uses S/m',
              sign_convention='Source-compatible potential-equation reaction Q; Y=+i*omega*Q/V. For exp(+iwt), this is outward-current admittance, opposite to standard entering-port Y. Magnitude unchanged.',
              source_compatibility_notes=built.details['source_compatibility_notes'],
              resource_limits={'max_hex_elements':MAX_HEX_ELEMENTS,'max_hex_nodes':MAX_HEX_NODES,'numerical_threads':1},
              python=sys.version,versions={name:dependency_version(name) for name in ['numpy','scipy','gmsh','matplotlib']})
    files=[ROOT/'frequency_tasks.py',ROOT/'hex_solver.py',ROOT/'hex_models.py',ROOT/'solver.py',ROOT/'models.py',ROOT/'config.py',ROOT/'material_runtime.py',*sorted((ROOT/'material_library').glob('*.py')),ROOT/'sp_specs.py',ROOT/'saw2d/materials.py',
           *sorted((ROOT/'sp_hex_meshes').glob('*.py')),*sorted((ROOT/'saw2d/saw3d').glob('*.py'))]
    meta['source_hashes']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    if not mesh_only:
        if ne>MAX_HEX_ELEMENTS or n>MAX_HEX_NODES:
            raise ValueError('Hex27 模型超过本机安全组装上限（2000单元/30000节点），请增大 mesh_um 或减小模型尺寸；已保留真实网格。')
        progress('组装 Hex27 矩阵',stage_id='assembly')
        frequencies=np.linspace(cfg.start_ghz*1e9,cfg.stop_ghz*1e9,cfg.points)
        mass,stiffness=form_stiffness_mass_3d(mesh.hexas27,built.position_m,built.material_type,built.pml,omega=2*np.pi*frequencies[-1])
        check();tfb,tlr=build_periodic_operators(built.boundary,4*n)
        engine=FrequencySolver3D(stiffness,mass,built.boundary,tfb,tlr);meta['active_dofs']=int(engine.n_act);meta.update(frequency_count=cfg.points,frequency_workers=worker_count(cfg.points),pml_reference_frequency_hz=float(frequencies[-1]))
        raw_q=[]
        with charge_stream(engine,frequencies,cfg.voltage,is_hex=True) as results:
            for i,f in enumerate(frequencies):
                progress('真实 Hex27 扫频',i,'sweep',float(f))
                q=next(results)
                if not np.isfinite(q):raise ValueError('Hex27 求解产生非有限电荷')
                raw_q.append(complex(q));y=1j*2*np.pi*frequencies[:i+1]*np.array(raw_q)/(cfg.voltage*aperture)
                atomic_json(out/'curve.json',dict(frequency_ghz=(frequencies[:i+1]*1e-9).tolist(),real=y.real.tolist(),imag=y.imag.tolist(),magnitude=np.abs(y).tolist()))
                progress('真实 Hex27 扫频',i+1,'sweep',float(f))
        progress('生成真实前截面场图',cfg.points,'postprocess')
        raw_q=np.array(raw_q);raw_y=1j*2*np.pi*frequencies*raw_q/cfg.voltage;y=raw_y/aperture
        np.savez_compressed(out/'admittance.npz',frequency_hz=frequencies,charge=raw_q/aperture,admittance=y,
                            raw_charge_c=raw_q,raw_admittance_s=raw_y,aperture_m=aperture)
        np.savetxt(out/'admittance.csv',np.column_stack([frequencies,y.real,y.imag,np.abs(y),raw_y.real,raw_y.imag,raw_q.real,raw_q.imag]),delimiter=',',
                   header='frequency_hz,real_y_s_per_m,imag_y_s_per_m,abs_y_s_per_m,raw_real_y_s,raw_imag_y_s,raw_real_reaction_q_c,raw_imag_reaction_q_c',comments='')
        peak=int(np.argmax(np.abs(y)));state,_,_=engine.solve(2*np.pi*frequencies[peak],voltage=cfg.voltage)
        if not np.isfinite(state).all():raise ValueError('Hex27 场结果包含非有限值')
        displacement=state[:3*n].reshape(n,3)*KM_SCALE;potential=state[3*n:]
        np.savez_compressed(out/'fields.npz',position_m=built.position_m,displacement_m=displacement,potential_v=potential,
                            frequency_hz=frequencies[peak],hexas27=mesh.hexas27,quads=built.preview_quads,
                            mesh_dimension=3,mode_extension=1,displacement_components=3,component_labels=['ux','uy','uz'],mesh_view_axes=[0,2])
        _front_plot(built,out/'disp_field.png','Displacement magnitude / m',np.linalg.norm(displacement,axis=1));check()
        _front_plot(built,out/'phi_field.png','Potential real part / V',potential.real)
        fig,ax=plt.subplots(figsize=(7,4));ax.plot(frequencies*1e-9,np.abs(y));ax.set_xlabel('Frequency / GHz');ax.set_ylabel('|Y| / (S/m)')
        ax.set_title('2.5D periodic slice; normalized by aperture');ax.grid(alpha=.3);fig.tight_layout();fig.savefig(out/'Y11.png',dpi=150);plt.close(fig)
        meta.update(peak_frequency_ghz=float(frequencies[peak]*1e-9),peak_is_boundary=peak in [0,len(y)-1],field_selection='maximum sampled admittance magnitude')
    else:meta['task_kind']='mesh'
    check();meta['elapsed_seconds']=time.time()-started;atomic_json(out/'metadata.json',meta)
    names=['input.json','material_snapshot.json','metadata.json','mesh.npz','material_data.npz','mesh.png','manifest.json']
    if not mesh_only:names += ['curve.json','admittance.npz','admittance.csv','fields.npz','disp_field.png','phi_field.png','Y11.png']
    artifacts=[dict(name=name,kind='image' if name.endswith('.png') else 'data',media_type={'.png':'image/png','.json':'application/json','.csv':'text/csv','.npz':'application/octet-stream'}[Path(name).suffix]) for name in names]
    manifest=ResultManifest(model_id=cfg.model_id,artifacts=artifacts).model_dump();atomic_json(out/'manifest.json',manifest)
    progress('完成',1 if mesh_only else cfg.points,'complete');return manifest
