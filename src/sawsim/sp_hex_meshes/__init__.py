"""Hex27 thin slabs with zero-phase left/right and front/rear periodicity."""
from importlib import import_module
from types import SimpleNamespace


def build_mesh(config):
    name=config.model_id[len('sp_2p5d_'):-len('_layer')]
    if name not in ('single','double','triple','quad'):
        raise ValueError('Unknown Hex27 SP model: '+config.model_id)
    # Both pydantic layer objects and ordinary configuration dictionaries work.
    if any(isinstance(layer,dict) for layer in config.layers):
        values=dict(vars(config));values['layers']=[SimpleNamespace(**layer) if isinstance(layer,dict) else layer for layer in config.layers]
        config=SimpleNamespace(**values)
    import_module('.'+name,__name__).build_mesh(config)
    layer_tags=list(range(9,9+len(config.layers)))
    pml_tag=9+len(config.layers)
    tag_map={7:0,8:1,**{tag:index+2 for index,tag in enumerate(layer_tags)}}
    tag_map[pml_tag]=len(config.layers)+1 if config.layers else 0
    return dict(tag_map=tag_map,pml_tag=pml_tag,pml_thickness_m=2*config.pitch_um*1e-6,
                period_m=2*config.pitch_um*1e-6,aperture_m=config.aperture_um*1e-6,
                layer_tags=layer_tags,coordinate_note='Hex27 slab: x propagation, y aperture, z depth; zero-phase x/y periodic boundaries',
                boundary_tags=dict(left=1,right=2,rear=3,front=4,bottom=5,positive=7,negative=8),
                mesh_dimension=3,displacement_components=3,pml_material_role='last_backing' if config.layers else 'primary_piezo')
