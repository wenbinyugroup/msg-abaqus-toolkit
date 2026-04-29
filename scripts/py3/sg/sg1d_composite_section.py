# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from textRepr import *
from caeModules import *
from math import *

from utils.utilities import *
from main import utilities_abq as uab
from utils import abq_view as abv


# ==============================================================================
#
#   Composite Sections
#
# ==============================================================================

def abaSection1D(model_name = '', part_name = '', section_name = '', offset_ratio = 0.0, element_type = 'five-noded'):

    model = mdb.models[model_name]
    set_name='Set_layup'
    cv = abv.current_viewport()
    
    if element_type=='five-noded':
        abaEle_edge=4
    elif element_type=='four-noded':
        abaEle_edge=3
    elif element_type=='three-noded':
        abaEle_edge=2
    elif element_type=='two-noded':
        abaEle_edge=1
        
    plies_sc = {}
    n_ply = len(plies_sc)
    layup_t = []
    t_total = 0.0
    layup_ori = []
    layup_mat = []

    layup_sec = model.sections[section_name].layup
    for ply_id in range(len(layup_sec)) :
        plies_sc[ply_id] = layup_sec[ply_id]  #  the key of plies_sc[ply_id_sc] begin at 0 .
        
        ply_t = plies_sc[ply_id].thickness
        t_total = t_total+ply_t
        layup_t.append(ply_t)
        
        ply_ori = plies_sc[ply_id].orientAngle
        layup_ori.append(ply_ori)
        
        ply_mat = plies_sc[ply_id].material
        layup_mat.append(ply_mat) 

    n_ply = len(plies_sc)
        
    ep = []
    sp = []
    ep_i = 0
    for i in range(n_ply):
        ep_i = layup_t[i] + ep_i
        ep.append(ep_i - t_total/2)
        sp.append(ep_i - t_total/2 - layup_t[i])   

    ## Y-Z transform
    p = mdb.models[model_name].Part(name=part_name, dimensionality=THREE_D, 
        type=DEFORMABLE_BODY)
    p = mdb.models[model_name].parts[part_name]
    
    datumPlaneYZ_id = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0).id
    datumAxisZ_id = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS).id
    
    #---------------------------------------------------
    YZworkPlaneTransform = (0,1,0,   0,0,1,  1,0,0,   0,0,0) #y-z plane
    YZviewVector = (1.0, 0.0, 0.0)
    YZcameraUpVector = (0.0, 0.0, 1.0)
    
    #--------------------------------------------------
    # create 3D beam model
    #
    s = mdb.models[model_name].ConstrainedSketch(name='__profile__', 
        sheetSize=200.0,transform=YZworkPlaneTransform)
    
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    abv.set_named_view('Left', vp=cv)
    
    p = mdb.models[model_name].parts[part_name]
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    
    for i in range(len(layup_t)):
        s.Line(point1=(0., sp[i]), point2=(0., ep[i]))
    
    e1, d2 = p.edges, p.datums
    p.Wire(sketchPlane=d2[datumPlaneYZ_id], sketchUpEdge=d2[datumAxisZ_id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s)
    s.unsetPrimaryObject()
    abv.set_displayed_object(p, vp=cv)
    del mdb.models[model_name].sketches['__profile__']    
    
    # mesh
    #
    e = p.edges
    p.seedEdgeByNumber(edges=e, number=abaEle_edge, constraint=FINER)
    p.generateMesh()
    
    p = mdb.models[model_name].parts[part_name]
    e = p.edges
    edges = e
    p.Set(edges=edges, name=set_name)
    
    region1 = p.sets[set_name]
    
    compositeLayup = p.CompositeLayup(
        name='CompositeLayup-1', description='', elementType=SHELL, 
        offsetType=SINGLE_VALUE, offsetValues=(offset_ratio, ), symmetric=False, 
        thicknessAssignment=FROM_SECTION)        
        
    compositeLayup.Section(preIntegrate=OFF, integrationRule=SIMPSON, 
        thicknessType=UNIFORM, poissonDefinition=DEFAULT, temperature=GRADIENT, 
        useDensity=OFF)
    compositeLayup.ReferenceOrientation(orientationType=GLOBAL, localCsys=None, 
        fieldName='', additionalRotationType=ROTATION_NONE, angle=0.0, axis=AXIS_3)
    
    for i in range(n_ply):
        compositeLayup.CompositePly(suppressed=False, plyName='Ply-'+str(i+1), region=region1,
                                    material=layup_mat[i], thicknessType=SPECIFY_THICKNESS, thickness=layup_t[i],
                                    orientationType=SPECIFY_ORIENT, orientationValue=float(layup_ori[i]),
                                    additionalRotationType=ROTATION_NONE, additionalRotationField='',
                                    axis=AXIS_3, angle=0.0, numIntPoints=3)
        
    # setYZview()
    uab.setViewYZ(nsg=1, obj=p)

    return 1
