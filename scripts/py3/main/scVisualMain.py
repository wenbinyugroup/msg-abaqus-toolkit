# -*- coding: utf-8 -*-

from __future__ import print_function
from odbAccess import *
from odbMaterial import *
from odbSection import *
from abaqus import *
from abaqusConstants import *
#from scVisual2D import *
#from scVisual3D import *
#from scVisual1D import *
from utils.utilities import *
from main import utilities_abq as uab
from textRepr import *
from utils import abq_view
from utils.UcheckDehoVisual import *
from sgdataio import swiftcomp as scio
import os.path
import os, shutil
import sys


TENSOR_INVARIANTS = (
    MISES, TRESCA, PRESS, INV3,
    MAX_PRINCIPAL, MID_PRINCIPAL, MIN_PRINCIPAL,
)


def _get_skip_lines(macro_model_dimension, ap_flag):
    """Return header lines skipped in a SwiftComp input file.

    Parameters
    ----------
    macro_model_dimension : str
        Macro model dimension label such as ``'1D'`` or ``'2D'``.
    ap_flag : bool
        Flag indicating whether the aperiodic header is present.

    Returns
    -------
    list[int]
        Line numbers skipped before SG metadata is read.
    """
    skip_line_map = {
        False: {'1D': [1, 2, 3, 4], '2D': [1, 2, 3], '3D': [1]},
        True: {'1D': [1, 2, 3, 4, 5], '2D': [1, 2, 3, 4], '3D': [1, 2]},
    }
    return skip_line_map[ap_flag][macro_model_dimension]


def _iter_non_empty_tokens(filename):
    """Yield tokenized non-empty lines from a text file.

    Parameters
    ----------
    filename : str
        Path to the source file.

    Yields
    ------
    list[str]
        Tokens parsed from one non-empty line.
    """
    with open(filename, 'r') as fin:
        for line in fin:
            line = line.strip()
            if line == '\n' or line == '':
                continue
            yield line.split()


def _read_displacement_results(filename):
    """Read nodal displacement output from a ``.u`` file.

    Parameters
    ----------
    filename : str
        Path to the displacement result file.

    Returns
    -------
    tuple[list[int], list[tuple[float, float, float]]]
        Node labels and displacement vectors.
    """
    node_label = []
    u_data = []

    try:
        for line in _iter_non_empty_tokens(filename):
            node_label.append(int(line[0]))
            u_data.append((float(line[1]), float(line[2]), float(line[3])))
        print('--> Find .u file.')
    except Exception:
        print('--! Cannot find .u file.')

    return node_label, u_data


def _read_tensor_results(filename, nsg, extension):
    """Read strain and stress tensors from a SwiftComp result file.

    Parameters
    ----------
    filename : str
        Path to the tensor result file.
    nsg : int
        Structure genome dimension used to offset result columns.
    extension : str
        File extension label used in status messages.

    Returns
    -------
    tuple[list[tuple[float, ...]], list[tuple[float, ...]]]
        Strain and stress tensors parsed from the file.
    """
    strain_data = []
    stress_data = []

    try:
        for line in _iter_non_empty_tokens(filename):
            strain_data.append(tuple(float(i) for i in line[nsg:nsg + 6]))
            stress_data.append(tuple(float(i) for i in line[nsg + 6:nsg + 12]))
        print('--> Find .%s file.' % extension)
    except Exception:
        print('--! Cannot find .%s file.' % extension)

    return strain_data, stress_data


def _create_dummy_material(odb_vis, log_message=None):
    """Create the shared elastic material used for visualization.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    log_message : str, optional
        Message printed before creating the material.

    Returns
    -------
    str
        Material name created in the ODB.
    """
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


def _create_sections(odb_vis, elem_sectn, material_name, section_name_g, log_message=None):
    """Create one homogeneous section per material section label.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    elem_sectn : dict
        Mapping from section id to element labels.
    material_name : str
        Name of the material assigned to each section.
    section_name_g : str
        Shared section name prefix.
    log_message : str, optional
        Message printed before creating sections.

    Returns
    -------
    dict
        Created Abaqus sections keyed by section id.
    """
    if log_message:
        print(log_message)

    abq_section = {}
    for k in list(elem_sectn.keys()):
        section_name = section_name_g + '-' + k
        abq_section[k] = odb_vis.HomogeneousSolidSection(
            name=section_name, material=material_name
        )
    return abq_section


