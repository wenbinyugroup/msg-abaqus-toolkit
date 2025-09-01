# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from scVisualMain import *
from utilities import *
import os
import time
from customKernel import CommandRegister, RegisteredList , RegisteredTuple#, RepositorySupport
from userDataSG import *
from UcheckDehoVisual import *
from Usgmodel_info import *


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
        macro_displacement=tuple(v), macro_roatation=tuple(c),
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



    with open(sc_global, 'w') as fout:
        writeFormat(fout, 'EEE', v)
        fout.write('\n')
        writeFormat(fout, 'EEE', c[0])
        fout.write('\n')
        writeFormat(fout, 'EEE', c[1])
        fout.write('\n')
        writeFormat(fout, 'EEE', c[2])
        fout.write('\n')
        writeFormat(fout, 'd', [load_measure])
        fout.write('\n')

        # Write generalized quantities by dimensional model
        if macro_model_dimension == '1D':
            # be contains [e11, k11, k12, k13] OR for stress [F1, M1, M2, M3] if user entered that order
            fout.write(" ".join(str(float(x)) for x in be) + "\n")
            # For Timoshenko we don't need to force placeholders; GUI provides correct triplets in 'be'
            # and 'bk', already folded above.

        elif macro_model_dimension == '2D':
            # For KL: 6 numbers. For Mindlin: 6 + 2 numbers (extra pair).
            # 'se' already includes membrane (3) + bending (3) after folding se[0] + sk[0].
            if shell_model.lower() in ('mindlin','reissner-mindlin') and len(mindlin_extra) > 0:
                pair = (mindlin_extra + [0.0, 0.0])[:2]
                all_vals = list(se) + list(pair)
                fout.write(" ".join(str(float(x)) for x in all_vals) + "\n")
            else:
                fout.write(" ".join(str(float(x)) for x in se) + "\n")

        elif macro_model_dimension == '3D':
            # 6 numbers for 3D (strain or stress), already folded into 'e'
            fout.write(" ".join(str(float(x)) for x in e) + "\n")

        fout.write('\n')
        if analysis==1:
            writeFormat(fout, 'E', tm)

    #execute dehomogenization
    try:
        if ap_flag==False:
            os.system('Swiftcomp ' + SCfileName + '.sc '+macro_model_dimension+' L')
        else:
            os.system('Swiftcomp ' + SCfileName + '.sc '+macro_model_dimension+' LA')
        cwd = os.getcwd()
#        print cwd
    except:
        return


    #check and wait
    while not os.path.exists(cwd + '\\' + SCfileName + '.sc' + '.u'):
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
