from abaqus import *
from abaqusConstants import *
import section
import xml.etree.ElementTree as et

from main import utilities_abq as uab
from utils import abq_view as abv

DEFAULT_1D_SET_NAME = 'Set_layup'
DEFAULT_1D_COMPOSITE_LAYUP_NAME = 'CompositeLayup-1'
YZ_WORK_PLANE_TRANSFORM = (0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0)


def get_element_edge_count(element_type):
    """Map the UI element type to Abaqus edge seed count.

    Parameters
    ----------
    element_type : str
        Element family selected in the 1D SG workflow.

    Returns
    -------
    int
        Number of seeds to apply on each ply edge.
    """
    edge_count_map = {
        'five-noded': 4,
        'four-noded': 3,
        'three-noded': 2,
        'two-noded': 1,
    }
    try:
        return edge_count_map[element_type]
    except KeyError:
        raise ValueError('Unknown elem_type: %s' % element_type)


def expand_layup_angles(layup_text):
    """Expand a compact layup string into ply angles.

    Parameters
    ----------
    layup_text : str
        Layup string such as ``[45/-45]2s``.

    Returns
    -------
    list of float
        Expanded ply orientation angles in stacking order.
    """
    mid = layup_text.find(']')
    layup_body = layup_text[:mid].replace('[', ' ').replace('/', ' ').replace('\\', ' ')
    base_angles = layup_body.split()

    repeat_token = layup_text[mid + 1:].strip().lower()
    symmetric = 's' in repeat_token
    if symmetric:
        repeat_token = repeat_token.replace('s', '')

    try:
        repeat_count = int(repeat_token) if repeat_token else 1
    except ValueError:
        repeat_count = 1

    half_layup = [float(angle) for angle in (base_angles * repeat_count)]
    if symmetric:
        return half_layup + list(reversed(half_layup))

    return half_layup


def build_section_layers(material_names, thicknesses, orientation_angles):
    """Build Abaqus section layers from ply properties.

    Parameters
    ----------
    material_names : sequence of str or str
        Material name for each ply. A single string is broadcast to all plies.
    thicknesses : sequence of float or float
        Thickness for each ply. A single float is broadcast to all plies.
    orientation_angles : sequence of float
        Orientation angle for each ply.

    Returns
    -------
    tuple
        Tuple of ``section.SectionLayer`` objects.
    """
    ply_count = len(orientation_angles)

    if isinstance(material_names, str):
        material_names = [material_names] * ply_count
    else:
        material_names = list(material_names)

    if isinstance(thicknesses, (int, float)):
        thicknesses = [float(thicknesses)] * ply_count
    else:
        thicknesses = [float(thickness) for thickness in thicknesses]

    if len(material_names) != ply_count or len(thicknesses) != ply_count:
        raise ValueError('Material, thickness, and orientation lists must have the same length.')

    section_layers = []
    for material_name, thickness, orientation_angle in zip(
        material_names, thicknesses, orientation_angles
    ):
        section_layers.append(
            section.SectionLayer(
                material=material_name,
                thickness=thickness,
                orientAngle=float(orientation_angle),
            )
        )

    return tuple(section_layers)


def get_ply_boundaries(thicknesses):
    """Compute lower and upper coordinates for each ply line.

    Parameters
    ----------
    thicknesses : sequence of float
        Ply thickness values in stacking order.

    Returns
    -------
    tuple of list
        Lower and upper coordinates for each ply measured from the laminate mid-plane.
    """
    thicknesses = [float(thickness) for thickness in thicknesses]
    total_thickness = sum(thicknesses)
    lower_bounds = []
    upper_bounds = []
    position = -total_thickness / 2.0

    for thickness in thicknesses:
        lower_bounds.append(position)
        position += thickness
        upper_bounds.append(position)

    return lower_bounds, upper_bounds


