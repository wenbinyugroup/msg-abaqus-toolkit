# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from main.scVisualMain import *
from utils.utilities import *
import subprocess
import os
import time
from customKernel import CommandRegister, RegisteredList , RegisteredTuple#, RepositorySupport
from sg.sg_data import *
from utils.UcheckDehoVisual import *
from sgdataio.sgmodel import resolve_sgmodel_info as sgmodel_info
from sgdataio.swiftcomp import write_swiftcomp_glb


def localization(
        sgmodel_source, v, c,
        sg_name='', sc_input='', analysis=0, macro_model=3,
        load_measure=1,
        be='', bk='', se='', sk='', en='', es='',
        sh2='',                    # extra 2 components for Mindlin: γ13 γ23 (strain) or N13 N23 (stress)
        tm=0.0, ap_flag=False,
        beam_model="Euler",        # Euler or Timoshenko (for 1D)
        shell_model="Kirchhoff"    # Kirchhoff or Mindlin (for 2D)
    ):
    """
    Localization analysis for a SG model or a SwiftComp input file.

    Parameters
    ----------
    sgmodel_source : int
        1: from sg model; 2: from sc input file
    v : list
        Macroscopic displacements
    c : list
        Macroscopic roatations
    sg_name : str
        Name of the SG model
    sc_input : str
        Path and name of the SwiftComp input file
    analysis : int
        Analysis type
    macro_model : int
        Macroscopic model type
    load_measure : int
        Load measure. 0: Generalized stress; 1: Generalized strain
    """

    startTime = time.perf_counter()

    if analysis == 33:
        analysis = 3
    elif analysis == 44:
        analysis = 4
    
    # v  = [float(v1), float(v2), float(v3)]
    # c  = [[float(c11), float(c12), float(c13)], 
          # [float(c21), float(c22), float(c23)], 
          # [float(c31), float(c32), float(c33)]]
    # be = [float(b_e11), float(b_k11), float(b_k12), float(b_k13)]
    # se = [float(s_e11),  float(s_e22),float(s_e12x2), float(s_k11),  float(s_k22), float(s_k12k21),]
    # e  = [float(e11), float(e22), float(e33), float(e23x2), float(e13x2), float(e12x2)]
    tm = [float(tm)]
    v = v[0]
    e = ''
    if be != '' and bk != '':
        be = be[0] + bk[0]
    elif se != '' and sk != '':
        se = se[0] + sk[0]
    elif en != '' and es != '':
        e = en[0] + es[0]

    # Handle extra Mindlin pair (γ13, γ23) or (N13, N23).
    # Accept from explicit 'sh2' if provided; otherwise, fall back to es[0][:2] if user entered via es.
    mindlin_extra = []
    if isinstance(sh2, (list, tuple)) and len(sh2) > 0:
        mindlin_extra = list(sh2[0])
    elif isinstance(es, (list, tuple)) and len(es) > 0:
        # If GUI provided γ13, γ23 (or N13, N23) via es for Mindlin, take the first two.
        if isinstance(es[0], (list, tuple)) and len(es[0]) >= 2:
            mindlin_extra = list(es[0][:2])

    mdb.customData.Repository('sgDehomoDataSets', SgDehomoData)
    
    SCfileName, sc_input, analysis,  macro_model, macro_model_dimension, ap_flag, sc_dim, sc_sub = sgmodel_info(
        sgmodel_source=sgmodel_source, sg_name=sg_name, sc_input=sc_input,
        analysis=analysis, macro_model=macro_model, ap_flag=ap_flag)

    dim_ui = {1:"1D", 2:"2D", 3:"3D"}.get(macro_model, str(macro_model))
    sub_ui = ("Solid" if dim_ui=="3D" else (beam_model if dim_ui=="1D" else shell_model))
    if sc_dim != dim_ui or sc_sub != sub_ui:
        raise ValueError("The SwiftComp input file is for %s %s model, but you selected %s %s model."
                         % (sc_dim, sc_sub, dim_ui, sub_ui))
    
#-----------------------------------------------------------
    print(sc_input)
    sgDehomoData_name = SCfileName
    sc_global = sc_input + r'.glb'
    sc_input_sc = os.path.basename(sc_input)
    # Check if there is a odb file with the destination name have already exist:
    checkDehoVisual(sc_input_sc, 'Dehomo')


    
    sgDehomoData = mdb.customData.SgDehomoData(name=sgDehomoData_name)
    sgDehomoData.createSgDehomoData(
        debug, sgmodel_source, sg_name, sc_input, analysis, macro_model,
        macro_displacement=tuple(v), macro_rotation=tuple(c),
        beam_strain=tuple(be), shell_strain=tuple(se), solid_strain=tuple(e), tm=tm,
        beam_model=beam_model)
    if info==1:
        print(('---> Create sgDehomoData: %s' % sg_name))
        print(('    mdb.customData.sgDehomoDataSets[\'%s\']' % sgDehomoData_name))
        prettyPrint(sgDehomoData,3)
        print('------------------------------')


    if info==1:
        print('------------------------------')
        print('SwiftComp input file name')
        print(SCfileName)
        print('Macroscopic displacements')
        print(v)
        print('Macroscopic roatations')
        print(c)
        if macro_model_dimension=='1D':
            print('beam macroscopic strain and curvatures :' if load_measure==1 else 'beam generalized stress resultants :')
            print(be)
            print('Beam model: %s' % beam_model)
        elif macro_model_dimension=='2D':
            print('shell macroscopic strain and curvatures :' if load_measure==1 else 'shell generalized stress resultants :')
            print(se)
            print('Shell model: %s' % shell_model)
            if shell_model.lower() in ('mindlin','reissner-mindlin'):
                print('Mindlin extra pair:')
                print(mindlin_extra)
        elif macro_model_dimension=='3D':
            print('3D solid macroscopic strain :' if load_measure==1 else '3D solid macroscopic stress :')
            print(e)



    write_swiftcomp_glb(
        sc_global=sc_global,
        macro_displacement=v,
        macro_rotation=c,
        load_measure=load_measure,
        macro_model_dimension=macro_model_dimension,
        beam_values=be,
        shell_values=se,
        solid_values=e,
        temperature_increment=tm if analysis == 1 else None,
        shell_model=shell_model,
        mindlin_extra=mindlin_extra,
    )

    #execute dehomogenization
    cwd = os.getcwd()
    cmd = ['Swiftcomp', SCfileName + '.sc', macro_model_dimension]
    if ap_flag==False:
        cmd.append('L')
    else:
        cmd.append('LA')
    result = subprocess.run(cmd, timeout=300, check=False)
    if result.returncode != 0:
        raise RuntimeError('SwiftComp exited with code %d' % result.returncode)


    #check and wait
    sc_output = os.path.join(cwd, SCfileName + '.sc.u')
    deadline = time.time() + 300
    while not os.path.exists(sc_output):
        if time.time() > deadline:
            raise RuntimeError('SwiftComp did not produce output after 300 s')
        time.sleep(1)
    
    endTime = time.perf_counter()

    dehomoTime=endTime-startTime


    VstartTime=time.perf_counter()
    print('before visual')
    visualization(macro_model, ap_flag, sc_input)

    VendTime = time.perf_counter()
    visualTime=VendTime-VstartTime

    print('Dehomogenization time (seconds): %s' % str(dehomoTime))
    print('Odb file creation time: %s' % str(visualTime))

    return


