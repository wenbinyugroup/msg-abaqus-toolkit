# -*- coding: utf-8 -*-

from abaqusConstants import *
from abaqus import *
from customKernel import CommandRegister, RegisteredList , RegisteredTuple#, RepositorySupport
from main.UdetermineNSG import determineNSG
import textRepr as tr
import os
from utils.utilities import info

class Sg(CommandRegister):
    
    def __init__(self, name):
        
        CommandRegister.__init__(self)
        
    def createSg(self, model_source,model_name, part_name,abaqus_input, swiftcomp_filename,
                 macro_model_dimension, w, analysis, elem_flag, trans_flag, temp_flag,
                 specific_model, 
                 bk, cos,
                 sk,
                 apstr='pbc'):
        
        if model_source == 1:
            
            self.modelfromSource = 'fromCAE'
            self.part_name       = part_name
            self.model_name      = model_name
            self.nSG             = determineNSG(model_name,part_name)
            
        elif model_source == 2:
            self.modelfromSource = 'fromInputfile'
            self.abaqus_input    = abaqus_input
        
        self.swiftcomp_filename    = swiftcomp_filename+'.sc'
        self.macro_model_dimension = macro_model_dimension
        self.volume                = w
        self.analysis              = analysis
        self.elem_flag             = elem_flag
        self.trans_flag            = trans_flag
        self.temp_flag             = temp_flag
        self.apstr                 = apstr
        
        if macro_model_dimension == '1D':
            self.specific_model     = specific_model
            self.bk                 = bk
            self.initialObliqueness = cos
            
        elif macro_model_dimension == '2D':
            self.specific_model = specific_model
            self.sk             = sk
        
        return

            
class SgDehomoData(CommandRegister):
    
    def __init__(self, name):
        
        CommandRegister.__init__(self)
        
    def createSgDehomoData(self, debug, sgmodel_source, sg_name, sc_input, 
                           analysis, macro_model, macro_displacement, 
                           macro_rotation, beam_strain, shell_strain, 
                           solid_strain, tm=0.0,
                           load_measure=1,
                           beam_model="Euler",
                           shell_model="Kirchhoff"):
        
        if sgmodel_source == 1:
            self.sgmodel_source = 'fromSGmodel'
            self.sg_name        = sg_name
            try: 
                sg                         = mdb.customData.sgs[sg_name]
                self.macro_model_dimension = sg.macro_model_dimension
                self.analysis              = sg.analysis
            except Exception:
                raise ValueError('Check and update the data in sg[\' %s \']' % sg_name)
                
        elif sgmodel_source == 2:
            self.sgmodel_source = 'fromSwiftCompInputFile'
            path                = os.path.dirname(sc_input)
            
            if debug == 1:
                print ('in userDataSG, initailly: sc_input= %s' % sc_input)
                print ('in userDataSG, path= %s' % path)
            temp_name   = os.path.basename(sc_input)
            temp_name   = temp_name.split('.')
            sc_filename = temp_name[0]
            if debug == 1:
                print ('in userDataSG, sgdehomo, self.sc_filename= %s' % sc_filename)
            self.sc_filepath = path
            self.sc_filename = sc_filename
            
            self.macro_model_dimension = str(macro_model) + 'D'
            self.analysis              = analysis
            
        self.macro_displacement = macro_displacement # RegisteredTuple(macro_displacement)
        self.macro_rotation     = macro_rotation     # RegisteredTuple(macro_rotation)
        self.load_measure       = load_measure       # 0: stress, 1: strain
        macro_model_dimension   = self.macro_model_dimension
        if macro_model_dimension == '1D':
            self.macro_strain = beam_strain          # RegisteredTuple(beam_strain) or stress resultants slots
            self.beam_model   = beam_model
        elif macro_model_dimension == '2D':
            self.macro_strain = shell_strain         # RegisteredTuple(shell_strain) or stress resultants slots
            self.shell_model  = shell_model
        elif macro_model_dimension == '3D':
            self.macro_strain = solid_strain         # RegisteredTuple(solid_strain) or stress components
        
        if self.analysis == 1:
            self.temperature_increment = tm
            
        return
    
def register_sg_in_mdb(
    sg_name, model_source, model_name, part_name, abaqus_input,
    swiftcomp_filename, macro_model_dimension, w, analysis, elem_flag,
    trans_flag, temp_flag, specific_model, bk, cos, sk, apstr='pbc'
):
    """Create and register an SG model in mdb.customData.

    Parameters
    ----------
    sg_name : str
        Key under which the SG is stored in ``mdb.customData.sgs``.
    model_source : int
        ``1`` for CAE model, ``2`` for input file.
    model_name : str
        Abaqus model name (used when ``model_source == 1``).
    part_name : str
        Abaqus part name (used when ``model_source == 1``).
    abaqus_input : str
        Path to Abaqus input file (used when ``model_source == 2``).
    swiftcomp_filename : str
        SwiftComp input filename without extension.
    macro_model_dimension : str
        ``'1D'``, ``'2D'``, or ``'3D'``.
    w : float
        SG volume/area/length.
    analysis : int
        Analysis type flag.
    elem_flag : int
        Element flag.
    trans_flag : int
        Transformation flag.
    temp_flag : int
        Thermal flag.
    specific_model : int
        Specific beam/shell sub-model flag.
    bk : list[float]
        Beam curvature vector (used for 1D macro model).
    cos : list[float]
        Initial obliqueness vector (used for 1D macro model).
    sk : list[float]
        Shell curvature vector (used for 2D macro model).
    apstr : str, optional
        Anti-periodicity string, default ``'pbc'``.

    Returns
    -------
    Sg
        The newly created SG model object.
    """
    mdb.customData.Repository('sgs', Sg)
    sg = mdb.customData.Sg(name=sg_name)
    sg.createSg(
        model_source, model_name, part_name, abaqus_input, swiftcomp_filename,
        macro_model_dimension, w, analysis, elem_flag, trans_flag, temp_flag,
        specific_model, bk, cos, sk, apstr,
    )
    if info == 1:
        print('--> Create sg model: %s' % sg_name)
        print('    mdb.customData.sgs[\'%s\']' % sg_name)
        tr.prettyPrint(sg, 2)
        print('------------------------------')
    return sg


mdb.customData.Repository('sgs', Sg)
mdb.customData.Repository('sgDehomoDataSets', SgDehomoData)