def create_1d_part_geometry(model_name, part_name, thicknesses):
    """Create a 1D laminate part from ply thickness data."""
    model = mdb.models[model_name]
    lower_bounds, upper_bounds = get_ply_boundaries(thicknesses)
    viewport = abv.current_viewport()

    part = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    datum_plane_yz_id = part.DatumPlaneByPrincipalPlane(
        principalPlane=YZPLANE, offset=0.0
    ).id
    datum_axis_z_id = part.DatumAxisByPrincipalAxis(principalAxis=ZAXIS).id

    sketch = model.ConstrainedSketch(
        name='__profile__', sheetSize=200.0, transform=YZ_WORK_PLANE_TRANSFORM
    )
    sketch.setPrimaryObject(option=STANDALONE)
    abv.set_named_view('Left', vp=viewport)

    part.projectReferencesOntoSketch(sketch=sketch, filter=COPLANAR_EDGES)
    for lower_bound, upper_bound in zip(lower_bounds, upper_bounds):
        sketch.Line(point1=(0.0, lower_bound), point2=(0.0, upper_bound))

    datums = part.datums
    part.Wire(
        sketchPlane=datums[datum_plane_yz_id],
        sketchUpEdge=datums[datum_axis_z_id],
        sketchPlaneSide=SIDE1,
        sketchOrientation=RIGHT,
        sketch=sketch,
    )
    sketch.unsetPrimaryObject()
    abv.set_displayed_object(part, vp=viewport)
    del model.sketches['__profile__']

    return part


def mesh_1d_part(part, element_type, set_name=DEFAULT_1D_SET_NAME):
    """Seed, mesh, and store the full edge set for a 1D laminate part."""
    edge_count = get_element_edge_count(element_type)
    part.seedEdgeByNumber(edges=part.edges, number=edge_count, constraint=FINER)
    part.generateMesh()
    part.Set(edges=part.edges, name=set_name)


def apply_1d_composite_layup(
    part,
    material_names,
    thicknesses,
    orientation_angles,
    offset_ratio,
    set_name=DEFAULT_1D_SET_NAME,
    layup_name=DEFAULT_1D_COMPOSITE_LAYUP_NAME,
):
    """Create the Abaqus composite layup for a generated 1D laminate part."""
    material_names = list(material_names)
    thicknesses = [float(thickness) for thickness in thicknesses]
    orientation_angles = [float(angle) for angle in orientation_angles]

    if not (
        len(material_names) == len(thicknesses) == len(orientation_angles)
    ):
        raise ValueError('Material, thickness, and orientation lists must have the same length.')

    region = part.sets[set_name]
    composite_layup = part.CompositeLayup(
        name=layup_name,
        description='',
        elementType=SHELL,
        offsetType=SINGLE_VALUE,
        offsetValues=(offset_ratio,),
        symmetric=False,
        thicknessAssignment=FROM_SECTION,
    )
    composite_layup.Section(
        preIntegrate=OFF,
        integrationRule=SIMPSON,
        thicknessType=UNIFORM,
        poissonDefinition=DEFAULT,
        temperature=GRADIENT,
        useDensity=OFF,
    )
    composite_layup.ReferenceOrientation(
        orientationType=GLOBAL,
        localCsys=None,
        fieldName='',
        additionalRotationType=ROTATION_NONE,
        angle=0.0,
        axis=AXIS_3,
    )

    for ply_index, (material_name, thickness, orientation_angle) in enumerate(
        zip(material_names, thicknesses, orientation_angles), start=1
    ):
        composite_layup.CompositePly(
            suppressed=False,
            plyName='Ply-' + str(ply_index),
            region=region,
            material=material_name,
            thicknessType=SPECIFY_THICKNESS,
            thickness=thickness,
            orientationType=SPECIFY_ORIENT,
            orientationValue=orientation_angle,
            additionalRotationType=ROTATION_NONE,
            additionalRotationField='',
            axis=AXIS_3,
            angle=0.0,
            numIntPoints=3,
        )


