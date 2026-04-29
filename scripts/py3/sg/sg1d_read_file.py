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
#   Read File
#
# ==============================================================================

def fromInputfile1D(file_layup_input, model_name, element_type):

    model = mdb.models[model_name]
    mat_abq = list(model.materials.keys())
    set_name = 'Set_layup'
    cv = abv.current_viewport()
    
    layup_input = file_layup_input.replace('\\','/')
    temp = layup_input.rsplit('/')
    temp = temp[-1]
    part_name = temp.rsplit('.')[0]
    
    if element_type == 'five-noded':
        abaEle_edge = 4
    elif element_type == 'four-noded':
        abaEle_edge = 3
    elif element_type == 'three-noded':
        abaEle_edge = 2
    elif element_type == 'two-noded':
        abaEle_edge = 1

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
    t_total = 0.0
    layup_mat = []
    for ply_id in range(n_ply) :
        ply_t = plies_sc[ply_id][0]
        t_total = t_total + ply_t
        layup_t.append(ply_t)
        layup_ori.append(plies_sc[ply_id][1])
        mat_id = plies_sc[ply_id][2]
        mat_name = mat_dict[mat_id]
        layup_mat.append(mat_name)
    
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
    YZworkPlaneTransform = (0,1,0, 0,0,1, 1,0,0, 0,0,0) #y-z plane
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

