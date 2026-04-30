# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from utils.utilities import *
import os
import time
from customKernel import CommandRegister, RegisteredList , RegisteredTuple#, RepositorySupport
from sg.sg_data import *
from utils.UcheckDehoVisual import *
from sgdataio.sgmodel import resolve_sgmodel_info as sgmodel_info
from sgdataio.swiftcomp import read_swiftcomp_homogenized_properties


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
     
    print('\n')
    print(('Read homogenized properties from %s.' % sc_input_k)) 
    material_data = read_swiftcomp_homogenized_properties(sc_input_k)
    prop_matrix = material_data['prop_matrix']
    prop_matrix_tuple = material_data['prop_matrix_tuple']
    prop_engi = material_data['prop_engi']
    prop_engi_tuple = material_data['prop_engi_tuple']
    CTE = material_data['cte']
    CTE_tuple = material_data['cte_tuple']
    sheat = material_data['sheat']
    sheat_tuple = material_data['sheat_tuple']
    density = material_data['density']

    if prop_matrix != [] and debug == 1:
        print(prop_matrix)

    if prop_engi != []:
        if debug == 1:
            print(prop_engi)
        scMat_name_engi = scMat_name + '_engi'
     
    if CTE != [] and debug == 1:
        print(CTE_tuple)
    
    if sheat != [] and debug == 1:
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


