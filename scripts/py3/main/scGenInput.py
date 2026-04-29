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
import time
import math
from utils.utilities import *
from main.UwriteMaterials import *
from main.userDataSG import *

def generateInputFromCAE(model_source, macro_model_dimension, analysis, elem_flag, trans_flag,
                         w, nSG, model_name, part_name, abaqus_input, new_filename, 
                         specific_model, bk, 
                         sk, cos, 
                         temp_flag, apvector, nlayer=0):

    startTime = time.perf_counter()

    model    = mdb.models[model_name]
    part     = model.parts[part_name]
    nodes    = part.nodes
    elements = part.elements

    # reject composite/elemental orientations in CAE path
    has_comp = False
    try:
        for _nm,_ly in part.compositeLayups.items():
            if not _ly.suppressed:
                has_comp = True
                break
    except Exception:
        pass
    has_orient = False
    try:
        if len(part.orientations.keys()) > 0:
            has_orient = True
    except Exception:
        pass
    if has_comp or has_orient:
        raise ValueError("Composite layup or elemental orientation detected. CAE files do not contain elemental orientations for each element. Please write input and use the input file to run SwiftComp.")

    if nSG == 2:
        nMaxnode_elem  = 9
        nodeinfoFormat = strFormat('dFF')
        eleminfoFormat = eleFormat('dd','d'*9)
    elif nSG == 3:
        nMaxnode_elem  = 20
        nodeinfoFormat = strFormat('dFFF')
        eleminfoFormat = eleFormat('dd','d'*20)

    #### start to write
    if new_filename == '':
        swiftcomp_filename = part_name + '_nSG' + str(nSG) + '_' + macro_model_dimension + '_' + str(elements[0].type)
    else:
        swiftcomp_filename = new_filename
    
    print(apvector)
    
    if apvector == [0,0,0]:
        apstr = 'pbc'
    else:
        apstr = ''.join(map(str, apvector))
        apstr = 'MIX'+apstr
    swiftcomp_filename = swiftcomp_filename + apstr
    
    mdb.customData.Repository('sgs', Sg)
    sg_name = swiftcomp_filename
    
    sg = mdb.customData.Sg(name = sg_name)
    sg.createSg(model_source, model_name, part_name, abaqus_input, swiftcomp_filename,
                macro_model_dimension, w, analysis, elem_flag, trans_flag, temp_flag,
                specific_model, 
                bk, cos,
                sk, 
                apstr)
    if info == 1:
        print('--> Create sg model: %s' % sg_name)
        print('    mdb.customData.sgs[\'%s\']' % sg_name)
        prettyPrint(sg, 2)
        print('------------------------------')
    
    print(swiftcomp_filename + '.sc')
    with open(swiftcomp_filename + '.sc', 'w') as file:
        if macro_model_dimension != '3D':
            writeFormat(file, 'd', [specific_model])
            file.write('\n')
        
        if macro_model_dimension == '2D':
            writeFormat(file, 'EE', sk)
            file.write('\n')
        elif macro_model_dimension == '1D':
            writeFormat(file, 'EEE', bk)
            file.write('\n')
            writeFormat(file, 'EE', cos)
            file.write('\n')  
            
        writeFormat(file, 'd'*4, [analysis, elem_flag, trans_flag, temp_flag])
        file.write('\n')
        
        if apvector != [0,0,0]:
            writeFormat(file, 'ddd', [apvector[0], apvector[1], apvector[2]])
            file.write('\n')
        
        nnode = len(nodes)
        nelem = len(elements)
        
        # materials from section assignments (isotropic only in CAE path)
        matDict = {}
        matSections = part.sectionAssignments
        for sec in matSections:
            if sec.suppressed == False:
                secName = sec.sectionName
                mname   = model.sections[secName].material
                if mname not in matDict:
                    matDict[mname] = len(matDict) + 1

        checkMaterials(matDict, analysis, model_name)
                    
        nmate  = len(matDict)
        nslave = 0
        nlayer = 0
        
        #Material control parameters
        ntemp = 1
        temperature = 0
        
        writeFormat(file, 'd'*6, [nSG, nnode, nelem, nmate, nslave, nlayer])
        file.write('\n')
            
        # write node info
        #==============================================================================
        nodeStartTime = time.perf_counter()

        if nSG == 3:
            for i in range(0, nnode):
                ndCoords = nodes[i].coordinates
                file.write(nodeinfoFormat.format([nodes[i].label, ndCoords[0], ndCoords[1], ndCoords[2]]))
        elif nSG == 2:    
            for i in range(0, nnode):
                ndCoords = nodes[i].coordinates    
                file.write(nodeinfoFormat.format([nodes[i].label, ndCoords[1], ndCoords[2]]))
                 
        nodeEndTime   = time.perf_counter()
        writeNodetime = nodeEndTime - nodeStartTime
        
        file.write('\n')    
        #==============================================================================
        
        elemStartTime = time.perf_counter()

        labellist   = []
        matIDlist   = []
        connectlist = []
        
        for sec in matSections:
            if sec.suppressed:
                continue
            regionName = sec.region[0]
            secName    = sec.sectionName
            mid = matDict[model.sections[secName].material]
            setElem = part.sets[regionName].elements
            for elem in setElem:
                labellist.append(elem.label)
                matIDlist.append(mid)
                conn = list(elem.connectivity)
                n_connect = len(conn)
                if nSG == 3:
                    out = [nodes[n].label for n in conn]
                    et  = str(elem.type).upper()
                    if et.startswith('C3D15') and n_connect == 15:
                        out.insert(6, 0)
                    elif n_connect == 10:
                        out.insert(4, 0)
                    out += [0]*(nMaxnode_elem - len(out))
                    connectlist.append(out)
                elif nSG == 2:
                    out = [nodes[n].label for n in conn]
                    if n_connect == 6:
                        out.insert(3, 0)
                    out += [0]*(nMaxnode_elem - len(out))
                    connectlist.append(out)
                    
        combinedList = list(zip(labellist, matIDlist, connectlist))
        combinedList.sort()
        for elem_info in combinedList:
            file.write(eleminfoFormat.format(elem_info))
        
        elemEndTime   = time.perf_counter()
        writeElemtime = elemEndTime - elemStartTime

        file.write('\n')
        
        writeMaterials(matDict, analysis, model_name, file)
        
        file.write('{0:16.6E}'.format(w))
        file.write('\n')
        file.write('\n')        
    endTime       = time.perf_counter()
    timeWritefile = endTime - startTime
    
    swiftcomp_filename += '.sc'
    
    return [swiftcomp_filename, macro_model_dimension]