def _create_part_with_nodes(odb_vis, node_coord, part_name='Part-1',
                            embedded_space=THREE_D, log_message=None,
                            node_log_message=None):
    """Create a deformable part and import nodal coordinates.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    node_coord : list[tuple]
        Nodal coordinates including node labels.
    part_name : str, optional
        Name of the created part.
    embedded_space : SymbolicConstant, optional
        Embedded space used when creating the part.
    log_message : str, optional
        Message printed before creating the part.
    node_log_message : str, optional
        Message printed before importing nodes.

    Returns
    -------
    OdbPart
        Created ODB part.
    """
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


def _add_element_groups(odb_vis, part, element_groups, log_message=None):
    """Import element groups into an ODB part.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    part : OdbPart
        ODB part receiving the elements.
    element_groups : list[tuple]
        Tuples of ``(connectivity, element_type, set_name, section_category)``.
    log_message : str, optional
        Message printed before importing elements.
    """
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


def _create_instance_and_assign_sections(odb_vis, part, elem_sectn, abq_section,
                                         section_name_g, instance_name='Part-1-1',
                                         log_message=None):
    """Create the assembly instance and assign element sections.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    part : OdbPart
        ODB part instantiated in the root assembly.
    elem_sectn : dict
        Mapping from section id to element labels.
    abq_section : dict
        Created Abaqus sections keyed by section id.
    section_name_g : str
        Shared section name prefix.
    instance_name : str, optional
        Name of the created instance.
    log_message : str, optional
        Message printed before creating the instance.

    Returns
    -------
    OdbInstance
        Created root assembly instance.
    """
    if log_message:
        print(log_message)

    instance = odb_vis.rootAssembly.Instance(name=instance_name, object=part)
    for k in list(elem_sectn.keys()):
        section_name = section_name_g + ' - ' + k
        elem_set = odb_vis.rootAssembly.instances[instance_name].ElementSetFromElementLabels(
            name=section_name, elementLabels=tuple(elem_sectn[k])
        )
        instance.assignSection(region=elem_set, section=abq_section[k])

    odb_vis.save()
    return instance


def _create_step_and_frame(odb_vis, log_message=None):
    """Create the single visualization step and frame.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    log_message : str, optional
        Message printed before creating the step.

    Returns
    -------
    tuple
        Created ``(step, frame)`` pair.
    """
    if log_message:
        print(log_message)

    step = odb_vis.Step(name='Step-1', description='', domain=TIME, timePeriod=1.0)
    frame = step.Frame(incrementNumber=1, frameValue=0.1, description='')
    return step, frame


def _add_displacement_field(odb_vis, frame, step, instance, node_label, u_data,
                            log_message=None):
    """Import the displacement field when present.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    frame : OdbFrame
        Frame receiving the field output.
    step : OdbStep
        Visualization step used to mark the default deformed field.
    instance : OdbInstance
        Instance receiving the field data.
    node_label : list[int]
        Node labels in Abaqus order.
    u_data : list[tuple[float, float, float]]
        Displacement vectors.
    log_message : str, optional
        Message printed before importing the field.
    """
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


def _tensor_component_labels(field_name):
    """Build tensor component labels for one field output name.

    Parameters
    ----------
    field_name : str
        Abaqus field output name such as ``'EN'`` or ``'SNM'``.

    Returns
    -------
    tuple[str, str, str, str, str, str]
        Tensor component labels in Abaqus naming format.
    """
    shear_prefix = '2' if field_name.startswith('E') else ''
    return (
        field_name + '11',
        field_name + '22',
        field_name + '33',
        shear_prefix + field_name + '23',
        shear_prefix + field_name + '13',
        shear_prefix + field_name + '12',
    )


def _add_tensor_field(odb_vis, frame, instance, labels, data, field_name,
                      description, position, log_message=None):
    """Import one tensor field output when data is available.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    frame : OdbFrame
        Frame receiving the field output.
    instance : OdbInstance
        Instance receiving the field data.
    labels : list[int]
        Element labels matching the data order.
    data : list[tuple[float, ...]]
        Tensor values.
    field_name : str
        Abaqus field output name.
    description : str
        Field output description stored in the ODB.
    position : SymbolicConstant
        Output position such as ``ELEMENT_NODAL``.
    log_message : str, optional
        Message printed before importing the field.
    """
    if data == []:
        return

    if log_message:
        print(log_message)

    field = frame.FieldOutput(
        name=field_name,
        description=description,
        type=TENSOR_3D_FULL,
        componentLabels=_tensor_component_labels(field_name),
        validInvariants=TENSOR_INVARIANTS,
    )
    field.addData(
        position=position,
        instance=instance,
        labels=tuple(labels),
        data=tuple(data),
    )
    odb_vis.save()


