# -*- coding: utf-8 -*-

from __future__ import print_function

"""Spherical 3D Structure Genome generation for Abaqus."""

try:
    from ._runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config
    from .helpers import DEFAULT_BLOCK_SIZE, calculate_spherical_geometry
except ImportError:
    from _runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config
    from helpers import DEFAULT_BLOCK_SIZE, calculate_spherical_geometry

ensure_py3_on_path()

from abaqus import *
from abaqusConstants import *
from caeModules import *
from utils import abq_view


BLOCK_SIZE = DEFAULT_BLOCK_SIZE
PROFILE_SKETCH_NAME = '__profile__'
PART_NAMES = {
    'matrix': 'matrix',
    'fiber': 'inclusion',
    'interface': 'interface',
    'merged': 'inclusionP3',
}
SECTION_NAMES = {
    'matrix': 'Matrix_section',
    'fiber': 'Inclusion_section',
    'interface': 'Interphase_section',
}
ELEMENT_TYPES = {
    'Linear': (C3D8, C3D4),
    'Quadratic': (C3D20, C3D10),
}


def _set_displayed_object_if_possible(displayed_object):
    """Update the current viewport when available."""
    abq_view.set_displayed_object(displayed_object)


def _configure_part_display(sectionAssignments=None, engineeringFeatures=None,
                            mesh=None, referenceRepresentation=None,
                            meshTechnique=None):
    """Apply part-display settings only when a viewport exists."""
    abq_view.configure_part_display(
        sectionAssignments=sectionAssignments,
        engineeringFeatures=engineeringFeatures,
        mesh=mesh,
        referenceRepresentation=referenceRepresentation,
        meshTechnique=meshTechnique,
    )


def _configure_assembly_display(mesh=None, optimizationTasks=None,
                                geometricRestrictions=None,
                                stopConditions=None, meshTechnique=None):
    """Apply assembly-display settings only when a viewport exists."""
    abq_view.configure_assembly_display(
        mesh=mesh,
        optimizationTasks=optimizationTasks,
        geometricRestrictions=geometricRestrictions,
        stopConditions=stopConditions,
        meshTechnique=meshTechnique,
    )


def _validate_part_and_section_names(model):
    """Fail early when the generated names already exist.

    Parameters
    ----------
    model : Model
        Abaqus model object.

    Raises
    ------
    ValueError
        Raised when a generated part or section name already exists.
    """
    existing_parts = []
    for part_name in PART_NAMES.values():
        if part_name in model.parts.keys():
            existing_parts.append(part_name)

    existing_sections = []
    for section_name in SECTION_NAMES.values():
        if section_name in model.sections.keys():
            existing_sections.append(section_name)

    if existing_parts:
        raise ValueError(
            'Target part names already exist in model "%s": %s'
            % (model.name, ', '.join(existing_parts))
        )
    if existing_sections:
        raise ValueError(
            'Target section names already exist in model "%s": %s'
            % (model.name, ', '.join(existing_sections))
        )


def _resolve_element_codes(elem_type):
    """Return the Abaqus solid element codes for the requested family.

    Parameters
    ----------
    elem_type : str
        Element family label.

    Returns
    -------
    tuple
        Tuple of primary and fallback element codes.

    Raises
    ------
    ValueError
        Raised when ``elem_type`` is unknown.
    """
    try:
        return ELEMENT_TYPES[elem_type]
    except KeyError:
        raise ValueError(
            'Unsupported element type "%s". Expected one of: %s.'
            % (elem_type, ', '.join(sorted(ELEMENT_TYPES.keys())))
        )


def _log_geometry(block_size, fiber_radius, vof_fiber, interface_radius=None,
                  vof_interface=0.0):
    """Print the derived geometry parameters for Abaqus command logs."""
    print('blockSize: %s' % block_size)
    print('totalVolume: %s' % (block_size ** 3))
    print('#---fiber------------------------')
    print('vof_inclusion: %s' % vof_fiber)
    print('Inclusion Radius: %s' % fiber_radius)

    if interface_radius is not None:
        print('#---interphase-------------------------')
        print('vof_interphace: %s' % vof_interface)
        print('interphase Radius: %s' % interface_radius)


def _create_box_part(model, part_name, block_size):
    """Create the matrix cube part."""
    sketch_object = model.ConstrainedSketch(
        name=PROFILE_SKETCH_NAME,
        sheetSize=200.0,
    )
    sketch_object.setPrimaryObject(option=STANDALONE)

    try:
        sketch_object.rectangle(
            point1=(-0.5 * block_size, -0.5 * block_size),
            point2=(0.5 * block_size, 0.5 * block_size),
        )
        part = model.Part(
            name=part_name,
            dimensionality=THREE_D,
            type=DEFORMABLE_BODY,
        )
        part.BaseSolidExtrude(sketch=sketch_object, depth=block_size)
    finally:
        sketch_object.unsetPrimaryObject()
        del model.sketches[PROFILE_SKETCH_NAME]

    _set_displayed_object_if_possible(part)
    return part