def create_1d_part_with_composite_layup(
    model_name,
    part_name,
    material_names,
    thicknesses,
    orientation_angles,
    offset_ratio,
    element_type,
):
    """Create, mesh, and populate a 1D laminate part from ply data."""
    part = create_1d_part_geometry(model_name, part_name, thicknesses)
    mesh_1d_part(part, element_type)
    apply_1d_composite_layup(
        part,
        material_names,
        thicknesses,
        orientation_angles,
        offset_ratio,
    )
    uab.setViewYZ(nsg=1, obj=part)

    return part


def update_1d_part_geometry(model_name, part_name, thicknesses, element_type):
    """Replace the existing 1D wire sketch with ply lines from thickness data."""
    model = mdb.models[model_name]
    part = model.parts[part_name]
    lower_bounds, upper_bounds = get_ply_boundaries(thicknesses)

    wire_key = list(part.features.keys())[-1]
    source_sketch = part.features[wire_key].sketch
    model.ConstrainedSketch(name='__edit__', objectToCopy=source_sketch)
    sketch = model.sketches['__edit__']
    sketch.setPrimaryObject(option=SUPERIMPOSE)
    part.projectReferencesOntoSketch(
        sketch=sketch, upToFeature=part.features[wire_key], filter=COPLANAR_EDGES
    )
    sketch.delete(objectList=tuple(sketch.geometry.values()))

    for lower_bound, upper_bound in zip(lower_bounds, upper_bounds):
        sketch.Line(point1=(0.0, lower_bound), point2=(0.0, upper_bound))

    sketch.unsetPrimaryObject()
    part.features[wire_key].setValues(sketch=sketch)
    del model.sketches['__edit__']
    part.regenerate()

    mesh_1d_part(part, element_type)
    uab.setViewYZ(nsg=1, obj=part)

    return part


def get_section_layup_data(section_layup):
    """Extract material, thickness, and orientation lists from a section layup."""
    material_names = []
    thicknesses = []
    orientation_angles = []

    for layer in section_layup:
        material_names.append(layer.material)
        thicknesses.append(layer.thickness)
        orientation_angles.append(layer.orientAngle)

    return material_names, thicknesses, orientation_angles


def get_active_composite_layup_thicknesses(composite_layup):
    """Extract thicknesses from non-suppressed composite plies."""
    thicknesses = []
    for ply in composite_layup.plies:
        if not ply.suppressed:
            thicknesses.append(ply.thickness)

    return thicknesses


def extract_composite_layup_sc_data(part):
    """Extract SwiftComp layer data from the active composite layup on a part.

    Identifies the single active composite layup, reads all non-suppressed
    plies, and builds the material/layer/ply mapping structures used by the
    SwiftComp input writer.

    Parameters
    ----------
    part : Part
        Abaqus part with exactly one active (non-suppressed) composite layup.

    Returns
    -------
    matDict : dict[str, int]
        Material name to integer id (1-indexed).
    nlayers : dict[int, list]
        Layer id to ``[mat_id, theta]`` after remapping names to ids.
    plies : dict[int, int]
        Ply index (0-indexed) to layer id.
    offset : float
        z-coordinate shift applied to each node: ``-total_thickness * offset_ratio``.

    Raises
    ------
    ValueError
        If the part has no active layup or more than one active layup.
    """
    # Identify the single active layup
    active_names = [
        name for name in part.compositeLayups.keys()
        if not part.compositeLayups[name].suppressed
    ]
    if len(active_names) == 0:
        raise ValueError(
            'part[%s].compositeLayups has no active layup; define exactly 1.'
            % part.name
        )
    if len(active_names) >= 2:
        raise ValueError(
            'part[%s].compositeLayups has more than 1 active layup; delete the extra.'
            % part.name
        )
    layup_abq = part.compositeLayups[active_names[0]]

    # Offset ratio from layup reference surface
    _offset_map = {
        MIDDLE_SURFACE:  0.0,
        BOTTOM_SURFACE: -0.5,
        TOP_SURFACE:     0.5,
    }
    if layup_abq.offsetType in _offset_map:
        offset_ratio = _offset_map[layup_abq.offsetType]
    else:  # SINGLE_VALUE
        offset_ratio = layup_abq.offsetValues[0]

    # Collect active plies
    active_plies = [ply for ply in layup_abq.plies if not ply.suppressed]
    t_total = sum(ply.thickness for ply in active_plies)
    offset = -t_total * offset_ratio

    # Build matDict, nlayers, plies mapping
    matDict = {}
    nlayers = {}
    plies = {}

    for ply_id, ply in enumerate(active_plies):
        mat_name = ply.material
        if ply.orientationType == SPECIFY_ORIENT:
            theta_i = ply.orientationValue
        else:
            theta_i = float(str(ply.orientationType).rsplit('_')[-1])

        if mat_name not in matDict:
            matDict[mat_name] = len(matDict) + 1

        # Find or create matching layer type [mat_name, theta]
        layer_id = next(
            (lid for lid, lv in nlayers.items() if lv == [mat_name, theta_i]),
            None,
        )
        if layer_id is None:
            layer_id = len(nlayers) + 1
            nlayers[layer_id] = [mat_name, theta_i]
        plies[ply_id] = layer_id

    # Remap material names → material ids in nlayers
    for lid in nlayers:
        nlayers[lid] = [matDict[nlayers[lid][0]], nlayers[lid][1]]

    return matDict, nlayers, plies, offset

