# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from utilities import *
import os
from userDataSG import *

def _get_sc_dim_sub(sc_path):
    import re
    def _noncomment_lines(path):
        with open(path, 'r') as f:
            for line in f:
                s=line.strip()
                if s and not s.startswith('#'):
                    yield s
    lines=list(_noncomment_lines(sc_path))
    if not lines:
        return ("3D","Solid")
    def _is_int(t):
        try: int(t); return True
        except Exception: return False
    toks=re.split(r'\s+', lines[0])
    if not toks or not _is_int(toks[0]) or int(toks[0]) not in (0,1,2,3):
        return ("3D","Solid")
    mflag=int(toks[0])
    def _count_reals(s):
        count = 0
        for token in re.split(r'\s+', s):
            if not token:
                continue
            try:
                float(token)
                count += 1
            except ValueError:
                pass
        return count
    n2=_count_reals(lines[1]) if len(lines)>1 else 0
    n3=_count_reals(lines[2]) if len(lines)>2 else 0
    if n2==3 and n3>=2:
        dim="1D"
        sub={0:"Euler",1:"Timoshenko",2:"Vlasov",3:"Trapeze"}.get(mflag,"Unknown")
    elif n2==2:
        dim="2D"
        sub={0:"Kirchhoff",1:"Mindlin"}.get(mflag,"Unknown")
    else:
        dim,sub="3D","Solid"
    return (dim, sub)

def sgmodel_info(sgmodel_source, sg_name, sc_input,  analysis, macro_model, ap_flag):

    if sgmodel_source == 1:  # sgmodel_source==1: sg_name;   sgmodel_source==2: sc_input file path and name
            
        SCfileName  = sg_name
        scinput     = mdb.customData.sgs[sg_name].swiftcomp_filename
        currentpath = os.getcwd()
        sc_input    = os.path.join(currentpath, scinput)
        
        if debug == 1:
            print('\n')
            print(('--->sc_input corresponding to the sg model is  %s' % sc_input))
            print('\n')
            
    elif sgmodel_source == 2:
        sc_input    = os.path.normpath(sc_input)
        scpath      = os.path.dirname(sc_input)
        currentpath = os.getcwd()
        if debug == 1:
            print('\n')
            print('when sgmodel_source == 2: ') 
            print('sc_input %s chosen in dialog box: ' % scpath)
            print('scpath = os.path.dirname(sc_input) : %s' % scpath)
            print('currentpath = os.getcwd() : %s' % currentpath)
            print('\n')
        temp_name  = os.path.basename(sc_input)
        temp_name  = temp_name.split('.')
        SCfileName = temp_name[0]
        if scpath != currentpath:
            raise ValueError('File %s.sc is at %s, \n the work directory is %s. \n File %s.sc and the homogenization output files should be in the work directory.' %(SCfileName, scpath, currentpath, SCfileName))
            return
        
        if debug == 1:
            print('\n')
            print('---> sc_input selected is %s ' % sc_input)
            print('\n')
        
    if sgmodel_source == 1:
        sg                    = mdb.customData.sgs[sg_name]
        analysis              = sg.analysis
        macro_model_dimension = sg.macro_model_dimension
        macro_model           = int(macro_model_dimension.strip('D'))
        if hasattr(sg, 'apstr'):
            apstr             = sg.apstr
            if apstr == 'pbc':
                ap_flag           = False
            else:
                ap_flag           = True
    elif sgmodel_source == 2:
        macro_model_dimension = str(macro_model) + 'D'
        
    
    sc_dim, sc_sub = _get_sc_dim_sub(sc_input)
    return SCfileName, sc_input, analysis, macro_model, macro_model_dimension, ap_flag, sc_dim, sc_sub
