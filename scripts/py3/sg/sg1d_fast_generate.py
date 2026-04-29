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
#   Fast Generate
#
# ==============================================================================

def fastGenerate1D(layup, thickness, model_name, material_name, offset_ratio, element_type):
    
    cv = abv.current_viewport()
    part_name = 'Laminate'
    partsobj = mdb.models[model_name].parts
    set_name ='Set_layup'
    lamSecName = part_name+'_section'
    
    if element_type=='five-noded':
        abaEle_edge=4
    
    elif element_type=='four-noded':
        abaEle_edge=3
    
    elif element_type=='three-noded':
        abaEle_edge=2
    
    elif element_type=='two-noded':
        abaEle_edge=1
    else:
        raise ValueError('Unknown elem_type: %s' % element_type)
    
    #### get reduced string without '2s'  
    
    model = mdb.models[model_name]
    
    ##
    mid = layup.find(']')
    rr = layup[:mid]            ## truncated string rr
    
    rr = rr.replace('[',' ')
    rr = rr.replace('/',' ')
    rr = rr.replace('\\',' ')
    #--------------
    
    layup_s = rr.split()   ## list of angles
    
    #### get reduced string without '2s'
    qq = layup[mid+1:]
    s_exist = qq.find('s') 
    S_exist = qq.find('S')
    
    if s_exist != -1:
        symm = True        #symmetric
        try:
            times = int(qq.replace('s',''))
        except ValueError:
            times = 1
    elif S_exist != -1:
        symm = True
        try:
            times = int(qq.replace('S',''))
        except ValueError:
            times = 1
    else:
        symm = False
        try:
            times = int(qq)
        except ValueError:
            times = 1
    
    #### get the complete layup
    layup_ori = []
    
    if symm == False:
        layup_ori = layup_s * times
    if symm == True:
        pp = layup_s * times
        layup_ori = pp[:]
        for i in range(len(pp)):
            layup_ori.append(pp[-i-1])
    
    layuplist = list(set(layup_s))        ## distinct angle list
    lay_id = []
    for i in range(len(layup_ori)):
        id = layuplist.index(layup_ori[i]) + 1
        lay_id.append(id)
    
    ## Y-Z transform
    p = mdb.models[model_name].Part(name=part_name, dimensionality=THREE_D, 
        type=DEFORMABLE_BODY)
    p = mdb.models[model_name].parts[part_name]
    
    datumPlaneYZ_id = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0).id
    datumAxisZ_id = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS).id
    
    #---------------------------------------------------
    YZworkPlaneTransform = (0,1,0,   0,0,1,  1,0,0,   0,0,0) #y-z plane
#    YZviewVector = (1.0, 0.0, 0.0)
#    YZcameraUpVector = (0.0, 0.0, 1.0)
    
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
    
    t_total = thickness*len(layup_ori)
    sp = -t_total/2.0
    
    
    for i in range(len(layup_ori)):
        s.Line(point1=(0., sp), point2=(0., sp+thickness))
        sp += thickness
        
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
    
    for i in range(len(layup_ori)):
        compositeLayup.CompositePly(suppressed=False, plyName='Ply-'+str(i+1), region=region1,
                                    material=material_name, thicknessType=SPECIFY_THICKNESS, thickness=thickness,
                                    orientationType=SPECIFY_ORIENT, orientationValue=float(layup_ori[i]),
                                    additionalRotationType=ROTATION_NONE, additionalRotationField='',
                                    axis=AXIS_3, angle=0.0, numIntPoints=3)
        
    uab.setViewYZ(nsg=1, obj=p)
    
    return 1
    