def _add_tensor_fields(odb_vis, frame, instance, labels, field_specs):
    """Import multiple tensor fields defined by a small configuration list.

    Parameters
    ----------
    odb_vis : Odb
        Target output database.
    frame : OdbFrame
        Frame receiving the field outputs.
    instance : OdbInstance
        Instance receiving the field data.
    labels : list[int]
        Element labels matching the data order.
    field_specs : list[dict]
        Field definitions containing data, name, description, and position.
    """
    for field_spec in field_specs:
        _add_tensor_field(
            odb_vis=odb_vis,
            frame=frame,
            instance=instance,
            labels=labels,
            data=field_spec['data'],
            field_name=field_spec['name'],
            description=field_spec['description'],
            position=field_spec['position'],
            log_message=field_spec.get('log_message'),
        )

# ==============================================================================
#
#   Main
#
# ==============================================================================

def visualization(macro_model, ap_flag, sc_input):

#    sc_input = sc_input.replace('\\','/')

    # =======================================================================
    # Read data from files
    # =======================================================================
    sc_input=sc_input.replace('\\','/')
#    debug = open(sc_input + '.debug', 'w')
#    print sc_input
    # =======================================================================
    # Read data from files
    # =======================================================================
    
    
    u_filename   = sc_input + r'.u'
    sg_filename  = sc_input + r'.sg'
    sn_filename  = sc_input + r'.sn'
    sgm_filename = sc_input + r'.sgm'
    snm_filename = sc_input + r'.snm'
    
#    sc_input_temp = sc_input.split('/')
#    project_path  = '/'.join(sc_input_temp[:-1])
    project_path = os.path.dirname(sc_input)
#    project_name  = sc_input_temp[-1]
    sc_input_sc = os.path.basename(sc_input)
    checkDehoVisual(sc_input_sc, 'visual')
    #print 'sc_input_sc %s' %sc_input_sc
    project_name = sc_input_sc.split('.')
    project_name = project_name[0]
    #print 'project_name %s' %project_name
    # check if the odb has already exist, and check if the file .sc exist or not.
    checkDehoVisual(sc_input_sc, 'visual')
    
    
    macro_model_dimension = str(macro_model) + 'D'
    mesh_data = scio.read_swiftcomp_input_mesh(
        sc_input, macro_model_dimension, ap_flag
    )
    nsg = mesh_data['nsg']
    node_coord = mesh_data['node_coord']
    elem_sectn = mesh_data['elem_sectn']
    elem_label = mesh_data['elem_label']
    elem_connt_s3 = mesh_data['elem_connt_s3']
    elem_connt_s6 = mesh_data['elem_connt_s6']
    elem_connt_s4 = mesh_data['elem_connt_s4']
    elem_connt_s8 = mesh_data['elem_connt_s8']
    elem_connt_s9 = mesh_data['elem_connt_s9']
    elem_connt_c4 = mesh_data['elem_connt_c4']
    elem_connt_c6 = mesh_data['elem_connt_c6']
    elem_connt_c10 = mesh_data['elem_connt_c10']
    elem_connt_c8 = mesh_data['elem_connt_c8']
    elem_connt_c20 = mesh_data['elem_connt_c20']
    elem_connt_c15 = mesh_data['elem_connt_c15']
    elem_connt_b31_temp = mesh_data['elem_connt_b31_temp']
    elem_connt_b31 = []

    result_data = scio.read_swiftcomp_results(sc_input, nsg)
    node_label = result_data['node_label']
    u_data = result_data['u_data']
    sg_strain = result_data['sg_strain']
    sg_stress = result_data['sg_stress']
    sn_strain = result_data['sn_strain']
    sn_stress = result_data['sn_stress']
    sgm_strain = result_data['sgm_strain']
    sgm_stress = result_data['sgm_stress']
    snm_strain = result_data['snm_strain']
    snm_stress = result_data['snm_stress']
    
    #=========================================================
    # tranfer sn data for nsg==1:  only work for cases that each edge contains the same number of B31 elements!
    #=========================================================
    new_conn = []
    if nsg == 1:
        print('--> Convert beam element infomation...')
        
