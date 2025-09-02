# -*- coding: utf-8 -*-

from abaqusGui import *
import scLocalDB
import importlib
if importlib.sys.version_info.major < 3:
    importlib.reload = reload


###########################################################################
# Class definition
###########################################################################

class LocalForm(AFXForm):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, owner):

        AFXForm.__init__(self, owner)
        self.radioButtonGroups = {}

        self.cmd = AFXGuiCommand(
            mode=self, method='localization',
            objectName='scLocalMain', registerQuery=False)

        # ----- Source selection & file/model fields
        self.sgmodel_sourceKw = AFXIntKeyword(self.cmd, 'sgmodel_source', True, 2)  # 1=CAE, 2=SC
        self.sg_nameKw       = AFXStringKeyword(self.cmd, 'sg_name', True)
        self.sc_inputKw      = AFXStringKeyword(self.cmd, 'sc_input', True, '')
        self.ap_flagKw       = AFXBoolKeyword(self.cmd, 'ap_flag', AFXBoolKeyword.TRUE_FALSE, True, False)

        # For SC-input mode only (UI decides visibility; values passed to backend)
        self.macro_modelKw = AFXIntKeyword(self.cmd, 'macro_model', True, 3, evalExpression=False)  # 1,2,3
        self.analysisKw    = AFXIntKeyword(self.cmd, 'analysis',    True, 0, evalExpression=False)

        # Model sub-options (used only when 1D/2D is chosen in SC mode)
        self.beam_modelKw  = AFXStringKeyword(self.cmd, 'beam_model',  True, 'Euler')      # Euler / Timoshenko
        self.shell_modelKw = AFXStringKeyword(self.cmd, 'shell_model', True, 'Kirchhoff')  # Kirchhoff / Mindlin

        # Generalized strain/stress selector (0=stress, 1=strain)
        self.load_measureKw = AFXIntKeyword(self.cmd, 'load_measure', True, 1, evalExpression=False)

        # Displacements (3) and Rotations (3x3)
        self.vKw = AFXTableKeyword(self.cmd, 'v', True)
        self.vKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.vKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.vKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.vKw.setRow(0, '0.0, 0.0, 0.0')

        self.cKw = AFXTableKeyword(self.cmd, 'c', True)
        self.cKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.cKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.cKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.cKw.setRow(0, '1.0, 0.0, 0.0')
        self.cKw.setRow(1, '0.0, 1.0, 0.0')
        self.cKw.setRow(2, '0.0, 0.0, 1.0')

        # Generalized quantities (tables are reused across views)
        # 1D: be (ε11 or F1 [+ γ12 γ13 for Timo strain / F2 F3 for stress]), bk (κ11 κ12 κ13 or M1 M2 M3)
        self.beKw = AFXTableKeyword(self.cmd, 'be', True)
        self.beKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.beKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.beKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.beKw.setRow(0, '0.0, 0.0, 0.0')

        self.bkKw = AFXTableKeyword(self.cmd, 'bk', True)
        self.bkKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.bkKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.bkKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.bkKw.setRow(0, '0.0, 0.0, 0.0')

        # 2D: se (membrane 3), sk (bending 3), es reused for Mindlin extra pair or 3D shear triplet
        self.seKw = AFXTableKeyword(self.cmd, 'se', True)
        self.seKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.seKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.seKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.seKw.setRow(0, '0.0, 0.0, 0.0')

        self.skKw = AFXTableKeyword(self.cmd, 'sk', True)
        self.skKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.skKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.skKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.skKw.setRow(0, '0.0, 0.0, 0.0')

        # 3D: en (normal 3), es (shear 3). For Mindlin extra (N13,N23 or γ13,γ23) we still pass through esKw’s first two entries.
        self.enKw = AFXTableKeyword(self.cmd, 'en', True)
        self.enKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.enKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.enKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.enKw.setRow(0, '0.0, 0.0, 0.0')

        self.esKw = AFXTableKeyword(self.cmd, 'es', True)
        self.esKw.setColumnType(0, AFXTABLE_TYPE_FLOAT)
        self.esKw.setColumnType(1, AFXTABLE_TYPE_FLOAT)
        self.esKw.setColumnType(2, AFXTABLE_TYPE_FLOAT)
        self.esKw.setRow(0, '0.0, 0.0, 0.0')

        # Temperature increment (used for thermal analyses)
        self.tmKw = AFXFloatKeyword(self.cmd, 'tm', True, 0.0)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getFirstDialog(self):
        importlib.reload(scLocalDB)
        return scLocalDB.LocalDB(self)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def doCustomChecks(self):
        for kw1, kw2, d in list(self.radioButtonGroups.values()):
            try:
                value = d[kw1.getValue()]
                kw2.setValue(value)
            except:
                pass
        return True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def okToCancel(self):
        return False