def _create_sphere_part(model, part_name, radius):
    """Create a spherical solid by revolving a semicircle."""
    sketch_object = model.ConstrainedSketch(
        name=PROFILE_SKETCH_NAME,
        sheetSize=20.0,
    )
    geometry = sketch_object.geometry
    vertices = sketch_object.vertices
    sketch_object.setPrimaryObject(option=STANDALONE)

    try:
        sketch_object.ConstructionLine(point1=(0.0, -10.0), point2=(0.0, 10.0))
        sketch_object.FixedConstraint(entity=geometry[2])
        sketch_object.Line(point1=(0.0, -radius), point2=(0.0, radius))
        sketch_object.VerticalConstraint(entity=geometry[3], addUndoState=False)
        sketch_object.ArcByCenterEnds(
            center=(0.0, 0.0),
            point1=(0.0, radius),
            point2=(0.0, -radius),
            direction=CLOCKWISE,
        )
        sketch_object.CoincidentConstraint(
            entity1=vertices[2],
            entity2=geometry[3],
            addUndoState=False,
        )
        sketch_object.EqualDistanceConstraint(
            entity1=vertices[0],
            entity2=vertices[1],
            midpoint=vertices[2],
            addUndoState=False,
        )
        part = model.Part(
            name=part_name,
            dimensionality=THREE_D,
            type=DEFORMABLE_BODY,
        )
        part.BaseSolidRevolve(
            sketch=sketch_object,
            angle=360.0,
            flipRevolveDirection=OFF,
        )
    finally:
        sketch_object.unsetPrimaryObject()
        del model.sketches[PROFILE_SKETCH_NAME]

    _set_displayed_object_if_possible(part)
    _configure_part_display(
        sectionAssignments=ON,
        engineeringFeatures=ON,
        referenceRepresentation=OFF,
    )
    return part


def _create_section(model, section_name, material_name):
    """Create a homogeneous solid section."""
    model.HomogeneousSolidSection(
        name=section_name,
        material=material_name,
        thickness=None,
    )


def _build_source_parts(model, fiber_radius, interface_radius, fiber_matname,
                        matrix_matname, interface_matname):
    """Create the temporary geometry parts and sections."""
    _create_box_part(model, PART_NAMES['matrix'], BLOCK_SIZE)
    _create_section(model, SECTION_NAMES['matrix'], matrix_matname)

    _create_sphere_part(model, PART_NAMES['fiber'], fiber_radius)
    _create_section(model, SECTION_NAMES['fiber'], fiber_matname)

    part_names = [PART_NAMES['matrix'], PART_NAMES['fiber']]
    if interface_radius is not None:
        _create_sphere_part(model, PART_NAMES['interface'], interface_radius)
        _create_section(model, SECTION_NAMES['interface'], interface_matname)
        part_names.append(PART_NAMES['interface'])

    return part_names


def _merge_source_parts(model, part_names, block_size):
    """Merge the cube, fiber, and optional interface into one SG part."""
    assembly = model.rootAssembly
    _set_displayed_object_if_possible(assembly)
    _configure_assembly_display(
        optimizationTasks=OFF,
        geometricRestrictions=OFF,
        stopConditions=OFF,
    )
    assembly.DatumCsysByDefault(CARTESIAN)

    for part_name in part_names:
        assembly.Instance(
            name=part_name + '-1',
            part=model.parts[part_name],
            dependent=ON,
        )

    assembly.translate(
        instanceList=(PART_NAMES['matrix'] + '-1',),
        vector=(0.0, 0.0, -0.5 * block_size),
    )

    instance_names = tuple(part_name + '-1' for part_name in part_names)
    assembly.InstanceFromBooleanMerge(
        name=PART_NAMES['merged'],
        instances=tuple(assembly.instances[name] for name in instance_names),
        keepIntersections=ON,
        originalInstances=SUPPRESS,
        domain=GEOMETRY,
    )

    for part_name in part_names:
        del assembly.features[part_name + '-1']
        del model.parts[part_name]

    return model.parts[PART_NAMES['merged']]


def _assign_section_to_cell(part, point, set_name, section_name):
    """Assign a section to a single cell found from an interior point."""
    cells = part.cells.findAt((point,))
    region = part.Set(cells=cells, name=set_name)
    part.SectionAssignment(
        region=region,
        sectionName=section_name,
        offset=0.0,
        offsetType=MIDDLE_SURFACE,
        offsetField='',
        thicknessAssignment=FROM_SECTION,
    )


def _assign_sections(part, fiber_radius, interface_radius, block_size):
    """Assign matrix, inclusion, and optional interphase sections."""
    session.journalOptions.setValues(
        replayGeometry=COORDINATE,
        recoverGeometry=COORDINATE,
    )

    outer_radius = fiber_radius
    if interface_radius is not None:
        outer_radius = interface_radius

    matrix_probe = ((outer_radius + block_size / 2.0) / 2.0, 0.0, 0.0)
    _assign_section_to_cell(
        part,
        matrix_probe,
        SECTION_NAMES['matrix'],
        SECTION_NAMES['matrix'],
    )
    _assign_section_to_cell(
        part,
        (0.0, 0.0, 0.0),
        SECTION_NAMES['fiber'],
        SECTION_NAMES['fiber'],
    )

    if interface_radius is not None:
        interface_probe = ((fiber_radius + interface_radius) / 2.0, 0.0, 0.0)
        _assign_section_to_cell(
            part,
            interface_probe,
            SECTION_NAMES['interface'],
            SECTION_NAMES['interface'],
        )


