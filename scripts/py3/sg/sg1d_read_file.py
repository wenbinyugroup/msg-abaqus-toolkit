# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from textRepr import *
from caeModules import *
from math import *

from utils.utilities import *
from sg.layup import create_1d_part_with_composite_layup


# ==============================================================================
#
#   Read File
#
# ==============================================================================

def fromInputfile1D(file_layup_input, model_name, element_type):
    model = mdb.models[model_name]
    mat_abq = list(model.materials.keys())
    
    layup_input = file_layup_input.replace('\\','/')
    temp = layup_input.rsplit('/')
    temp = temp[-1]
    part_name = temp.rsplit('.')[0]

    # ------------------------------------
    # Read layup data from layup input file
    plies_sc = {}
    mat_dict = {}
    parameter_line = [1]
    sym_flag = 'n'
    offset_ratio = 0.0
    i = 1
    j = 0
#    print '--> Reading Layup input file...'
    
    with open(layup_input, 'r') as fin:
        for line in fin:
            line = line.strip()
            if line == '\n' or line == '':
                continue
            else:
                line = line.split()
                if i == parameter_line[-1]:
                    n_ply = int(line[0])              # Read the number of plies
                    nmat = int(line[1])            # Read the number of materials
                    if len(line) <= 4:
                        sym_flag = str(line[2])             # Read if the layup should be symmetrical or antisymmetric ( n, sym, antisym)
                    if len(line) == 4:
                        offset_ratio = float(line[3])            # Read the offset_ratio
                    i += 1
                elif j <= (n_ply-1):                    # construct plies_sc  {'ply_id_sc':}
                    ply_id_sc = j        #  the key of plies_sc[ply_id_sc] begin at 0.
                    plies_sc[ply_id_sc] = (float(line[0]), float(line[1]), int(line[2]))   # thickness, orientation, mat_id
                    if sym_flag[0] == 's':
                        ply_id_sc_s = 2*n_ply - 1 - ply_id_sc
                        plies_sc[ply_id_sc_s] = plies_sc[ply_id_sc]
                    elif sym_flag[0] == 'a' and ply_id_sc != (n_ply-1):
                        ply_id_sc_a = 2*(n_ply-1) - ply_id_sc
                        plies_sc[ply_id_sc_a] = plies_sc[ply_id_sc]
                    j += 1
                elif j <= (n_ply - 1 + nmat):          # Read element connectivities
                    mat_id = int(line[0])
                    mat_name = str(line[1])
                    mat_dict[mat_id] = mat_name
                    if mat_name not in mat_abq:
                        raise ValueError('material \'%s \' is not existed in model \'%s\'.' %(mat_name, model_name))
                    j += 1
    
    if len(mat_dict) != nmat:
        raise ValueError('The material types existed in the layup is not equal to the number of materials specified!')
    
    n_ply = len(plies_sc)
    
    layup_t = []
    layup_ori = []
    layup_mat = []
    for ply_id in range(n_ply) :
        layup_t.append(plies_sc[ply_id][0])
        layup_ori.append(plies_sc[ply_id][1])
        mat_id = plies_sc[ply_id][2]
        mat_name = mat_dict[mat_id]
        layup_mat.append(mat_name)

    create_1d_part_with_composite_layup(
        model_name,
        part_name,
        layup_mat,
        layup_t,
        layup_ori,
        offset_ratio,
        element_type,
    )

    return 1

