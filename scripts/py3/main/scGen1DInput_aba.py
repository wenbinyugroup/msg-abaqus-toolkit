# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqusConstants import *
from textRepr import *
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
import os
from utils.utilities import *
from sgdataio.swiftcomp import checkMaterials, writeMaterials
from sg.sg_data import register_sg_in_mdb
from sg.layup import extract_composite_layup_sc_data


def generate_1DInputFromCAE(model_source, macro_model_dimension, analysis, elem_flag, trans_flag,
                            w, nSG, model_name, part_name, abaqus_input, new_filename,
                            specific_model, bk,
                            sk, cos,
                            temp_flag):

    model = mdb.models[model_name]
    part  = model.parts[part_name]
    nodes = part.nodes
    edges = part.edges
    nnode = len(nodes)
    nelem = len(edges)

    if nelem == 0:
        raise ValueError('Part %s has no mesh edges; generate the mesh first.' % part_name)

    nMaxnode_elem = 5  # max nodes per 1D element

    # Extract material/layer data from composite layup
    matDict, nlayers, plies, offset = extract_composite_layup_sc_data(part)
    checkMaterials(matDict, analysis, model_name)

    if nelem != len(plies):
        raise ValueError(
            'Part %s: edge count (%d) != ply count (%d); '
            'each mesh edge must correspond to exactly one ply.'
            % (part_name, nelem, len(plies))
        )

    nmate  = len(matDict)
    nslave = 0
    nlayer = len(nlayers)

    nnodes_scelem = len(list(edges[0].getNodes()))

    if new_filename == '':
        swiftcomp_filename = (
            part_name + '_nSG' + str(nSG) + '_' + macro_model_dimension
            + '_n' + str(nnodes_scelem)
        )
    else:
        swiftcomp_filename = new_filename

    register_sg_in_mdb(
        swiftcomp_filename, model_source, model_name, part_name, abaqus_input,
        swiftcomp_filename, macro_model_dimension, w, analysis, elem_flag,
        trans_flag, temp_flag, specific_model, bk, cos, sk,
    )

    with open(swiftcomp_filename + '.sc', 'w') as sc_file:
        if macro_model_dimension != '3D':
            writeFormat(sc_file, 'd', [specific_model])
            sc_file.write('\n')

        if macro_model_dimension == '2D':
            writeFormat(sc_file, 'EE', sk)
            sc_file.write('\n')
        elif macro_model_dimension == '1D':
            raise ValueError('1D SG cannot be used for beam model!')

        writeFormat(sc_file, 'd' * 4, [analysis, elem_flag, trans_flag, temp_flag])
        sc_file.write('\n')

        writeFormat(sc_file, 'd' * 6, [nSG, nnode, nelem, nmate, nslave, nlayer])
        sc_file.write('\n')

        # Write node info: label + z coordinate (1D SG uses z axis only)
        for i in range(nnode):
            ndCoords = nodes[i].coordinates
            writeFormat(sc_file, 'dE', [nodes[i].label, float(ndCoords[2]) + offset])
        sc_file.write('\n')

        # Write edge connectivity
        for i in range(nelem):
            connect_temp = list(edges[i].getNodes())
            connect = [n.label for n in connect_temp]
            abaEle_edge = len(connect) - 1
            if abaEle_edge == 4:
                # swap mid-side nodes to match SwiftComp ordering
                connect[3], connect[4] = connect[4], connect[3]
            else:
                connect += [0] * (nMaxnode_elem - len(connect))
            writeFormat(sc_file, 'd' * (2 + nMaxnode_elem), [i + 1, plies[i]] + connect)
        sc_file.write('\n')
        sc_file.write('\n')

        # Write layer types: [layer_id, mat_id, angle]
        for nlayer_id, nlayer_values in nlayers.items():
            writeFormat(sc_file, 'ddE', [nlayer_id, nlayer_values[0], float(nlayer_values[1])])
        sc_file.write('\n')

        writeMaterials(matDict, analysis, model_name, sc_file)

        sc_file.write('\n')
        sc_file.write('\n')
        writeFormat(sc_file, 'E', [w])

    return [swiftcomp_filename + '.sc', macro_model_dimension]