#        elem_connt_b31_temp : element_id_aba,  element connectivity                           
        nelem_edge=len(elem_connt_b31_temp[0]) -2  # nelem_edge per edge/(element of swiftcomp)
        
        if nelem_edge == 1:
            elem_connt_b31= elem_connt_b31_temp
            print('--> Two noded beam element are implemented, no convertion is necessary. ')
    
            
        else:
            elem_label = []
            for item in elem_connt_b31_temp:
                elabel = (item[0] - 1) * nelem_edge + 1
                for i in range(nelem_edge):
                    elem_label.append(elabel + i)
                if nelem_edge == 4:
                    new_conn.append((elabel, item[1], item[3]))
                    new_conn.append((elabel + 1, item[3], item[5]))
                    new_conn.append((elabel + 2, item[5], item[4]))
                    new_conn.append((elabel + 3, item[4], item[2]))
                elif nelem_edge == 3:
                    new_conn.append((elabel, item[1], item[3]))
                    new_conn.append((elabel + 1, item[3], item[4]))
                    new_conn.append((elabel + 2, item[4], item[2]))
                elif nelem_edge == 2:
                    new_conn.append((elabel, item[1], item[3]))
                    new_conn.append((elabel + 1, item[3], item[2]))
                
            elem_connt_b31 = new_conn
         
            elem_sectn_new = {}
            for sect, elems in elem_sectn.items():
                elem_sectn_new[sect] = []
                for i in range(len(elems)):
                    temp_i = [(elems[i]-1) * nelem_edge + 1 + j for j in range(nelem_edge)]
                    elem_sectn_new[sect] = elem_sectn_new[sect] + temp_i
            elem_sectn = elem_sectn_new
            new_strain = []
            new_stress = []

            nedge = int(len(elem_label) / nelem_edge)
            print('number of beam elements in the 1D SG model: ')
            print(nedge)

            if nelem_edge == 4:
                nodes_edge = [0,2,2,4,4,3,3,1]
            elif nelem_edge == 3:
                nodes_edge = [0,2,2,3,3,1]
            elif nelem_edge == 2:
                nodes_edge = [0,2,2,1]
    
            for edge_i in range(nedge):
                for j in range(len(nodes_edge)):
                    new_strain.append(sn_strain[nodes_edge[j] + (nelem_edge+1) * edge_i])
                    new_stress.append(sn_stress[nodes_edge[j] + (nelem_edge+1) * edge_i])
            sn_strain = new_strain
            sn_stress = new_stress

    # =======================================================================
    # Create odb file and import data
    # =======================================================================
    
    # ---------------------
    # Create a new odb file
    print('--> Creating ODB file...')
    odb_name = project_name
    odb_title = project_name
    odb_file_name = os.path.join(project_path, project_name + '.odb')

    # Check if ODB already exists
    if os.path.exists(odb_file_name):
        print("--! Warning: ODB file already exists and will be overwritten.")
        try:
            # Try closing if it's open
            try:
                odb = openOdb(odb_file_name)
                odb.close()
            except Exception:
                pass

            os.remove(odb_file_name)
            aux_dir = odb_file_name + "_f"
            if os.path.isdir(aux_dir):
                shutil.rmtree(aux_dir)

            print("--> Existing ODB deleted.")
        except OSError as e:
            print("--! Failed to delete existing ODB: {}".format(e))
            sys.exit(1)
    
    odb = Odb(name = odb_name, 
              analysisTitle = odb_title, 
              description = 'SwiftComp Dehomogenization', 
              path = odb_file_name)

    # print('\nelem_label:')
    # print(elem_label)
    # print('\nsn_strain:')
    # print(sn_strain)

    if nsg == 2:
        visualization2D(odb, project_name, node_coord, elem_connt_s3, elem_connt_s6, 
                        elem_connt_s4, elem_connt_s8, elem_connt_s9, elem_sectn, node_label, elem_label, 
                        u_data, sg_strain, sg_stress, sn_strain, sn_stress, 
                        sgm_strain, sgm_stress, snm_strain, snm_stress)
    elif nsg == 3:
        visualization3D(odb, project_name, node_coord,
                        elem_connt_c4, elem_connt_c6,
                        elem_connt_c8, elem_connt_c10,
                        elem_connt_c15, elem_connt_c20,
                        elem_sectn, node_label, elem_label,
                        u_data, sg_strain, sg_stress,
                        sn_strain, sn_stress,
                        sgm_strain, sgm_stress,
                        snm_strain, snm_stress)
    elif nsg == 1:
        visualization1D(odb, project_name, node_coord, elem_connt_b31, elem_sectn, node_label, elem_label, 
                        u_data, sg_strain, sg_stress, sn_strain, sn_stress)
                        
    print('    Done.')
    
    session.odbs[odb_name].close()
    odb = openOdb(odb_file_name)
    
    # Customize the viewport
    vp1, vp2 = abq_view.split_viewport_left_right()
    uab.setViewYZ(vp=vp1, nsg=nsg, obj=odb)
    abq_view.configure_odb_contour_display(
        vp=vp1, variable_label='EN', component='EN11', restore=True
    )
    abq_view.configure_viewport_annotations(vp=vp1)
    uab.setViewYZ(vp=vp2, nsg=nsg, obj=odb)
    abq_view.configure_odb_contour_display(
        vp=vp2, variable_label='SN', component='SN11'
    )

    abq_view.make_current(vp=vp1)
    abq_view.set_linked_viewports(link_viewports=True)

    return 1



