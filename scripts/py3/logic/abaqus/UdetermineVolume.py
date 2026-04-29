# -*- coding: utf-8 -*-

from abaqus import *
# import time

def determineVolume(model_name, part_name, macro_model_dimension, nSG):

    part       = mdb.models[model_name].parts[part_name]
    nodes      = part.nodes
    # WstartTime = time.clock()
    geo_info   = part.queryGeometry()
    
    if geo_info['category'] == 'OrphanMesh':
        nodeX = []
        nodeY = []
        nodeZ = []
        n_coord = []
        for n in range(0, len(nodes)):
            coords = nodes[n].coordinates
            nodeX.append(coords[0])
            nodeY.append(coords[1])
            nodeZ.append(coords[2])
            n_coord.append(coords)
        if not n_coord:
            raise ValueError('Please mesh the part!')
        if all(c[0] == 0 and c[1] == 0 and c[2] == 0 for c in n_coord):
            raise ValueError('Please mesh the part!')
        LX = max(nodeX) - min(nodeX)
        LY = max(nodeY) - min(nodeY)
        LZ = max(nodeZ) - min(nodeZ)
    elif geo_info['category'] == 'Geometry':
        boundbox = geo_info['boundingBox']
        LX = boundbox[1][0] - boundbox[0][0]
        LY = boundbox[1][1] - boundbox[0][1]
        LZ = boundbox[1][2] - boundbox[0][2]
    
    if macro_model_dimension == '3D':
        if nSG == 1:
            volume = LZ
        elif nSG == 2:
            volume = LY * LZ
        elif nSG == 3:
            volume = LX * LY * LZ
    elif macro_model_dimension == '2D':
        if nSG == 3:
            volume = LX * LY
        elif nSG == 2:
            volume = LY
        elif nSG == 1:
            volume = 1
    elif macro_model_dimension == '1D':
        if nSG == 3:
            volume = LX
        elif nSG == 2:
            volume = 1
        elif nSG == 1:
            raise TypeError (' Wire model cannot be used for beam analysis!  ')
    else:
        raise ValueError('Unknown macro_model_dimension: %s' % macro_model_dimension)
    
    # WendTime = time.clock()
    # WTime = WendTime - WstartTime
    #print 'Time for calculate w:  %s' % str(WTime)
    return volume
