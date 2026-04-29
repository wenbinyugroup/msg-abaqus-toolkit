# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from utils.utilities import *
import os
import time
from customKernel import CommandRegister, RegisteredList , RegisteredTuple#, RepositorySupport
from main.userDataSG import *
from utils.UcheckDehoVisual import *
from main.Usgmodel_info import *


def importSCmat(
        sgmodel_source, sg_name='', sc_input_k='',
        analysis=0, macro_model=3):

    if sgmodel_source == 1:
        sc_input = ''
    if sgmodel_source == 2:
        sc_input = sc_input_k.rsplit('.', 1)[0]

    if analysis == 33:
        analysis = 3
    elif analysis == 44:
        analysis = 4
    result = sgmodel_info(sgmodel_source, sg_name, sc_input,
                          analysis, macro_model,ap_flag=False)
    SCfileName = result[0]
    sc_input = result[1]
    analysis = result[2]
    macro_model = result[3]
    macro_model_dimension = result[4]
    if debug == 1:
        print('sc_input %s' % sc_input)
        print('SCfileName %s' % SCfileName)
    sc_input_sc = os.path.basename(sc_input)
    checkDehoVisual(sc_input_sc, 'm')

    sc_input_k = sc_input + '.k'
    scMat_name = SCfileName  
    model_name = SCfileName
     
    prop_matrix = []
    prop_engi = []
    CTE = []
    sheat = []
    density = 0.0
    print('\n')
    print(('Read homogenized properties from %s.' % sc_input_k)) 
    
    i = 1
    title = None

    with open(sc_input_k, 'r') as fin:
        for line in fin:
            line = line.strip()
    #        print line
    #        print i
            i = i + 1
            if line == '\n' or line == '':
                continue
            else:
                line = line.split()
                if 'Stiffness' in line:
                    title = 'Stiffness'
#                    j=0
                    continue
                elif 'Engineering' in line:
                    title = 'Engineering'
#                    j=0
                    continue
                elif 'Compliance' in line:
                    title = 'Compliance'
#                    j=0
                    continue
                elif 'Thermal' in line:
                    title = 'Thermal'
#                    j=0
                    continue
                elif 'Heat' in line:
                    title = 'Heat'
#                    j=0
                    continue
                elif 'Density' in line:
                    density = float(line[-1])
#                    j=0
                    continue
                
                elif len(line) == 1 and line[0][0] == '-':
#                    j=0
                    continue
                elif title is None:
                    raise ValueError('Unknown section header in %s: %s' % (sc_input_k, ' '.join(line)))
                elif title == 'Stiffness':
    #                print j
                    line = list(map(float, line))
                    prop_matrix.append(line)
#                    j=j+1
                elif title == 'Engineering':
                    prop_engi.append(float(line[-1]))
#                    j=j+1
                elif title == 'Thermal':
                    CTE.append(float(line[-1]))
#                    j=j+1
                elif title == 'Heat':
                    sheat.append(float(line[-1]))
#                    j=j+1
                else:
                    raise ValueError('Unknown section header in %s: %s' % (sc_input_k, title))
    
    if prop_matrix != []:
        if debug == 1:
            print(prop_matrix)
        
        prop_matrix_tuple = (
            prop_matrix[0][0],
            prop_matrix[1][0], prop_matrix[1][1],
            prop_matrix[2][0], prop_matrix[2][1], prop_matrix[2][2],
            prop_matrix[3][0], prop_matrix[3][1], prop_matrix[3][2],
            prop_matrix[3][3],
            prop_matrix[4][0], prop_matrix[4][1], prop_matrix[4][2],
            prop_matrix[4][3], prop_matrix[4][4],
            prop_matrix[5][0], prop_matrix[5][1], prop_matrix[5][2],
            prop_matrix[5][3], prop_matrix[5][4], prop_matrix[5][5])

    if prop_engi != []:
        if debug == 1:
            print(prop_engi)
        prop_engi = [
            prop_engi[0], prop_engi[1], prop_engi[2],
            prop_engi[6], prop_engi[7], prop_engi[8],
            prop_engi[3], prop_engi[4], prop_engi[5]
        ]
        prop_engi_tuple = tuple(prop_engi)
        scMat_name_engi = scMat_name + '_engi'
     
    if CTE != []:
        CTE_tuple = tuple(CTE)
        if debug == 1:
            print(CTE_tuple)
    
    if sheat != []:
        sheat_tuple = tuple(sheat)
        if debug == 1:
            print(sheat_tuple)
    
    if model_name in mdb.models:
        raise ValueError(
            "Model '%s' already exists. Delete or rename it before importing SwiftComp materials."
            % model_name
        )
    mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)
    model = mdb.models[model_name]
    
    if macro_model_dimension == '3D':
        scMat_name_matrix = scMat_name + '_matrix'
        if scMat_name_matrix in model.materials:
            raise ValueError(
                "Material '%s' already exists in model '%s'. Delete or rename it before importing SwiftComp materials."
                % (scMat_name_matrix, model_name)
            )
        model.Material(name=scMat_name_matrix)
        material = model.materials[scMat_name_matrix]
        material.Elastic(type=ANISOTROPIC, table=(prop_matrix_tuple,))
        material.Density(table=((density,),))   
        if CTE != []:
            if len(CTE_tuple) == 1:
                material.Expansion(table=(CTE_tuple,))
            elif len(CTE_tuple) == 3:
                material.Expansion(type=ORTHOTROPIC, table=(CTE_tuple, ))
            elif len(CTE_tuple) == 6:
                material.Expansion(type=ANISOTROPIC, table=(CTE_tuple, ))
        if sheat != []:
            if len(sheat_tuple) == 1:
                material.SpecificHeat(table=(sheat_tuple, ))
    
    #        mdb.models['Model-1'].materials['Material-6'].SpecificHeat(table=((1.0, ), ))
    #        mdb.models['Model-1'].materials['Material-6'].SpecificHeat(
    #            temperatureDependency=ON, table=((1.0, 2.0), (3.0, 4.0)))

        if prop_engi != []:
            if scMat_name_engi in model.materials:
                raise ValueError(
                    "Material '%s' already exists in model '%s'. Delete or rename it before importing SwiftComp materials."
                    % (scMat_name_engi, model_name)
                )
            model.Material(name=scMat_name_engi)
            material = model.materials[scMat_name_engi]
            material.Elastic(type=ENGINEERING_CONSTANTS, table=(prop_engi_tuple, ))
            material.Density(table=((density, ), )) 
            if CTE != []:
                if len(CTE_tuple) == 1:
                    material.Expansion(table=(CTE_tuple, ))
                elif len(CTE_tuple) == 3:
                    material.Expansion(type=ORTHOTROPIC, table=(CTE_tuple, ))
                elif len(CTE_tuple) == 6:
                    material.Expansion(type=ANISOTROPIC, table=(CTE_tuple, ))
            if sheat != []:
                if len(sheat_tuple) == 1:
                    material.SpecificHeat(table=(sheat_tuple, ))
            
    elif macro_model_dimension == '2D':
        model.GeneralStiffnessSection(
            name=scMat_name,
            referenceTemperature=None,
            stiffnessMatrix=prop_matrix_tuple,
            applyThermalStress=0,
            poissonDefinition=DEFAULT,
            useDensity=ON,
            density=density)

    return


