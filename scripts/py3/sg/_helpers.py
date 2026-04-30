# -*- coding: utf-8 -*-

"""Shared Abaqus-side helpers for SG builders."""

from __future__ import print_function

from abaqus import *
from abaqusConstants import *
from caeModules import *
import regionToolset

from utils import abq_view


PROFILE_SKETCH_NAME = '__profile__'
YZ_WORK_PLANE_TRANSFORM = (0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0)
SQUARE_ELEMENT_TYPES = {
    'Linear': (S4, S3),
    'Quadratic': (S8R, STRI65),
}


def set_square_view_yz_if_possible(part):
    """Set the standard SG YZ view when a viewport exists."""
    abq_view.set_sg_view(nsg=2, obj=part, clr='Material')


def build_square_part_names(base_name):
    """Return the temporary and final part names for a square SG."""
    return {
        'quarter': base_name + 'quater',
        'half': base_name + 'quaterhalf',
        'full': base_name,
    }


def set_sg2d_view_yz_if_possible(part):
    """Set the standard SG YZ view when a viewport exists."""
    set_square_view_yz_if_possible(part)


def build_reflected_part_names(base_name):
    """Return the temporary and final part names for a reflected 2D SG."""
    return build_square_part_names(base_name)


def validate_generated_names(model, part_names, section_names):
    """Fail early when generated part or section names already exist."""
    existing_parts = []
    for part_name in part_names.values():
        if part_name in model.parts.keys():
            existing_parts.append(part_name)

    existing_sections = []
    for section_name in section_names.values():
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


def resolve_square_element_codes(elem_type):
    """Return Abaqus shell element codes for the requested family."""
    try:
        return SQUARE_ELEMENT_TYPES[elem_type]
    except KeyError:
        raise ValueError(
            'Unknown elem_type: %s. Expected one of: %s'
            % (elem_type, ', '.join(sorted(SQUARE_ELEMENT_TYPES.keys())))
        )


def log_square_geometry(block_size, fiber_radius, fiber_area_fraction,
                        interface_radius=None, interface_area_fraction=0.0):
    """Print derived square-cell geometry for the Abaqus command log."""
    print('blockSize: %s' % block_size)
    print('#---fiber------------------------')
    print('vof_fiber: %s' % fiber_area_fraction)
    print('fiberRadius: %s' % fiber_radius)

    if interface_radius is not None:
        print('#---interphase-------------------------')
        print('vof_interface: %s' % interface_area_fraction)
        print('interfaceRadius: %s' % interface_radius)


def create_quarter_shell_part(model, part_name, quarter_size):
    """Create the quarter square shell part on the YZ plane."""
    part = model.Part(
        name=part_name,
        dimensionality=THREE_D,
        type=DEFORMABLE_BODY,
    )
    datum_plane_yz_id = part.DatumPlaneByPrincipalPlane(
        principalPlane=YZPLANE,
        offset=0.0,
    ).id
    datum_axis_z_id = part.DatumAxisByPrincipalAxis(principalAxis=ZAXIS).id

    sketch_object = model.ConstrainedSketch(
        name=PROFILE_SKETCH_NAME,
        sheetSize=200.0,
        transform=YZ_WORK_PLANE_TRANSFORM,
    )
    sketch_object.setPrimaryObject(option=STANDALONE)

    try:
        part.projectReferencesOntoSketch(
            sketch=sketch_object,
            filter=COPLANAR_EDGES,
        )
        sketch_object.rectangle(
            point1=(0.0, 0.0),
            point2=(quarter_size, quarter_size),
        )
        part.Shell(
            sketchPlane=part.datums[datum_plane_yz_id],
            sketchUpEdge=part.datums[datum_axis_z_id],
            sketchPlaneSide=SIDE1,
            sketchOrientation=RIGHT,
            sketch=sketch_object,
        )
    finally:
        sketch_object.unsetPrimaryObject()
        del model.sketches[PROFILE_SKETCH_NAME]

    return part


