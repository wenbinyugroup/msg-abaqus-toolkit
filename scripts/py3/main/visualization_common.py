# -*- coding: utf-8 -*-

from __future__ import print_function

from odbAccess import Odb, openOdb
from abaqus import session
from abaqusConstants import *
from utils import abq_view
from main import utilities_abq as uab
import os
import shutil


TENSOR_INVARIANTS = (
    MISES, TRESCA, PRESS, INV3,
    MAX_PRINCIPAL, MID_PRINCIPAL, MIN_PRINCIPAL,
)


def resolve_project_location(input_file):
    """Return the output directory and project stem for one input file.

    Parameters
    ----------
    input_file : str
        Visualization input file path.

    Returns
    -------
    tuple[str, str]
        Project directory and project stem without extension.
    """
    project_path = os.path.dirname(input_file)
    project_name = os.path.basename(input_file).split('.')[0]
    return project_path, project_name


def create_visualization_odb(project_path, project_name, description,
                             overwrite_existing=False):
    """Create an ODB used by one visualization workflow.

    Parameters
    ----------
    project_path : str
        Directory containing the generated ODB file.
    project_name : str
        Base file name used for the ODB.
    description : str
        ODB description shown in Abaqus.
    overwrite_existing : bool, optional
        Whether an existing ODB with the same path should be deleted first.

    Returns
    -------
    tuple[Odb, str, str]
        Created ODB object, ODB session name, and ODB file path.
    """
    print('--> Creating ODB file...')

    odb_name = project_name
    odb_file_name = os.path.join(project_path, project_name + '.odb')

    if overwrite_existing and os.path.exists(odb_file_name):
        print('--! Warning: ODB file already exists and will be overwritten.')
        _close_matching_session_odb(odb_file_name)
        _remove_odb_artifacts(odb_file_name)
        print('--> Existing ODB deleted.')

    odb = Odb(
        name=odb_name,
        analysisTitle=project_name,
        description=description,
        path=odb_file_name,
    )
    return odb, odb_name, odb_file_name


def reopen_visualization_odb(odb_name, odb_file_name):
    """Close the freshly written ODB handle and reopen it for display."""
    try:
        session.odbs[odb_name].close()
    except Exception:
        pass
    return openOdb(odb_file_name)


def configure_visualization_viewports(
    odb, nsg, primary_field='EN', primary_component='EN11',
    secondary_field='SN', secondary_component='SN11',
    primary_restore=True, primary_visible_edges=None,
    secondary_restore=False, secondary_visible_edges=None,
    link_field_output=None, annotate_primary=True
):
    """Configure the standard side-by-side visualization viewports."""
    vp1, vp2 = abq_view.split_viewport_left_right()
    uab.setViewYZ(vp=vp1, nsg=nsg, obj=odb)
    abq_view.configure_odb_contour_display(
        vp=vp1,
        variable_label=primary_field,
        component=primary_component,
        restore=primary_restore,
        visible_edges=primary_visible_edges,
    )
    if annotate_primary:
        abq_view.configure_viewport_annotations(vp=vp1)

    uab.setViewYZ(vp=vp2, nsg=nsg, obj=odb)
    abq_view.configure_odb_contour_display(
        vp=vp2,
        variable_label=secondary_field,
        component=secondary_component,
        restore=secondary_restore,
        visible_edges=secondary_visible_edges,
    )

    abq_view.make_current(vp=vp1)
    abq_view.set_linked_viewports(
        link_viewports=True, field_output=link_field_output
    )
    return vp1, vp2


def create_dummy_material(odb_vis, log_message=None):
    """Create the shared elastic material used for visualization."""
    if log_message:
        print(log_message)

    material_name = 'Elastic material'
    material = odb_vis.Material(name=material_name)
    material.Elastic(
        type=ISOTROPIC,
        temperatureDependency=OFF,
        dependencies=0,
        noCompression=OFF,
        noTension=OFF,
        moduli=LONG_TERM,
        table=((12000, 0.3),),
    )
    return material_name


def create_sections(odb_vis, elem_sectn, material_name, section_name_prefix,
                    section_kind='solid', section_kwargs=None,
                    log_message=None):
    """Create one visualization section per section id."""
    if log_message:
        print(log_message)

    if section_kind == 'solid':
        section_factory = odb_vis.HomogeneousSolidSection
    elif section_kind == 'shell':
        section_factory = odb_vis.HomogeneousShellSection
    else:
        raise ValueError('Unsupported section kind: %s' % section_kind)

    section_kwargs = section_kwargs or {}
    abq_section = {}
    for section_id in list(elem_sectn.keys()):
        section_name = section_name_prefix + '-' + str(section_id)
        kwargs = {'name': section_name, 'material': material_name}
        kwargs.update(section_kwargs)
        abq_section[section_id] = section_factory(**kwargs)

    return abq_section


def create_section_category(odb_vis, name='S5', description='',
                            section_point_number=None,
                            section_point_description=''):
    """Create a section category and an optional section point."""
    section_category = odb_vis.SectionCategory(
        name=name, description=description
    )
    section_point = None
    if section_point_number is not None:
        section_point = section_category.SectionPoint(
            number=section_point_number,
            description=section_point_description,
        )
    return section_category, section_point


