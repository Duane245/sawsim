"""Parameterized project-local meshes. Caller owns harvest and gmsh.finalize()."""

def _thickness(layer):
    return layer['thickness_um'] if isinstance(layer, dict) else layer.thickness_um


def build_mesh(config):
    identifier = config.model_id
    p = config.pitch_um
    layers = [_thickness(item) for item in config.layers]
    if identifier == 'sp_double_layer':
        from .double import GM
        GM(p, 0, config.electrode_um, config.metal_ratio, config.substrate_um, layers[0], config.mesh_um)
        tags, pml = [22], 23
    elif identifier == 'sp_triple_layer':
        from .triple import GM
        GM(p, 0, config.electrode_um, config.metal_ratio, config.substrate_um, layers[0], layers[1], 0, config.mesh_um, 0, 0)
        tags, pml = [22, 23], 24
    elif identifier == 'sp_quad_layer':
        from .quad import GM
        GM(p, config.metal_ratio, config.electrode_um, config.substrate_um, *layers, 2*p, config.mesh_um)
        tags, pml = [22, 23, 24], 25
    elif identifier == 'sp_tcsaw':
        from .tcsaw import build_mesh as build_tc
        build_tc(p, config.electrode_um, config.substrate_um, config.metal_ratio, config.mesh_um, *layers)
        tags, pml = [12, 11], 13
    elif identifier == 'sp_stack':
        from .stack import GM
        built = GM(p, config.metal_ratio, config.electrode_um, config.substrate_um, layers,
                   [_thickness(item) for item in config.coatings], config.mesh_um)
        tags, pml = built['tag_backing'] + built['tag_coating'], built['tag_pml']
        nb = len(built['tag_backing'])
        mapping = {16: 0, 15: 1, pml: (1 + nb) if nb else 0}
        mapping.update({tag: i+2 for i,tag in enumerate(tags)})
        tc = config.substrate_material == 'linbo3_tc'
        return dict(tag_map=mapping, pml_tag=pml, pml_thickness_m=built['pml_thickness_um']*1e-6,
            period_m=2*p*1e-6, layer_tags=tags, electrode_tag=15, piezo_tag=16,
            boundary_tags=dict(positive=17, negative=18, left=19, right=20, bottom=21),
            coordinate_note='mesh (x,y) = material global (x,z)' if tc else 'mesh (x,y) = material global (x,y)',
            pml_material_role='last_backing' if nb else 'primary_piezo', piezo_top_fraction=None,
            mesh_rows=built['rows'], mesh_cols=built['cols'], mesh_h_near_um=built['h_near'], mesh_h_deep_um=built['h_deep'])
    else:
        raise ValueError('No multilayer mesh builder for ' + identifier)
    mapping = {16: 0, 15: 1, pml: 0}
    mapping.update({tag: i+2 for i,tag in enumerate(tags)})
    tc = identifier == 'sp_tcsaw'
    return dict(tag_map=mapping, pml_tag=pml, pml_thickness_m=(4 if tc else 2)*p*1e-6,
        period_m=2*p*1e-6, layer_tags=tags, electrode_tag=15, piezo_tag=16,
        boundary_tags=dict(positive=17, negative=18, left=19, right=20, bottom=21),
        coordinate_note='mesh (x,y) = material global (x,z)' if tc else 'mesh (x,y) = material global (x,y)',
        pml_material_role='primary_piezo', piezo_top_fraction=.25 if tc else None)