def create_rectangular_shell_part(model, part_name, width, height):
    """Create a rectangular shell part on the YZ plane."""
    part = model.Part(
        name=part_name,
        dimensionality=THREE_D,
        type=DEFORMABLE_BODY,
    )
    datum_plane_yz_id = part.DatumPlaneByPrincipalPlane(
        principalPlane=YZPLANE,
        offset=0.0,
    ).id
    datum_axis_z_id = part.DatumAxisByPrincipalAxis(principalAxis=ZAXIS).id

    sketch_object = model.ConstrainedSketch(
        name=PROFILE_SKETCH_NAME,
        sheetSize=200.0,
        transform=YZ_WORK_PLANE_TRANSFORM,
    )
    sketch_object.setPrimaryObject(option=STANDALONE)

    try:
        part.projectReferencesOntoSketch(
            sketch=sketch_object,
            filter=COPLANAR_EDGES,
        )
        sketch_object.rectangle(
            point1=(0.0, 0.0),
            point2=(width, height),
        )
        part.Shell(
            sketchPlane=part.datums[datum_plane_yz_id],
            sketchUpEdge=part.datums[datum_axis_z_id],
            sketchPlaneSide=SIDE1,
            sketchOrientation=RIGHT,
            sketch=sketch_object,
        )
    finally:
        sketch_object.unsetPrimaryObject()
        del model.sketches[PROFILE_SKETCH_NAME]

    return part


def partition_circular_faces(part, model, radii):
    """Partition the quarter shell with one or more concentric circles."""
    transform = part.MakeSketchTransform(
        sketchPlane=part.faces[0],
        sketchUpEdge=part.edges[1],
        sketchPlaneSide=SIDE1,
        origin=(0.0, 0.0, 0.0),
    )
    sketch_object = model.ConstrainedSketch(
        name=PROFILE_SKETCH_NAME,
        sheetSize=2.0,
        gridSpacing=0.02,
        transform=transform,
    )
    sketch_object.setPrimaryObject(option=SUPERIMPOSE)

    try:
        part.projectReferencesOntoSketch(
            sketch=sketch_object,
            filter=COPLANAR_EDGES,
        )
        for radius in radii:
            sketch_object.CircleByCenterPerimeter(
                center=(0.0, 0.0),
                point1=(0.0, radius),
            )
        part.PartitionFaceBySketch(
            sketchUpEdge=part.edges[1],
            faces=part.faces,
            sketch=sketch_object,
        )
    finally:
        sketch_object.unsetPrimaryObject()
        del model.sketches[PROFILE_SKETCH_NAME]


def partition_hex_corner_arcs(part, model, width, height, radius):
    """Partition the rectangular hex quarter with corner arcs."""
    transform = part.MakeSketchTransform(
        sketchPlane=part.faces[0],
        sketchUpEdge=part.edges[1],
        sketchPlaneSide=SIDE1,
        origin=(0.0, 0.0, 0.0),
    )
    sketch_object = model.ConstrainedSketch(
        name=PROFILE_SKETCH_NAME,
        sheetSize=width * 4.0,
        gridSpacing=0.1 * max(width, height),
        transform=transform,
    )
    sketch_object.setPrimaryObject(option=SUPERIMPOSE)

    try:
        part.projectReferencesOntoSketch(
            sketch=sketch_object,
            filter=COPLANAR_EDGES,
        )
        geometry = sketch_object.geometry
        vertices = sketch_object.vertices
        sketch_object.ArcByCenterEnds(
            center=(0.0, 0.0),
            point1=(0.0, radius),
            point2=(radius, 0.0),
            direction=CLOCKWISE,
        )
        sketch_object.CoincidentConstraint(
            entity1=vertices[4],
            entity2=geometry[5],
            addUndoState=False,
        )
        sketch_object.CoincidentConstraint(
            entity1=vertices[5],
            entity2=geometry[2],
            addUndoState=False,
        )
        sketch_object.ArcByCenterEnds(
            center=(width, height),
            point1=(width - radius, height),
            point2=(width, height - radius),
            direction=COUNTERCLOCKWISE,
        )
        sketch_object.CoincidentConstraint(
            entity1=vertices[6],
            entity2=geometry[4],
            addUndoState=False,
        )
        sketch_object.CoincidentConstraint(
            entity1=vertices[7],
            entity2=geometry[3],
            addUndoState=False,
        )
        part.PartitionFaceBySketch(
            sketchUpEdge=part.edges[1],
            faces=part.faces.getSequenceFromMask(mask=('[#1 ]',),),
            sketch=sketch_object,
        )
    finally:
        sketch_object.unsetPrimaryObject()
        del model.sketches[PROFILE_SKETCH_NAME]