def create_part_with_nodes(odb_vis, node_coord, part_name='Part-1',
                           embedded_space=THREE_D, log_message=None,
                           node_log_message=None):
    """Create a deformable part and import nodal coordinates."""
    if log_message:
        print(log_message)

    part = odb_vis.Part(
        name=part_name, embeddedSpace=embedded_space, type=DEFORMABLE_BODY
    )

    if node_log_message:
        print(node_log_message)

    part.addNodes(nodeData=tuple(node_coord), nodeSetName='nSet-1')
    odb_vis.save()
    return part


def add_element_groups(odb_vis, part, element_groups, log_message=None):
    """Import one or more element connectivity groups into an ODB part."""
    if log_message:
        print(log_message)

    for connectivity, element_type, element_set_name, section_category in element_groups:
        if connectivity == []:
            continue

        kwargs = {
            'elementData': tuple(connectivity),
            'type': element_type,
            'elementSetName': element_set_name,
        }
        if section_category is not None:
            kwargs['sectionCategory'] = section_category
        part.addElements(**kwargs)

    odb_vis.save()


def create_instance_and_assign_sections(
    odb_vis, part, elem_sectn, abq_section, section_name_prefix,
    instance_name='Part-1-1', log_message=None
):
    """Create the root-assembly instance and assign element sections."""
    if log_message:
        print(log_message)

    instance = odb_vis.rootAssembly.Instance(name=instance_name, object=part)
    for section_id in list(elem_sectn.keys()):
        section_name = section_name_prefix + ' - ' + str(section_id)
        elem_set = odb_vis.rootAssembly.instances[
            instance_name
        ].ElementSetFromElementLabels(
            name=section_name,
            elementLabels=tuple(elem_sectn[section_id]),
        )
        instance.assignSection(region=elem_set, section=abq_section[section_id])

    odb_vis.save()
    return instance


def create_step_and_frame(odb_vis, log_message=None):
    """Create the single visualization step and frame."""
    if log_message:
        print(log_message)

    step = odb_vis.Step(
        name='Step-1', description='', domain=TIME, timePeriod=1.0
    )
    frame = step.Frame(incrementNumber=1, frameValue=0.1, description='')
    return step, frame


def add_displacement_field(odb_vis, frame, step, instance, node_label, u_data,
                           log_message=None):
    """Import the nodal displacement field when present."""
    if u_data == []:
        return

    if log_message:
        print(log_message)

    u_field = frame.FieldOutput(
        name='U',
        description='Displacements.',
        type=VECTOR,
        validInvariants=(MAGNITUDE,),
    )
    u_field.addData(
        position=NODAL,
        instance=instance,
        labels=tuple(node_label),
        data=tuple(u_data),
    )
    step.setDefaultDeformedField(u_field)
    odb_vis.save()


def tensor_component_labels(field_name):
    """Build default Abaqus tensor component labels for one field name."""
    shear_prefix = '2' if field_name.startswith('E') else ''
    return (
        field_name + '11',
        field_name + '22',
        field_name + '33',
        shear_prefix + field_name + '23',
        shear_prefix + field_name + '13',
        shear_prefix + field_name + '12',
    )


def add_tensor_field(odb_vis, frame, instance, labels, data, field_name,
                     description, position, section_point=None,
                     component_labels=None, valid_invariants=None,
                     log_message=None):
    """Import one tensor field output when data is available."""
    if data == []:
        return

    if log_message:
        print(log_message)

    if component_labels is None:
        component_labels = tensor_component_labels(field_name)
    if valid_invariants is None:
        valid_invariants = TENSOR_INVARIANTS

    field = frame.FieldOutput(
        name=field_name,
        description=description,
        type=TENSOR_3D_FULL,
        componentLabels=component_labels,
        validInvariants=valid_invariants,
    )

    add_data_kwargs = {
        'position': position,
        'instance': instance,
        'labels': tuple(labels),
        'data': tuple(data),
    }
    if section_point is not None:
        add_data_kwargs['sectionPoint'] = section_point
    field.addData(**add_data_kwargs)
    odb_vis.save()


def add_tensor_fields(odb_vis, frame, instance, labels, field_specs):
    """Import multiple tensor fields described by a small config list."""
    for field_spec in field_specs:
        add_tensor_field(
            odb_vis=odb_vis,
            frame=frame,
            instance=instance,
            labels=field_spec.get('labels', labels),
            data=field_spec['data'],
            field_name=field_spec['name'],
            description=field_spec['description'],
            position=field_spec['position'],
            section_point=field_spec.get('section_point'),
            component_labels=field_spec.get('component_labels'),
            valid_invariants=field_spec.get('valid_invariants'),
            log_message=field_spec.get('log_message'),
        )


def _close_matching_session_odb(odb_file_name):
    """Close any session ODB already opened from the same file path."""
    for existing_name in list(session.odbs.keys()):
        try:
            existing_odb = session.odbs[existing_name]
            if getattr(existing_odb, 'path', None) == odb_file_name:
                existing_odb.close()
        except Exception:
            pass

    try:
        odb = openOdb(odb_file_name)
        odb.close()
    except Exception:
        pass


def _remove_odb_artifacts(odb_file_name):
    """Delete an ODB file and its auxiliary directory."""
    try:
        os.remove(odb_file_name)
    except OSError as exc:
        raise RuntimeError(
            'Failed to delete existing ODB: %s' % exc
        )

    aux_dir = odb_file_name + '_f'
    if os.path.isdir(aux_dir):
        shutil.rmtree(aux_dir)