# ==============================================================================
#
#   Visualization of 1D SG
#
# ==============================================================================

def visualization1D(odb_vis, project_name, node_coord, elem_connt_b31, 
                    elem_sectn, node_label, elem_label, 
                    u_data, sg_strain, sg_stress, sn_strain, sn_stress):
    section_name_g = 'nLayer'
    material_name = _create_dummy_material(odb_vis)
    abq_section = _create_sections(
        odb_vis, elem_sectn, material_name, section_name_g
    )

    part_1 = _create_part_with_nodes(odb_vis, node_coord)
    _add_element_groups(
        odb_vis,
        part_1,
        [(elem_connt_b31, 'B31', 'eSet-b31', None)],
    )

    instance_1 = _create_instance_and_assign_sections(
        odb_vis, part_1, elem_sectn, abq_section, section_name_g
    )
    step_1, frame_1 = _create_step_and_frame(odb_vis)
    _add_displacement_field(
        odb_vis, frame_1, step_1, instance_1, node_label, u_data
    )

    _add_tensor_fields(
        odb_vis,
        frame_1,
        instance_1,
        elem_label,
        [
            {
                'data': sg_strain,
                'name': 'EG',
                'description': 'Strains at Gaussian points.',
                'position': INTEGRATION_POINT,
            },
            {
                'data': sg_stress,
                'name': 'SG',
                'description': 'Stresses at Gaussian points.',
                'position': INTEGRATION_POINT,
            },
            {
                'data': sn_strain,
                'name': 'EN',
                'description': 'Strains at nodes.',
                'position': ELEMENT_NODAL,
            },
            {
                'data': sn_stress,
                'name': 'SN',
                'description': 'Stresses at nodes.',
                'position': ELEMENT_NODAL,
            },
        ],
    )
        
    return 1
    


# ==============================================================================
#
#   Visualization of 2D SG
#
# ==============================================================================

def visualization2D(
    odb_vis, project_name, node_coord, elem_connt_s3, elem_connt_s6, 
    elem_connt_s4, elem_connt_s8, elem_connt_s9, elem_sectn, node_label, elem_label, 
    u_data, sg_strain, sg_stress, sn_strain, sn_stress, 
    sgm_strain, sgm_stress, snm_strain, snm_stress
    ):
    section_name_g = 'Homogeneous solid section'
    material_name = _create_dummy_material(odb_vis)
    abq_section = _create_sections(
        odb_vis, elem_sectn, material_name, section_name_g
    )
    s_cat = odb_vis.SectionCategory(name='S5', description='')

    part_1 = _create_part_with_nodes(odb_vis, node_coord)
    _add_element_groups(
        odb_vis,
        part_1,
        [
            (elem_connt_s3, 'WARPF2D3', 'eSet-s3', s_cat),
            (elem_connt_s6, 'WARPF2D6', 'eSet-s6', s_cat),
            (elem_connt_s4, 'WARPF2D4', 'eSet-s4', s_cat),
            (elem_connt_s8, 'WARPF2D8', 'eSet-s8', s_cat),
            (elem_connt_s9, 'M3D9', 'eSet-s9', s_cat),
        ],
    )

    instance_1 = _create_instance_and_assign_sections(
        odb_vis, part_1, elem_sectn, abq_section, section_name_g
    )
    step_1, frame_1 = _create_step_and_frame(odb_vis)
    _add_displacement_field(
        odb_vis, frame_1, step_1, instance_1, node_label, u_data
    )

    _add_tensor_fields(
        odb_vis,
        frame_1,
        instance_1,
        elem_label,
        [
            {
                'data': sn_strain,
                'name': 'EN',
                'description': 'Strains at nodes in the global coordinates.',
                'position': ELEMENT_NODAL,
                'log_message': ' --> Importing strains at elemental nodes in the global coordinates...',
            },
            {
                'data': sn_stress,
                'name': 'SN',
                'description': 'Stresses at nodes in the global coordinates.',
                'position': ELEMENT_NODAL,
                'log_message': ' --> Importing stresses at elemental nodes in the global coordinates...',
            },
            {
                'data': sgm_strain,
                'name': 'EGM',
                'description': 'Strains at Gaussian points in the material coordinates.',
                'position': INTEGRATION_POINT,
            },
            {
                'data': sgm_stress,
                'name': 'SGM',
                'description': 'Stresses at Gaussian points in the material coordinates.',
                'position': INTEGRATION_POINT,
            },
            {
                'data': snm_strain,
                'name': 'ENM',
                'description': 'Strains at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
            },
            {
                'data': snm_stress,
                'name': 'SNM',
                'description': 'Stresses at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
            },
        ],
    )
        
    return 1
    


