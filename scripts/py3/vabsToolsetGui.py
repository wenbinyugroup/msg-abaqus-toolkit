# -*- coding: utf-8 -*-

# ******************************************************************************
# This script creates a persistent toolset (toolbox buttons next to the viewport)
# which will remain visible no matter which module it in
# ******************************************************************************

from abaqusGui import *
from sessionGui import CanvasToolsetGui
from forms.workplaneV5Form import WorkplaneV5Form
from forms.layupsForm import LayupsForm
from forms.sG1D_v3Form import SG1D_v3Form
from forms.sG2DV5Form import SG2DV5Form
from forms.sg2DLaminateForm import SG2DLaminateForm
from forms.sg2DLaminateEraseForm import SG2DLaminateEraseForm
from forms.sg2DReadFileForm import SG2DReadFileForm
from forms.node9Form import Node9Form
from forms.sG3DV5Form import SG3DV5Form
from forms.scHomoForm import HomoForm
from forms.scMacroForm import MacroForm
from forms.scLocalForm import LocalForm
# from forms.scVisualForm import VisualForm
from forms.vabsForm import VabsForm
from forms.vabsVisualForm import VisualForm
import os

thisPath = os.path.abspath(__file__)
thisDir = os.path.dirname(thisPath)
thisDir = os.path.join(thisDir, 'Icon')

