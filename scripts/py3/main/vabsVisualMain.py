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
from sgdataio import vabs as vabsio
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

def visualization(vabs_input):

#    sc_input = sc_input.replace('\\','/')

    # =======================================================================
    # Read data from files
    # =======================================================================
    # vabs_input = vabs_input.replace('\\','/')
#    debug = open(sc_input + '.debug', 'w')
#    print sc_input
    # =======================================================================
    # Read data from files
    # =======================================================================
    project_path, project_name = resolve_project_location(vabs_input)
# #    sc_input_temp = sc_input.split('/')
# #    project_path  = '/'.join(sc_input_temp[:-1])
#     project_path = os.path.dirname(sc_input)
# #    project_name  = sc_input_temp[-1]
#     sc_input_sc = os.path.basename(sc_input)
#     checkDehoVisual(sc_input_sc, 'visual')
#     #print 'sc_input_sc %s' %sc_input_sc
#     project_name = sc_input_sc.split('.')
#     project_name = project_name[0]
#     #print 'project_name %s' %project_name
#     # check if the odb has already exist, and check if the file .sc exist or not.
#     checkDehoVisual(sc_input_sc, 'visual')
    
    
    # macro_model_dimension=str(macro_model)+'D'
    
    # if ap_flag==False:
    #     if macro_model_dimension == '1D':            # Beam
    #         skip_line = [1, 2, 3, 4]
    #     elif macro_model_dimension == '2D':          # Plate/Shell
    #         skip_line = [1, 2, 3]
    #     elif macro_model_dimension == '3D':          # Solid/Block
    #         skip_line = [1]
    # else:
    #     if macro_model_dimension == '1D':            # Beam
    #         skip_line = [1, 2, 3, 4, 5]
    #     elif macro_model_dimension == '2D':          # Plate/Shell
    #         skip_line = [1, 2, 3, 4]
    #     elif macro_model_dimension == '3D':          # Solid/Block
    #         skip_line = [1, 2 ]
            
    mesh_data = vabsio.read_vabs_input_mesh(vabs_input)
    node_coord = mesh_data['node_coord']
    elem_sectn = mesh_data['elem_sectn']
    elem_label = mesh_data['elem_label']
    elem_connt_s3 = mesh_data['elem_connt_s3']
    elem_connt_s6 = mesh_data['elem_connt_s6']
    elem_connt_s4 = mesh_data['elem_connt_s4']
    elem_connt_s8 = mesh_data['elem_connt_s8']
    elem_connt_s9 = mesh_data['elem_connt_s9']

    result_data = vabsio.read_vabs_results(vabs_input)
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
#     new_conn = []
#     if nsg == 1:
#         print '--> Convert beam element infomation...'
        
# #        elem_connt_b31_temp : element_id_aba,  element connectivity                           
#         nelem_edge=len(elem_connt_b31_temp[0]) -2  # nelem_edge per edge/(element of swiftcomp)
        
#         if nelem_edge == 1:
#             elem_connt_b31= elem_connt_b31_temp
#             print '--> Two noded beam element are implemented, no convertion is necessary. '
    
            
#         else:
#             elem_label = []
#             for item in elem_connt_b31_temp:
#                 elabel = (item[0] - 1) * nelem_edge + 1
#                 for i in range(nelem_edge):
#                     elem_label.append(elabel + i)
#                 if nelem_edge == 4:
#                     new_conn.append((elabel, item[1], item[3]))
#                     new_conn.append((elabel + 1, item[3], item[5]))
#                     new_conn.append((elabel + 2, item[5], item[4]))
#                     new_conn.append((elabel + 3, item[4], item[2]))
#                 elif nelem_edge == 3:
#                     new_conn.append((elabel, item[1], item[3]))
#                     new_conn.append((elabel + 1, item[3], item[4]))
#                     new_conn.append((elabel + 2, item[4], item[2]))
#                 elif nelem_edge == 2:
#                     new_conn.append((elabel, item[1], item[3]))
#                     new_conn.append((elabel + 1, item[3], item[2]))
                