# ==============================================================================
#
#   Visualization of 3D SG
#
# ==============================================================================

def visualization3D(odb_vis, project_name, node_coord, elem_connt_c4, elem_connt_c6,
                    elem_connt_c8, elem_connt_c10, elem_connt_c15, elem_connt_c20,
                    elem_sectn, node_label, elem_label,
                    u_data, sg_strain, sg_stress, sn_strain, sn_stress,
                    sgm_strain, sgm_stress, snm_strain, snm_stress):
    section_name_g = 'Homogeneous solid section'
    material_name = _create_dummy_material(
        odb_vis, log_message=' --> Creating a dummy material...'
    )
    abq_section = _create_sections(
        odb_vis,
        elem_sectn,
        material_name,
        section_name_g,
        log_message=' --> Creating dummy sections...',
    )

    part_1 = _create_part_with_nodes(
        odb_vis,
        node_coord,
        log_message=' --> Creating a new part...',
        node_log_message=' --> Importing nodes...',
    )
    _add_element_groups(
        odb_vis,
        part_1,
        [
            (elem_connt_c4, 'C3D4', 'eSet-c3d4', None),
            (elem_connt_c6, 'C3D6', 'eSet-c3d6', None),
            (elem_connt_c10, 'C3D10', 'eSet-c3d10', None),
            (elem_connt_c8, 'C3D8', 'eSet-c3d8', None),
            (elem_connt_c15, 'C3D15', 'eSet-c3d15', None),
            (elem_connt_c20, 'C3D20', 'eSet-c3d20', None),
        ],
        log_message=' --> Importing elements...',
    )

    instance_1 = _create_instance_and_assign_sections(
        odb_vis,
        part_1,
        elem_sectn,
        abq_section,
        section_name_g,
        log_message=' --> Creating a new instance...',
    )
    step_1, frame_1 = _create_step_and_frame(
        odb_vis, log_message=' --> Creating new step and frame...'
    )
    _add_displacement_field(
        odb_vis,
        frame_1,
        step_1,
        instance_1,
        node_label,
        u_data,
        log_message=' --> Importing displacement data...',
    )

    print(' --> Importing strain and stress data under global coordinates...')
    _add_tensor_fields(
        odb_vis,
        frame_1,
        instance_1,
        elem_label,
        [
            {
                'data': sn_strain,
                'name': 'EN',
                'description': 'Strains at nodes in the global coordinates.',
                'position': ELEMENT_NODAL,
                'log_message': '  --> Strains at elemental nodes...',
            },
            {
                'data': sn_stress,
                'name': 'SN',
                'description': 'Stresses at nodes in the global coordinates.',
                'position': ELEMENT_NODAL,
                'log_message': '  --> Stresses at elemental nodes...',
            },
        ],
    )

    print(' --> Importing strain and stress data under material coordinates...')
    _add_tensor_fields(
        odb_vis,
        frame_1,
        instance_1,
        elem_label,
        [
            {
                'data': snm_strain,
                'name': 'ENM',
                'description': 'Strains at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
                'log_message': '  --> Strains at elemental nodes...',
            },
            {
                'data': snm_stress,
                'name': 'SNM',
                'description': 'Stresses at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
                'log_message': '  --> Stresses at elemental nodes...',
            },
        ],
    )
        
    return 1
    