class VABSToolsetGui(AFXToolsetGui):
    
    [
        ID_YZview,
        ID_LAST
    ] = list(range(AFXToolsetGui.ID_LAST, AFXToolsetGui.ID_LAST + 2))

    def __init__(self):

        # Construct base class.
        AFXToolsetGui.__init__(self, 'VABS')

        # Toolbox buttons
        toolbar_group_1 = AFXToolbarGroup(self, title='VABS Toolset')

        ic = afxCreateIcon(os.path.join(thisDir, 'sc_wp_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tSet sketch plane for 1D/2D customized SG', 
                      icon  = ic, 
                      tgt   = WorkplaneV5Form(self), 
                      sel   = AFXMode.ID_ACTIVATE)
                      
        ic = afxCreateIcon(os.path.join(thisDir, 'view_yz_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tApply YZ view', 
                      icon  = ic, 
                      tgt   = self, 
                      sel   = self.ID_YZview)
        FXMAPFUNC(self, SEL_COMMAND, self.ID_YZview, VABSToolsetGui.setYZview)

        ic = afxCreateIcon(os.path.join(thisDir, 'add_layups_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tNew layups', 
                      icon  = ic, 
                      tgt   = LayupsForm(self), 
                      sel   = AFXMode.ID_ACTIVATE)

        # FXVerticalSeparator(p=toolbar_group_1, x=0, y=0, w=0, h=0, pl=2, pr=2, pt=2, pb=2)

        # ic = afxCreateIcon(os.path.join(thisDir, 'sg_1d_small.png'))
        # AFXToolButton(p     = toolbar_group_1, 
        #               label = '\tCreate 1D SG', 
        #               icon  = ic, 
        #               tgt   = SG1D_v3Form(self), 
        #               sel   = AFXMode.ID_ACTIVATE)

        FXVerticalSeparator(p=toolbar_group_1, x=0, y=0, w=0, h=0, pl=2, pr=2, pt=2, pb=2)

        # ic = afxCreateIcon(os.path.join(thisDir, 'sg_2d_uc_small.png'))
        # AFXToolButton(p     = toolbar_group_1, 
        #               label = '\tCreate 2D SG: Unit cell', 
        #               icon  = ic, 
        #               tgt   = SG2DV5Form(self), 
        #               sel   = AFXMode.ID_ACTIVATE)

        ic = afxCreateIcon(os.path.join(thisDir, 'sg_2d_laminate_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tCreate 2D SG: Assign layups', 
                      icon  = ic, 
                      tgt   = SG2DLaminateForm(self), 
                      sel   = AFXMode.ID_ACTIVATE)
        
        ic = afxCreateIcon(os.path.join(thisDir, 'sg_2d_laminate_erase_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tCreate 2D SG: Erase layups', 
                      icon  = ic, 
                      tgt   = SG2DLaminateEraseForm(self), 
                      sel   = AFXMode.ID_ACTIVATE)
        
        ic = afxCreateIcon(os.path.join(thisDir, 'sg_2d_file_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tCreate 2D SG: Read file', 
                      icon  = ic, 
                      tgt   = SG2DReadFileForm(self), 
                      sel   = AFXMode.ID_ACTIVATE)
                      
        ic = afxCreateIcon(os.path.join(thisDir, 'node_9_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tGenerate 9-node 2D elements', 
                      icon  = ic, 
                      tgt   = Node9Form(self), 
                      sel   = AFXMode.ID_ACTIVATE)
        
        # FXVerticalSeparator(p=toolbar_group_1, x=0, y=0, w=0, h=0, pl=2, pr=2, pt=2, pb=2)

        # ic = afxCreateIcon(os.path.join(thisDir, 'sg_3d_small.png'))
        # AFXToolButton(p     = toolbar_group_1, 
        #               label = '\tCreate 3D SG', 
        #               icon  = ic, 
        #               tgt   = SG3DV5Form(self), 
        #               sel   = AFXMode.ID_ACTIVATE)

        FXVerticalSeparator(p=toolbar_group_1, x=0, y=0, w=0, h=0, pl=2, pr=2, pt=2, pb=2)

        # ic = afxCreateIcon(os.path.join(thisDir, 'sc_homo_small.png'))
        # AFXToolButton(p     = toolbar_group_1, 
        #               label = '\tHomogenization', 
        #               icon  = ic, 
        #               tgt   = HomoForm(self), 
        #               sel   = AFXMode.ID_ACTIVATE)
        
        # ic = afxCreateIcon(os.path.join(thisDir, 'sc_import_k_small.png'))
        # AFXToolButton(p     = toolbar_group_1, 
        #               label = '\tImport homogenized properties', 
        #               icon  = ic, 
        #               tgt   = MacroForm(self), 
        #               sel   = AFXMode.ID_ACTIVATE)

        # ic = afxCreateIcon(os.path.join(thisDir, 'sc_dehomo_small.png'))
        # AFXToolButton(p     = toolbar_group_1, 
        #               label = '\tDehomogenization', 
        #               icon  = ic, 
        #               tgt   = LocalForm(self), 
        #               sel   = AFXMode.ID_ACTIVATE)
        
        ic = afxCreateIcon(os.path.join(thisDir, 'vabs_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tVABS', 
                      icon  = ic, 
                      tgt   = VabsForm(self), 
                      sel   = AFXMode.ID_ACTIVATE)

        ic = afxCreateIcon(os.path.join(thisDir, 'sc_visual_small.png'))
        AFXToolButton(p     = toolbar_group_1, 
                      label = '\tVisualization', 
                      icon  = ic, 
                      tgt   = VisualForm(self), 
                      sel   = AFXMode.ID_ACTIVATE)
                      
        # FXVerticalSeparator(p=toolbar_group_1, x=0, y=0, w=0, h=0, pl=2, pr=2, pt=2, pb=2)
        
        

    def getKernelInitializationCommand(self):
        
        h = 'from main import'
        h += ' userDataSG, scHomoMain, scMacroMat, scLocalMain'
        h += ', scVisualMain, workplaneMain, layupsMain'
        h += ', sg1DMain, sg2DV5Main, sg2DLaminateMain'
        h += ', sg2DLaminateErase, sg2DReadFileMain, node9, sg3DV5Main'
        h += ', vabsMain, vabsVisualMain'

        return h
        
    def setYZview(self, sender, sel, ptr):
        
        cmd = 'session.viewports[session.currentViewportName]'
        cmd += '.view.setViewpoint(viewVector = (1, 0, 0), cameraUpVector = (0, 0, 1))'
        sendCommand(cmd)
        
        return 1
        