def partition_hex_corner_circles(part, model, width, height, radii):
    """Partition the rectangular hex quarter with corner circles."""
    transform = part.MakeSketchTransform(
        sketchPlane=part.faces[0],
        sketchUpEdge=part.edges[1],
        sketchPlaneSide=SIDE1,
        origin=(0.0, 0.0, 0.0),
    )
    sketch_object = model.ConstrainedSketch(
        name=PROFILE_SKETCH_NAME,
        sheetSize=2.0,
        gridSpacing=0.04,
        transform=transform,
    )
    sketch_object.setPrimaryObject(option=SUPERIMPOSE)

    try:
        part.projectReferencesOntoSketch(
            sketch=sketch_object,
            filter=COPLANAR_EDGES,
        )
        geometry = sketch_object.geometry
        vertices = sketch_object.vertices

        for radius in radii:
            sketch_object.CircleByCenterPerimeter(
                center=(0.0, 0.0),
                point1=(0.0, radius),
            )
        sketch_object.CoincidentConstraint(
            entity1=vertices[4],
            entity2=geometry[5],
            addUndoState=False,
        )
        sketch_object.CoincidentConstraint(
            entity1=vertices[5],
            entity2=geometry[5],
            addUndoState=False,
        )

        for radius in radii:
            sketch_object.CircleByCenterPerimeter(
                center=(width, height),
                point1=(width, height - radius),
            )
        sketch_object.CoincidentConstraint(
            entity1=vertices[6],
            entity2=geometry[3],
            addUndoState=False,
        )
        sketch_object.CoincidentConstraint(
            entity1=vertices[7],
            entity2=geometry[3],
            addUndoState=False,
        )

        part.PartitionFaceBySketch(
            sketchUpEdge=part.edges[1],
            faces=part.faces.getSequenceFromMask(mask=('[#1 ]',),),
            sketch=sketch_object,
        )
    finally:
        sketch_object.unsetPrimaryObject()
        del model.sketches[PROFILE_SKETCH_NAME]


def create_shell_section(model, section_name, material_name, thickness):
    """Create a shell section with the standard SG defaults."""
    model.HomogeneousShellSection(
        name=section_name,
        preIntegrate=OFF,
        material=material_name,
        thicknessType=UNIFORM,
        thickness=thickness,
        thicknessField='',
        idealization=NO_IDEALIZATION,
        poissonDefinition=DEFAULT,
        thicknessModulus=None,
        temperature=GRADIENT,
        useDensity=OFF,
        integrationRule=SIMPSON,
        numIntPts=5,
    )


def assign_section(part, set_name, section_name, mask):
    """Assign a section to faces selected by a known Abaqus mask."""
    faces = part.faces.getSequenceFromMask(mask=(mask,),)
    region = part.Set(faces=faces, name=set_name)
    part.SectionAssignment(
        region=region,
        sectionName=section_name,
        offset=0.0,
        offsetType=MIDDLE_SURFACE,
        offsetField='',
        thicknessAssignment=FROM_SECTION,
    )