#             elem_connt_b31 = new_conn
         
#             elem_sectn_new = {}
#             for sect, elems in elem_sectn.iteritems():
#                 elem_sectn_new[sect] = []
#                 for i in range(len(elems)):
#                     temp_i = [(elems[i]-1) * nelem_edge + 1 + j for j in range(nelem_edge)]
#                     elem_sectn_new[sect] = elem_sectn_new[sect] + temp_i
#             elem_sectn = elem_sectn_new
#             new_strain = []
#             new_stress = []
                
#             nedge = len(elem_label) / nelem_edge
#             print 'number of beam elements in the 1D SG model: '
#             print nedge
                
#             if nelem_edge == 4:
#                 nodes_edge = [0,2,2,4,4,3,3,1]
#             elif nelem_edge == 3:
#                 nodes_edge = [0,2,2,3,3,1]
#             elif nelem_edge == 2:
#                 nodes_edge = [0,2,2,1]
    
#             for edge_i in range(nedge):
#                 for j in range(len(nodes_edge)):
#                     new_strain.append(sn_strain[nodes_edge[j] + (nelem_edge+1) * edge_i])
#                     new_stress.append(sn_stress[nodes_edge[j] + (nelem_edge+1) * edge_i])
#             sn_strain = new_strain
#             sn_stress = new_stress

    # =======================================================================
    # Create odb file and import data
    # =======================================================================
    
    odb, odb_name, odb_file_name = create_visualization_odb(
        project_path=project_path,
        project_name=project_name,
        description='VABS Dehomogenization',
        overwrite_existing=True,
    )
    
    # if nsg == 2:
    visualization2D(
        odb, project_name, node_coord, elem_connt_s3, elem_connt_s6, 
        elem_connt_s4, elem_connt_s8, elem_connt_s9, elem_sectn, node_label, 
        elem_label, u_data, sg_strain, sg_stress, sn_strain, sn_stress, 
        sgm_strain, sgm_stress, snm_strain, snm_stress)
    # elif nsg == 3:
    #     visualization3D(odb, project_name, node_coord, elem_connt_c4, elem_connt_c10, 
    #                     elem_connt_c8, elem_connt_c20, elem_sectn, node_label, elem_label, 
    #                     u_data, sg_strain, sg_stress, sn_strain, sn_stress, 
    #                     sgm_strain, sgm_stress, snm_strain, snm_stress)
    # elif nsg == 1:
    #     visualization1D(odb, project_name, node_coord, elem_connt_b31, elem_sectn, node_label, elem_label, 
    #                     u_data, sg_strain, sg_stress, sn_strain, sn_stress)
                        
    print('    Done.')
    
    odb = reopen_visualization_odb(odb_name, odb_file_name)
    configure_visualization_viewports(
        odb=odb,
        nsg=2,
        primary_visible_edges=FEATURE,
        link_field_output=False,
    )

    return 1



# ====================================================================
#
#   Visualization of 2D SG
#
# ====================================================================

