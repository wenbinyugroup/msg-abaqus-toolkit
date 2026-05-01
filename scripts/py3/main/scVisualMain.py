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
from main.visualization_common import (
    add_displacement_field,
    add_element_groups,
    add_tensor_fields,
    configure_visualization_viewports,
    create_dummy_material,
    create_instance_and_assign_sections,
    create_part_with_nodes,
    create_section_category,
    create_sections,
    create_step_and_frame,
    create_visualization_odb,
    reopen_visualization_odb,
    resolve_project_location,
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
    sc_input_sc = os.path.basename(sc_input)
    checkDehoVisual(sc_input_sc, 'visual')
    project_path, project_name = resolve_project_location(sc_input)

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
    
    odb, odb_name, odb_file_name = create_visualization_odb(
        project_path=project_path,
        project_name=project_name,
        description='SwiftComp Dehomogenization',
        overwrite_existing=True,
    )

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
    
    odb = reopen_visualization_odb(odb_name, odb_file_name)
    configure_visualization_viewports(odb=odb, nsg=nsg)

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
    material_name = create_dummy_material(odb_vis)
    abq_section = create_sections(
        odb_vis, elem_sectn, material_name, section_name_g
    )

    part_1 = create_part_with_nodes(odb_vis, node_coord)
    add_element_groups(
        odb_vis,
        part_1,
        [(elem_connt_b31, 'B31', 'eSet-b31', None)],
    )

    instance_1 = create_instance_and_assign_sections(
        odb_vis, part_1, elem_sectn, abq_section, section_name_g
    )
    step_1, frame_1 = create_step_and_frame(odb_vis)
    add_displacement_field(
        odb_vis, frame_1, step_1, instance_1, node_label, u_data
    )

    add_tensor_fields(
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
    material_name = create_dummy_material(odb_vis)
    abq_section = create_sections(
        odb_vis, elem_sectn, material_name, section_name_g
    )
    s_cat, sp_bot = create_section_category(
        odb_vis, name='S5', section_point_number=1,
        section_point_description='Bottom'
    )

    part_1 = create_part_with_nodes(odb_vis, node_coord)
    add_element_groups(
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

    instance_1 = create_instance_and_assign_sections(
        odb_vis, part_1, elem_sectn, abq_section, section_name_g
    )
    step_1, frame_1 = create_step_and_frame(odb_vis)
    add_displacement_field(
        odb_vis, frame_1, step_1, instance_1, node_label, u_data
    )

    add_tensor_fields(
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
                'section_point': sp_bot,
                'log_message': ' --> Importing strains at elemental nodes in the global coordinates...',
            },
            {
                'data': sn_stress,
                'name': 'SN',
                'description': 'Stresses at nodes in the global coordinates.',
                'position': ELEMENT_NODAL,
                'section_point': sp_bot,
                'log_message': ' --> Importing stresses at elemental nodes in the global coordinates...',
            },
            {
                'data': sgm_strain,
                'name': 'EGM',
                'description': 'Strains at Gaussian points in the material coordinates.',
                'position': INTEGRATION_POINT,
                'section_point': sp_bot,
            },
            {
                'data': sgm_stress,
                'name': 'SGM',
                'description': 'Stresses at Gaussian points in the material coordinates.',
                'position': INTEGRATION_POINT,
                'section_point': sp_bot,
            },
            {
                'data': snm_strain,
                'name': 'ENM',
                'description': 'Strains at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
                'section_point': sp_bot,
            },
            {
                'data': snm_stress,
                'name': 'SNM',
                'description': 'Stresses at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
                'section_point': sp_bot,
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
    material_name = create_dummy_material(
        odb_vis, log_message=' --> Creating a dummy material...'
    )
    abq_section = create_sections(
        odb_vis,
        elem_sectn,
        material_name,
        section_name_g,
        log_message=' --> Creating dummy sections...',
    )

    part_1 = create_part_with_nodes(
        odb_vis,
        node_coord,
        log_message=' --> Creating a new part...',
        node_log_message=' --> Importing nodes...',
    )
    add_element_groups(
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

    instance_1 = create_instance_and_assign_sections(
        odb_vis,
        part_1,
        elem_sectn,
        abq_section,
        section_name_g,
        log_message=' --> Creating a new instance...',
    )
    step_1, frame_1 = create_step_and_frame(
        odb_vis, log_message=' --> Creating new step and frame...'
    )
    add_displacement_field(
        odb_vis,
        frame_1,
        step_1,
        instance_1,
        node_label,
        u_data,
        log_message=' --> Importing displacement data...',
    )

    print(' --> Importing strain and stress data under global coordinates...')
    add_tensor_fields(
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
    add_tensor_fields(
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
    