def assign_material_orientation(part, set_name):
    """Assign the standard global material orientation to a face set."""
    part.MaterialOrientation(
        region=part.sets[set_name],
        orientationType=GLOBAL,
        axis=AXIS_1,
        additionalRotationType=ROTATION_NONE,
        localCsys=None,
        fieldName='',
    )


def assign_section_by_points(part, set_name, section_name, points):
    """Assign a section to faces identified by interior probe points."""
    faces = part.faces.findAt(*tuple((point,) for point in points))
    region = part.Set(faces=faces, name=set_name)
    part.SectionAssignment(
        region=region,
        sectionName=section_name,
        offset=0.0,
        offsetType=MIDDLE_SURFACE,
        offsetField='',
        thicknessAssignment=FROM_SECTION,
    )


def mesh_quarter_part(part, mesh_size, element_codes, face_mask):
    """Mesh the quarter shell part."""
    if mesh_size <= 0.0:
        raise ValueError('Mesh size must be positive.')

    part.seedPart(size=mesh_size, deviationFactor=0.1, minSizeFactor=0.1)
    faces = part.faces.getSequenceFromMask(mask=(face_mask,),)
    part.setMeshControls(regions=faces, elemShape=QUAD, algorithm=MEDIAL_AXIS)
    elem_types = tuple(
        mesh.ElemType(elemCode=element_code, elemLibrary=STANDARD)
        for element_code in element_codes
    )
    part.setElementType(regions=(faces,), elemTypes=elem_types)
    part.generateMesh()


def mirror_quarter_to_full(model, part_names, mesh_size):
    """Mirror the meshed quarter shell twice and merge the full part."""
    assembly = model.rootAssembly
    quarter_name = part_names['quarter']
    half_name = part_names['half']
    full_name = part_names['full']
    part = model.parts[quarter_name]

    assembly.Instance(name=quarter_name + '-1', part=part, dependent=ON)
    assembly.Instance(name=quarter_name + '-2', part=part, dependent=ON)
    assembly.rotate(
        instanceList=(quarter_name + '-2',),
        axisPoint=(0.0, 0.0, 0.0),
        axisDirection=(0.0, 10.0, 0.0),
        angle=180.0,
    )
    assembly.InstanceFromBooleanMerge(
        name=half_name,
        instances=(
            assembly.instances[quarter_name + '-1'],
            assembly.instances[quarter_name + '-2'],
        ),
        mergeNodes=BOUNDARY_ONLY,
        nodeMergingTolerance=0.0001 * mesh_size,
        domain=MESH,
        originalInstances=DELETE,
    )

    half_part = model.parts[half_name]
    assembly.Instance(name=half_name + '-2', part=half_part, dependent=ON)
    assembly.rotate(
        instanceList=(half_name + '-2',),
        axisPoint=(0.0, 0.0, 0.0),
        axisDirection=(10.0, 0.0, 0.0),
        angle=180.0,
    )
    assembly.InstanceFromBooleanMerge(
        name=full_name,
        instances=(
            assembly.instances[half_name + '-1'],
            assembly.instances[half_name + '-2'],
        ),
        mergeNodes=BOUNDARY_ONLY,
        nodeMergingTolerance=0.0001 * mesh_size,
        domain=MESH,
        originalInstances=DELETE,
    )

    return model.parts[full_name]


def flip_shell_normal(part):
    """Ensure the final merged shell has consistent element normals."""
    elements = part.elements
    regions = regionToolset.Region(elements=elements)
    part.flipNormal(referenceRegion=elements[1], regions=regions)


def cleanup_temporary_parts(model, part_names):
    """Remove temporary quarter and half parts plus the assembly instance."""
    del model.parts[part_names['half']]
    del model.parts[part_names['quarter']]
    del model.rootAssembly.features[part_names['full'] + '-1']