def _mesh_part(part, mesh_size, element_codes):
    """Mesh the merged SG part."""
    if mesh_size <= 0.0:
        raise ValueError('Mesh size must be positive.')

    part.setMeshControls(regions=part.cells, elemShape=TET, technique=FREE)
    elem_types = tuple(mesh.ElemType(elemCode=code) for code in element_codes)
    part.setElementType(regions=(part.cells,), elemTypes=elem_types)
    part.seedPart(size=mesh_size, deviationFactor=0.1, minSizeFactor=0.1)
    part.generateMesh()


def _finalize_display(model, part):
    """Show the meshed SG part and hide the temporary assembly feature."""
    assembly = model.rootAssembly
    del assembly.features[PART_NAMES['merged'] + '-1']

    _configure_assembly_display(mesh=ON, meshTechnique=ON)
    _set_displayed_object_if_possible(part)
    _configure_part_display(
        sectionAssignments=OFF,
        engineeringFeatures=OFF,
        mesh=ON,
        meshTechnique=ON,
    )


def create3DsphericV5(model_name, fiber_flag, vf_f, interface_flag,
                      t_interface, fiber_matname, matrix_matname,
                      interface_matname, mesh_size, elem_type):
    """Create a spherical 3D Structure Genome part.

    Parameters
    ----------
    model_name : str
        Abaqus model name.
    fiber_flag : int
        Fiber input mode selector. ``1`` means volume fraction, ``2`` means
        radius.
    vf_f : float
        Inclusion volume fraction or radius, depending on ``fiber_flag``.
    interface_flag : int
        Interface input mode selector. ``1`` means volume fraction, ``2`` means
        thickness.
    t_interface : float
        Interface volume fraction or thickness, depending on
        ``interface_flag``.
    fiber_matname : str
        Inclusion material name.
    matrix_matname : str
        Matrix material name.
    interface_matname : str
        Interphase material name.
    mesh_size : float
        Target mesh seed size.
    elem_type : str
        Element family label.

    Returns
    -------
    Part
        Abaqus part containing the merged and meshed SG geometry.
    """
    model = mdb.models[model_name]
    _validate_part_and_section_names(model)

    element_codes = _resolve_element_codes(elem_type)
    geometry = calculate_spherical_geometry(
        fiber_flag,
        vf_f,
        interface_flag,
        t_interface,
        BLOCK_SIZE,
    )
    fiber_radius = geometry['fiber_radius']
    vof_fiber = geometry['fiber_volume_fraction']
    interface_radius = geometry['interface_radius']
    vof_interface = geometry['interface_volume_fraction']

    print('#-------part_name  %s---------------------------' % PART_NAMES['merged'])
    _log_geometry(
        BLOCK_SIZE,
        fiber_radius,
        vof_fiber,
        interface_radius=interface_radius,
        vof_interface=vof_interface,
    )

    part_names = _build_source_parts(
        model,
        fiber_radius,
        interface_radius,
        fiber_matname,
        matrix_matname,
        interface_matname,
    )
    part = _merge_source_parts(model, part_names, BLOCK_SIZE)
    _assign_sections(part, fiber_radius, interface_radius, BLOCK_SIZE)
    _mesh_part(part, mesh_size, element_codes)
    _finalize_display(model, part)
    return part


DEFAULT_CONFIG = {
    'model_name': 'Model-1',
    'fiber_flag': 1,
    'vf_f': 0.2,
    'interface_flag': 2,
    't_interface': 0.02,
    'fiber_matname': 'Fiber',
    'matrix_matname': 'Matrix',
    'interface_matname': 'Interface',
    'mesh_size': 0.1,
    'elem_type': 'Linear',
}


def main(config=None):
    """Build a spherical 3D SG outside the GUI.

    Parameters
    ----------
    config : dict, optional
        Command-line configuration dictionary.

    Returns
    -------
    Part
        Abaqus part containing the merged and meshed SG geometry.
    """
    if config is None:
        config = load_cli_config(DEFAULT_CONFIG)

    material_names = [
        config['fiber_matname'],
        config['matrix_matname'],
    ]
    if config['t_interface'] > 0.0:
        material_names.append(config['interface_matname'])

    ensure_materials_exist(
        mdb,
        config['model_name'],
        material_names,
    )
    return create3DsphericV5(
        config['model_name'],
        config['fiber_flag'],
        config['vf_f'],
        config['interface_flag'],
        config['t_interface'],
        config['fiber_matname'],
        config['matrix_matname'],
        config['interface_matname'],
        config['mesh_size'],
        config['elem_type'],
    )


if __name__ == '__main__':
    main()