def visualization2D(
    odb_vis, project_name, node_coord, elem_connt_s3, elem_connt_s6, 
    elem_connt_s4, elem_connt_s8, elem_connt_s9, elem_sectn, node_label, 
    elem_label, u_data, sg_strain, sg_stress, sn_strain, sn_stress, 
    sgm_strain, sgm_stress, snm_strain, snm_stress
    ):
    print('    -> Creating a dummy material...')
    material_name = create_dummy_material(odb_vis)

    print('    -> Creating sections...')
    section_name_g = 'Homogeneous shell section'
    abq_section = create_sections(
        odb_vis,
        elem_sectn,
        material_name,
        section_name_g,
        section_kind='shell',
        section_kwargs={'thickness': 0.1},
    )
    s_cat, sp_bot = create_section_category(
        odb_vis, name='S5', section_point_number=1,
        section_point_description='Bottom'
    )

    print('    -> Creating a new part...')
    part_1 = create_part_with_nodes(odb_vis, node_coord)
    add_element_groups(
        odb_vis,
        part_1,
        [
            (elem_connt_s3, 'DS3', 'eSet-s3', s_cat),
            (elem_connt_s6, 'DS6', 'eSet-s6', s_cat),
            (elem_connt_s4, 'DS4', 'eSet-s4', s_cat),
            (elem_connt_s8, 'DS8', 'eSet-s8', s_cat),
            (elem_connt_s9, 'M3D9', 'eSet-s9', s_cat),
        ],
    )

    print('    -> Creating a new instance...')
    instance_1 = create_instance_and_assign_sections(
        odb_vis, part_1, elem_sectn, abq_section, section_name_g
    )

    print('    -> Creating a new step...')
    step_1, frame_1 = create_step_and_frame(odb_vis)

    print('    -> Importing displacements...')
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
                'name': 'E',
                'description': 'Strains at Gaussian points in the global coordinates.',
                'position': INTEGRATION_POINT,
                'section_point': sp_bot,
                'component_labels': ('E11', '2E12', '2E13', 'E22', '2E23', 'E33'),
                'log_message': '    -> Importing strains at Gaussian points...',
            },
            {
                'data': sg_stress,
                'name': 'S',
                'description': 'Stresses at Gaussian points in the global coordinates.',
                'position': INTEGRATION_POINT,
                'section_point': sp_bot,
                'component_labels': ('S11', 'S12', 'S13', 'S22', 'S23', 'S33'),
                'log_message': '    -> Importing stresses at Gaussian points...',
            },
            {
                'data': sn_strain,
                'name': 'EN',
                'description': 'Strains at nodes in the global coordinates.',
                'position': ELEMENT_NODAL,
                'section_point': sp_bot,
                'component_labels': ('EN11', '2EN12', '2EN13', 'EN22', '2EN23', 'EN33'),
                'log_message': '    -> Importing strains at elemental nodes...',
            },
            {
                'data': sn_stress,
                'name': 'SN',
                'description': 'Stresses at nodes in the global coordinates.',
                'position': ELEMENT_NODAL,
                'section_point': sp_bot,
                'component_labels': ('SN11', 'SN12', 'SN13', 'SN22', 'SN23', 'SN33'),
                'log_message': '    -> Importing stresses at elemental nodes...',
            },
            {
                'data': sgm_strain,
                'name': 'EM',
                'description': 'Strains at Gaussian points in the material coordinates.',
                'position': INTEGRATION_POINT,
                'section_point': sp_bot,
                'component_labels': ('EM11', '2EM12', '2EM13', 'EM22', '2EM23', 'EM33'),
                'log_message': '    -> Importing strains at Gaussian points in material coordinates...',
            },
            {
                'data': sgm_stress,
                'name': 'SM',
                'description': 'Stresses at Gaussian points in the material coordinates.',
                'position': INTEGRATION_POINT,
                'section_point': sp_bot,
                'component_labels': ('SM11', 'SM12', 'SM13', 'SM22', 'SM23', 'SM33'),
                'log_message': '    -> Importing stresses at Gaussian points in material coordinates...',
            },
            {
                'data': snm_strain,
                'name': 'EMN',
                'description': 'Strains at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
                'section_point': sp_bot,
                'component_labels': ('EMN11', '2EMN12', '2EMN13', 'EMN22', '2EMN23', 'EMN33'),
                'log_message': '    -> Importing strains at elemental nodes in material coordinates...',
            },
            {
                'data': snm_stress,
                'name': 'SMN',
                'description': 'Stresses at nodes in the material coordinates.',
                'position': ELEMENT_NODAL,
                'section_point': sp_bot,
                'component_labels': ('SMN11', 'SMN12', 'SMN13', 'SMN22', 'SMN23', 'SMN33'),
                'log_message': '    -> Importing stresses at elemental nodes in material coordinates...',
            },
        ],
    )
        
    return 1
    





