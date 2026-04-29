# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from textRepr import *
from caeModules import *
from math import *

from utils.utilities import *


# ==============================================================================
#
#   Composite Layups
#
# ==============================================================================

def abaLayupGenerate(model_name_abq, part_name,layup_abq, element_type):

    cv = abv.current_viewport()
    
    model_name = model_name_abq

    model = mdb.models[model_name]
    part  = model.parts[part_name]
    abv.set_displayed_object(part, vp=cv)
    
    set_name = 'Set_layup'
    
    layup_name_inuse = layup_abq

    if element_type == 'five-noded':
        abaEle_edge = 4
    elif element_type == 'four-noded':
        abaEle_edge = 3
    elif element_type == 'three-noded':
        abaEle_edge = 2
    elif element_type == 'two-noded':
        abaEle_edge = 1
    else:
        raise ValueError('Unknown elem_type: %s' % element_type)
    
    plies_sc = {}
    ply_id_sc = 0
    
    layup_abq = part.compositeLayups[layup_name_inuse]
    for i in range(len(layup_abq.plies)):
        if layup_abq.plies[i].suppressed == False:    # construct plies_sc  {'ply_id_sc':}
            plies_sc[ply_id_sc] = layup_abq.plies[i]  #  the key of plies_sc[ply_id_sc] begin at 0 .
            ply_id_sc = ply_id_sc + 1
    
    n_ply = len(plies_sc)
    
    layup_t = []
    t_total = 0.0
    
    for ply_id in range(n_ply):
        ply_t = plies_sc[ply_id].thickness
        t_total = t_total + ply_t
        layup_t.append(ply_t)
    
    ep = []
    sp = []
    ep_i = 0
    for i in range(n_ply):
        ep_i = layup_t[i] + ep_i
        ep.append(ep_i - t_total/2)
        sp.append(ep_i - t_total/2 - layup_t[i])
    
    #--------------------------------------------------
    # create 3D beam model
    #
    #
    p = mdb.models[model_name].parts[part_name]
    wire_key = list(p.features.keys())[-1]
    s1 = p.features[wire_key].sketch
    mdb.models[model_name].ConstrainedSketch(name='__edit__', objectToCopy=s1)
    s2 = mdb.models[model_name].sketches['__edit__']
    g, v, d, c = s2.geometry, s2.vertices, s2.dimensions, s2.constraints
    s2.setPrimaryObject(option=SUPERIMPOSE)
    p.projectReferencesOntoSketch(sketch=s2, upToFeature=p.features[wire_key], 
        filter=COPLANAR_EDGES)
    t5 = list(g.values())    
    s2.delete(objectList=tuple(t5))
    
    for i in range(len(layup_t)):
        s2.Line(point1=(0., sp[i]), point2=(0., ep[i]))
    
    s2.unsetPrimaryObject()
    p = mdb.models[model_name].parts[part_name]
    p.features[wire_key].setValues(sketch=s2)
    del mdb.models[model_name].sketches['__edit__']
    p = mdb.models[model_name].parts[part_name]
    p.regenerate()
    
    p = mdb.models[model_name].parts[part_name]
    e = p.edges

    p.Set(edges=e, name=set_name)

    #-----------------------------------
    # mesh
    #
    e = p.edges
    p.seedEdgeByNumber(edges=e, number=abaEle_edge, constraint=FINER)
    p.generateMesh()

    # setYZview()
    uab.setViewYZ(nsg=1, obj=p)

    return 1