def readMaterialFile(model_name, file_name):
    
    model = mdb.models[model_name]
    tree = et.parse(file_name)
    mtr_root = tree.getroot()
    
    mid_name = {}
#    mname_id = {}

    for mtr in mtr_root:
        material_id   = int(mtr.find('id').text)
        material_name = mtr.find('name').text
        material_type = mtr.get('type')
        density = mtr.find('density')
        mid_name[material_id] = material_name
#        mname_id[material_name] = material_id
        m = model.Material(name = material_name)
        if not density == None:
            dens = float(density.text)
            m.Density(table = ((dens,),))
        if material_type == 'ISOTROPIC':
            e = float(mtr.find('e').text)
            nu = float(mtr.find('nu').text)
            prop = ((e, nu),)
            m.Elastic(type = ISOTROPIC, table = prop)
#            sn = material_name + '_0.0'
#            model.HomogeneousSolidSection(name = sn, material = material_name, thickness = None)
        elif material_type == 'ENGINEERING CONSTANTS':
            e1 = float(mtr.find('e1').text)
            e2 = float(mtr.find('e2').text)
            e3 = float(mtr.find('e3').text)
            g12 = float(mtr.find('g12').text)
            g13 = float(mtr.find('g13').text)
            g23 = float(mtr.find('g23').text)
            nu12 = float(mtr.find('nu12').text)
            nu13 = float(mtr.find('nu13').text)
            nu23 = float(mtr.find('nu23').text)
            prop = ((e1, e2, e3, nu12, nu13, nu23, g12, g13, g23),)
            m.Elastic(type = ENGINEERING_CONSTANTS, table = prop)
        
    
    return mid_name



def fastGenerate(model_name, material_name, section_name, layup, ply_thickness):
    model = mdb.models[model_name]
    layup_ori = expand_layup_angles(layup)
    section_layer = build_section_layers(material_name, ply_thickness, layup_ori)
    model.CompositeSolidSection(name=section_name, layup=section_layer)
    
    return 1




def readLayupFile(model_name, file_name, mid_name):
    
    model = mdb.models[model_name]
    
    tree_layup = et.parse(file_name)
    root_layup = tree_layup.getroot()
    
    for layup in root_layup:
        lyp_name = layup.find('name').text
        lyp_data = layup.find('data').text
        lyp_data = lyp_data.strip().split('\n')
        material_names = []
        thicknesses = []
        orientation_angles = []
        for l in lyp_data:
            l = l.split()
            [thk, mid, ora] = [float(l[0]), int(l[1]), float(l[2])]
            material_names.append(mid_name[mid])
            thicknesses.append(thk)
            orientation_angles.append(ora)
        section_layer = build_section_layers(
            material_names, thicknesses, orientation_angles
        )
        model.CompositeSolidSection(name=lyp_name, layup=section_layer)

