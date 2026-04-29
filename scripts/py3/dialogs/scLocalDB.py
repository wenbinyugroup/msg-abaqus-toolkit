# -*- coding: utf-8 -*-

from abaqusGui import *
# from kernelAccess import mdb, session
import os

thisPath = os.path.abspath(__file__)
thisDir  = os.path.dirname(thisPath)

# Show only CAE SGs that have a real .sc in the work directory =====
def _resolve_sc_for_sg(sg, sg_name):
    """Return absolute path to the .sc that should be used for this SG, or None."""
    try:
        cwd = os.getcwd()
        swift = getattr(sg, 'swiftcomp_filename', None)

        # 1) <swiftcomp_filename>.sc in work dir (by basename)
        if swift:
            p = os.path.join(cwd, os.path.basename(swift) + '.sc')
            if os.path.isfile(p):
                return os.path.abspath(p)

        # 2) <sg_name>.sc in work dir
        p2 = os.path.join(cwd, sg_name + '.sc')
        if os.path.isfile(p2):
            return os.path.abspath(p2)
    except Exception:
        pass
    return None

def _valid_cae_sg_names():
    """Return sorted SG names that have a resolvable .sc file in the current work dir."""
    try:
        names = []
        for name, sg in mdb.customData.sgs.items():
            if _resolve_sc_for_sg(sg, name):
                names.append(name)
        return sorted(names)
    except Exception:
        return []
# =========================================================================================

###########################################################################
# Dialog
###########################################################################

class LocalDB(AFXDataDialog):

    def __init__(self, form):

        AFXDataDialog.__init__(
            self, form, 'Dehomogenization',
            self.OK | self.CANCEL, DIALOG_ACTIONS_SEPARATOR
        )

        # Make the window resizable and big enough that OK/Cancel are visible
        try:
            self.setDecorations(self.getDecorations() | DECOR_RESIZE)
        except Exception: pass
        try:
            self.resize(max(self.getDefaultWidth(), 560), 760)
        except Exception: pass

        self.form = form
        colw = 100  # AFXTable column width

        # Remember last error so we don't spam dialogs
        self._last_error_key = None
        self._last_sg_name   = ''  # to detect selection changes
        self._last_source    = None  # to detect CAE/SC switching

        # ---------------- Top controls (non-scrolling) ----------------
        srcGB = FXGroupBox(self, 'SG model source', FRAME_GROOVE | LAYOUT_FILL_X)
        hf    = FXHorizontalFrame(srcGB, 0, 0,0,0,0, 0,0,0,0)
        FXRadioButton(hf, 'CAE',                   self.form.sgmodel_sourceKw, 1)
        FXRadioButton(hf, 'SwiftComp Input file',  self.form.sgmodel_sourceKw, 2)

        self.swt_source = FXSwitcher(self, LAYOUT_FILL_X, 0,0,0,0, 0,0,0,0)

        # ===== CAE PANEL =====
        caeVF = FXVerticalFrame(self.swt_source, FRAME_SUNKEN|FRAME_THICK|LAYOUT_FILL_X)
        caeVF.setSelector(99)

        self.List_sg = AFXList(
            caeVF, nvis=8, tgt=self.form.sg_nameKw, sel=0,
            opts=HSCROLLING_OFF | LIST_SINGLESELECT | LAYOUT_FILL_X
        )

        # CAE: user controls only strain/stress (uses SAME keyword as SC)
        self.ComboBox_measure_cae = AFXComboBox(
            caeVF, ncols=28, nvis=1, text='Generalized strain/stress: ',
            tgt=self.form.load_measureKw, sel=0
        )
        self.ComboBox_measure_cae.setMaxVisible(2)
        self.ComboBox_measure_cae.appendItem('Strain', 1)
        self.ComboBox_measure_cae.appendItem('Stress', 0)

        # Populate CAE list with only SGs that have a real .sc in work dir
        self._refresh_sg_list()
        # --------------------------------------------------------------------------

        # ===== SwiftComp PANEL =====
        scVF  = FXVerticalFrame(self.swt_source)
        align = AFXVerticalAligner(scVF)

        fh = LocalDBFileHandler(self.form, 'sc_input', 'SC Input (*.sc)')
        fileHF = FXHorizontalFrame(align, hs=DEFAULT_SPACING, vs=DEFAULT_SPACING)
        fileHF.setSelector(99)
        AFXTextField(fileHF, 26, 'SwiftComp input file: ',
                     self.form.sc_inputKw, 0, AFXTEXTFIELD_STRING | LAYOUT_CENTER_Y)
        icon = afxGetIcon('fileOpen', AFX_ICON_SMALL)
        FXButton(fileHF, '\tSelect File\nFrom Dialog', icon, fh,
                 AFXMode.ID_ACTIVATE, BUTTON_NORMAL | LAYOUT_CENTER_Y, 0,0,0,0,1,1,1,1)

        # Analysis type
        cb_ana = AFXComboBox(align, 28, 1, 'Analysis type: ', self.form.analysisKw, 0)
        cb_ana.setMaxVisible(10)
        cb_ana.appendItem('Elastic', 0)
        cb_ana.appendItem('ThermoElastic', 1)
        cb_ana.appendItem('Conduction', 2)
        cb_ana.appendItem('PiezoElectric', 3)
        cb_ana.appendItem('PiezoMagnetic', 33)
        cb_ana.appendItem('ThermoPiezoElectric', 4)
        cb_ana.appendItem('ThermoPiezoMagnetic', 44)
        cb_ana.appendItem('PiezoElectroMagnetic', 5)
        cb_ana.appendItem('ThermoPiezoElectroMagnetic', 6)

        # Macro model
        self.cb_macro = AFXComboBox(align, 28, 1, 'Macroscopic model: ', self.form.macro_modelKw, 0)
        self.cb_macro.setMaxVisible(10)
        self.cb_macro.appendItem('1D (Beam)', 1)
        self.cb_macro.appendItem('2D (Shell)', 2)
        self.cb_macro.appendItem('3D (Solid)', 3)

        # Measure (same keyword as CAE)
        self.cb_measure_sc = AFXComboBox(
            align, 28, 1, 'Generalized strain/stress: ', self.form.load_measureKw, 0)
        self.cb_measure_sc.setMaxVisible(2)
        self.cb_measure_sc.appendItem('Strain', 1)
        self.cb_measure_sc.appendItem('Stress', 0)

        # Beam/Shell type rows (SwiftComp only; CAE deduces automatically)
        self.beamRow  = FXHorizontalFrame(align);  self.beamRow.hide()
        self.cb_beam  = AFXComboBox(self.beamRow, 28, 1, 'Beam model: ', self.form.beam_modelKw, 0)
        self.cb_beam.setMaxVisible(2)
        self.cb_beam.appendItem('Euler', 1)
        self.cb_beam.appendItem('Timoshenko', 2)

        self.shellRow = FXHorizontalFrame(align);  self.shellRow.hide()
        self.cb_shell = AFXComboBox(self.shellRow, 28, 1, 'Shell model: ', self.form.shell_modelKw, 0)
        self.cb_shell.setMaxVisible(2)
        self.cb_shell.appendItem('Kirchhoff', 1)
        self.cb_shell.appendItem('Mindlin',  2)

        FXCheckButton(scVF, 'Aperiodic', self.form.ap_flagKw, 0)

        FXHorizontalSeparator(self, 2,2,2,2)

        # ---------------- Scrolling content ----------------
        scroll  = FXScrollWindow(self, LAYOUT_FILL_X|LAYOUT_FILL_Y|VSCROLLER_ALWAYS|HSCROLLER_NEVER)
        content = FXVerticalFrame(scroll, FRAME_NONE|LAYOUT_FILL_X|LAYOUT_FILL_Y)

        # Title
        t = FXLabel(p=content, text='Macroscopic analysis results', opts=JUSTIFY_LEFT)
        t.setFont(getAFXFont(FONT_BOLD))

        # Displacements
        gb_v = FXGroupBox(content, 'Displacements', FRAME_GROOVE|LAYOUT_FILL_X)
        vf_v = FXVerticalFrame(gb_v, FRAME_SUNKEN|FRAME_THICK)
        tv   = AFXTable(vf_v, 2,3, 2,3, self.form.vKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tv.setLeadingRows(1); tv.setLeadingRowLabels('v1\tv2\tv3')
        tv.setColumnWidth(-1, colw); tv.setColumnJustify(-1, AFXTable.RIGHT)
        tv.showHorizontalGrid(True); tv.showVerticalGrid(True)

        # Rotations
        gb_c = FXGroupBox(content, 'Rotations', FRAME_GROOVE|LAYOUT_FILL_X)
        vf_c = FXVerticalFrame(gb_c, FRAME_SUNKEN|FRAME_THICK)
        tc   = AFXTable(vf_c, 3,3, 2,3, self.form.cKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tc.setColumnWidth(-1, colw); tc.setColumnJustify(-1, AFXTable.RIGHT)
        tc.showHorizontalGrid(True); tc.showVerticalGrid(True)

        # Generalized inputs (switchers)
        gb_g   = FXGroupBox(content, 'Generalized inputs', FRAME_GROOVE|LAYOUT_FILL_X)
        self.swt_dim = FXSwitcher(gb_g)  # 1D / 2D / 3D

        # 1D switcher: 0 Euler strain, 1 Euler stress, 2 Timo strain, 3 Timo stress
        f1d = FXVerticalFrame(self.swt_dim)
        self.swt_1d = FXSwitcher(f1d)

        # Euler STRAIN: be=[ε11], bk=[κ11 κ12 κ13]
        f_1d_es = FXVerticalFrame(self.swt_1d)
        vf = FXVerticalFrame(f_1d_es, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,1, 2,1, self.form.beKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('epsilon11')
        vf2 = FXVerticalFrame(f_1d_es, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.bkKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('kappa11\tkappa12\tkappa13')

        # Euler STRESS: be=[F1], bk=[M1 M2 M3]
        f_1d_eF = FXVerticalFrame(self.swt_1d)
        vf = FXVerticalFrame(f_1d_eF, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,1, 2,1, self.form.beKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('F1')
        vf2 = FXVerticalFrame(f_1d_eF, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.bkKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('M1\tM2\tM3')

        # Timoshenko STRAIN: be=[ε11 γ12 γ13], bk=[κ11 κ12 κ13]
        f_1d_ts = FXVerticalFrame(self.swt_1d)
        vf = FXVerticalFrame(f_1d_ts, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.beKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('epsilon11\tgamma12\tgamma13')
        vf2 = FXVerticalFrame(f_1d_ts, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.bkKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('kappa11\tkappa12\tkappa13')

        # Timoshenko STRESS: be=[F1 F2 F3], bk=[M1 M2 M3]
        f_1d_tF = FXVerticalFrame(self.swt_1d)
        vf = FXVerticalFrame(f_1d_tF, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.beKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('F1\tF2\tF3')
        vf2 = FXVerticalFrame(f_1d_tF, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.bkKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('M1\tM2\tM3')

        # 2D switcher: 0 KL strain, 1 KL stress, 2 Mindlin strain, 3 Mindlin stress
        f2d = FXVerticalFrame(self.swt_dim)
        self.swt_2d = FXSwitcher(f2d)

        # Kirchhoff STRAIN
        f_2d_ks = FXVerticalFrame(self.swt_2d)
        vf = FXVerticalFrame(f_2d_ks, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.seKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('epsilon11\t2epsilon12\tepsilon22')
        vf2 = FXVerticalFrame(f_2d_ks, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.skKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('kappa11\t2kappa12\tkappa22')

        # Kirchhoff STRESS
        f_2d_kF = FXVerticalFrame(self.swt_2d)
        vf = FXVerticalFrame(f_2d_kF, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.seKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('N11\tN22\tN12')
        vf2 = FXVerticalFrame(f_2d_kF, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.skKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('M11\tM22\tM12')

        # Mindlin STRAIN (adds γ13 γ23 in esKw)
        f_2d_ms = FXVerticalFrame(self.swt_2d)
        vf = FXVerticalFrame(f_2d_ms, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.seKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('epsilon11\t2epsilon12\tepsilon22')
        vf2 = FXVerticalFrame(f_2d_ms, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.skKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('kappa11\t2kappa12\tkappa22')
        vf3 = FXVerticalFrame(f_2d_ms, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf3, 2,2, 2,2, self.form.esKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('gamma13\tgamma23')

        # Mindlin STRESS (adds N13 N23 in esKw)
        f_2d_mF = FXVerticalFrame(self.swt_2d)
        vf = FXVerticalFrame(f_2d_mF, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.seKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('N11\tN22\tN12')
        vf2 = FXVerticalFrame(f_2d_mF, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.skKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('M11\tM22\tM12')
        vf3 = FXVerticalFrame(f_2d_mF, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf3, 2,2, 2,2, self.form.esKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('N13\tN23')

        # 3D switcher: 0 strain, 1 stress
        f3d = FXVerticalFrame(self.swt_dim)
        self.swt_3d = FXSwitcher(f3d)

        f_3d_s = FXVerticalFrame(self.swt_3d)
        vf = FXVerticalFrame(f_3d_s, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.enKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('epsilon11\tepsilon22\tepsilon33')
        vf2 = FXVerticalFrame(f_3d_s, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.esKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('2epsilon23\t2epsilon13\t2epsilon12')

        f_3d_F = FXVerticalFrame(self.swt_3d)
        vf = FXVerticalFrame(f_3d_F, FRAME_SUNKEN|FRAME_THICK)
        tb = AFXTable(vf, 2,3, 2,3, self.form.enKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('sigma11\tsigma22\tsigma33')
        vf2 = FXVerticalFrame(f_3d_F, FRAME_SUNKEN|FRAME_THICK)
        tb  = AFXTable(vf2, 2,3, 2,3, self.form.esKw, 0, AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        tb.setLeadingRows(1); tb.setLeadingRowLabels('sigma23\tsigma13\tsigma12')

        # Additional inputs
        addGB = FXGroupBox(content, 'Additional inputs', FRAME_GROOVE|LAYOUT_FILL_X)
        addHF = FXHorizontalFrame(addGB, LAYOUT_FILL_X)
        addVA = AFXVerticalAligner(addHF)
        self.tempdiff = AFXTextField(addVA, 12, 'temperature increment', self.form.tmKw, 0)

    # Repopulate the CAE SG list with only valid names --------
    def _refresh_sg_list(self):
        try:
            valid = _valid_cae_sg_names()
            # clear and repopulate list
            try:
                self.List_sg.clearItems()
            except Exception:
                pass
            for nm in valid:
                self.List_sg.appendItem(nm)
            # set keyword to first valid (or empty)
            if valid:
                if self.form.sg_nameKw.getValue() not in valid:
                    self.form.sg_nameKw.setValue(valid[0])
            else:
                self.form.sg_nameKw.setValue('')
        except Exception:
            pass
    # ----------------------------------------------------------------------

    # -------- Helpers --------
    def _toggle_specific(self, macro_model_int):
        if macro_model_int == 1:
            self.beamRow.show();  self.shellRow.hide()
        elif macro_model_int == 2:
            self.beamRow.hide();  self.shellRow.show()
        else:
            self.beamRow.hide();  self.shellRow.hide()
        try:
            self.beamRow.recalc(); self.shellRow.recalc()
            self.layout(); self.update()
        except Exception: pass

    def _error(self, title, msg):
        try:
            showAFXErrorDialog(getAFXApp().getAFXMainWindow(), '%s\n\n%s' % (title, msg))
        except Exception:
            try:
                AFXMessageDialog(getAFXApp().getAFXMainWindow(),
                                 self, AFXMessageDialog.ERROR, title, msg).create().showModal()
            except Exception:
                print('[ERROR] %s: %s' % (title, msg))

    # Show an error only once per unique "key"
    def _error_once(self, title, msg, key):
        if key == self._last_error_key:
            return
        self._last_error_key = key
        self._error(title, msg)

    def _determine_model_from_cae(self, sg_name):
        """Return (macro_model_int, model_string). Enforces that a real .sc exists.
           Uses numeric specific_model when available; falls back to model strings."""
        # 0) fetch SG
        try:
            sg = mdb.customData.sgs[sg_name]
        except Exception:
            self._error_once('CAE model',
                             'Selected SG cannot be found in mdb.customData.sgs.',
                             key=('missing_sg', sg_name))
            return (None, None)

        # 1) MUST have a usable .sc file in current work directory
        sc_path = _resolve_sc_for_sg(sg, sg_name)
        if not sc_path:
            self._error_once(
                'SwiftComp file not found',
                ("The selected CAE SG requires a matching .sc file in the current work directory.\n"
                 "Set the work directory to the folder containing the .sc and try again, "
                 "or re-export homogenization."),
                key=('missing_sc', sg_name)
            )
            return (None, None)

        # 2) dimension
        try:
            dim = (getattr(sg, 'macro_model_dimension', '') or '').strip()
            macro = int(dim.strip('D')) if dim else None
        except Exception:
            macro = None

        # 3) prefer numeric specific_model (0/1). fall back to strings.
        sm = getattr(sg, 'specific_model', None)
        beam  = (getattr(sg, 'beam_model',  '') or '').strip()
        shell = (getattr(sg, 'shell_model', '') or '').strip()
        model = (getattr(sg, 'model',       '') or '').strip()
        nm = (sg_name or '').lower()

        if macro == 1:
            # 1D: 0=Euler, 1=Timoshenko
            if isinstance(sm, (int, long)) if 'long' in dir(__builtins__) else isinstance(sm, int):
                if sm in (0, 1):
                    return (1, 'Euler' if sm == 0 else 'Timoshenko')
            # fallback: strings / name
            cand = beam or (model if model.lower().startswith(('euler','timo')) else '')
            if not cand:
                cand = 'Euler' if 'euler' in nm else ('Timoshenko' if 'timo' in nm else '')
            if not cand:
                self._error_once(
                    'Missing beam model',
                    'CAE SG is 1D but lacks Euler/Timoshenko info. Re-export with the latest GUI.',
                    key=('beam_missing', sg_name)
                ); return (None, None)
            return (1, 'Euler' if cand.lower().startswith('euler') else 'Timoshenko')

        if macro == 2:
            # 2D: 0=Kirchhoff, 1=Mindlin
            if isinstance(sm, (int, long)) if 'long' in dir(__builtins__) else isinstance(sm, int):
                if sm in (0, 1):
                    return (2, 'Kirchhoff' if sm == 0 else 'Mindlin')
            # fallback: strings / name
            ml = model.lower()
            cand = shell or (model if ml.startswith(('kirch','mind')) else '')
            if not cand:
                cand = 'Kirchhoff' if 'kirch' in nm else ('Mindlin' if ('mind' in nm or 'reissner' in nm) else '')
            if not cand:
                self._error_once(
                    'Missing shell model',
                    'CAE SG is 2D but lacks Kirchhoff/Mindlin info. Re-export with the latest GUI.',
                    key=('shell_missing', sg_name)
                ); return (None, None)
            return (2, 'Kirchhoff' if cand.lower().startswith('kirch') else 'Mindlin')

        if macro == 3:
            return (3, '')

        self._error_once(
            'Unknown macro model',
            'Could not determine whether the CAE SG is 1D/2D/3D. Re-export with the latest GUI.',
            key=('macro_unknown', sg_name)
        )
        return (None, None)

    # -------- AFXDataDialog overrides --------
    def show(self):
        # reset error latch every time dialog opens
        self._last_error_key = None
        self._last_sg_name   = ''
        self._last_source    = None

        if self.form.sgmodel_sourceKw.getValue() == 2:
            self.swt_source.setCurrent(1)
            self._toggle_specific(self.form.macro_modelKw.getValue())
        else:
            self.swt_source.setCurrent(0)
            self.beamRow.hide(); self.shellRow.hide()
            # Ensure list is fresh on open in CAE mode
            self._refresh_sg_list()

        self.tempdiff.disable()
        AFXDataDialog.show(self)

    def processUpdates(self):
        # detect CAE/SC switching; refresh list when CAE is selected
        try:
            current_source = self.form.sgmodel_sourceKw.getValue()
        except Exception:
            current_source = None

        if current_source != self._last_source:
            self._last_source = current_source
            if current_source == 1:  # CAE
                self._refresh_sg_list()

        # if the selected SG changed, allow a new error to show once
        sg_now = self.form.sg_nameKw.getValue()
        if sg_now != self._last_sg_name:
            self._last_sg_name = sg_now
            self._last_error_key = None  # clear the latch when user changes selection

        # normalize measure
        try:
            measure = int(self.form.load_measureKw.getValue())
        except Exception:
            measure = 1 if str(self.form.load_measureKw.getValue()).lower().startswith('strain') else 0
        is_strain = (measure == 1)

        if self.form.sgmodel_sourceKw.getValue() == 1:
            # -------- CAE mode --------
            self.swt_source.setCurrent(0)
            sg_name = self.form.sg_nameKw.getValue()

            if not sg_name:
                self.swt_dim.setCurrent(2)
                return

            macro, variant = self._determine_model_from_cae(sg_name)
            if macro is None:
                return

            self.swt_dim.setCurrent(macro - 1)

            if macro == 1:
                self.beamRow.hide(); self.shellRow.hide()
                self.swt_1d.setCurrent(0 if (variant == 'Euler' and is_strain)
                                       else 1 if (variant == 'Euler' and not is_strain)
                                       else 2 if (variant == 'Timoshenko' and is_strain)
                                       else 3)
            elif macro == 2:
                self.beamRow.hide(); self.shellRow.hide()
                self.swt_2d.setCurrent(0 if (variant == 'Kirchhoff' and is_strain)
                                       else 1 if (variant == 'Kirchhoff' and not is_strain)
                                       else 2 if (variant == 'Mindlin' and is_strain)
                                       else 3)
            else:
                self.beamRow.hide(); self.shellRow.hide()
                self.swt_3d.setCurrent(0 if is_strain else 1)

            try:
                analysis = int(getattr(mdb.customData.sgs[sg_name], 'analysis', 0))
            except Exception:
                analysis = 0
            if analysis in (1, 4, 6):
                self.tempdiff.enable()
            else:
                self.tempdiff.disable()

            try:
                self.swt_1d.recalc(); self.swt_2d.recalc(); self.swt_3d.recalc()
                self.swt_dim.recalc(); self.layout(); self.update()
            except Exception: pass

        else:
            # -------- SwiftComp mode --------
            # changing source resets error latch
            if self._last_error_key is not None:
                self._last_error_key = None

            self.swt_source.setCurrent(1)
            macro = self.form.macro_modelKw.getValue()
            self._toggle_specific(macro)

            self.swt_dim.setCurrent(macro - 1)
            if macro == 1:
                bm = self.form.beam_modelKw.getValue().lower()
                self.swt_1d.setCurrent(0 if (bm=='euler' and is_strain)
                                       else 1 if (bm=='euler' and not is_strain)
                                       else 2 if (bm=='timoshenko' and is_strain)
                                       else 3)
            elif macro == 2:
                sm = self.form.shell_modelKw.getValue().lower()
                self.swt_2d.setCurrent(0 if (sm=='kirchhoff' and is_strain)
                                       else 1 if (sm=='kirchhoff' and not is_strain)
                                       else 2 if (sm in ('mindlin','reissner','reissner–mindlin','reissner-mindlin') and is_strain)
                                       else 3)
            else:
                self.swt_3d.setCurrent(0 if is_strain else 1)

            analysis = self.form.analysisKw.getValue()
            if analysis in (1, 4, 44, 6):
                self.tempdiff.enable()
            else:
                self.tempdiff.disable()

            try:
                self.swt_1d.layout(); self.swt_2d.layout(); self.swt_3d.layout()
                self.swt_dim.layout(); self.layout(); self.update()
            except Exception: pass

###########################################################################
# File selector helper
###########################################################################

class LocalDBFileHandler(FXObject):
    def __init__(self, form, keyword, patterns='*'):
        self.form      = form
        self.patterns  = patterns
        self.patternTgt= AFXIntTarget(0)
        self.fileNameKw = getattr(form, keyword + 'Kw')
        self.readOnlyKw= AFXBoolKeyword(None, 'readOnly', AFXBoolKeyword.TRUE_FALSE)
        FXObject.__init__(self)
        FXMAPFUNC(self, SEL_COMMAND, AFXMode.ID_ACTIVATE, LocalDBFileHandler.activate)

    def activate(self, sender, sel, ptr):
        dlg = AFXFileSelectorDialog(getAFXApp().getAFXMainWindow(), 'Select a File',
                                    self.fileNameKw, self.readOnlyKw,
                                    AFXSELECTFILE_ANY, self.patterns, self.patternTgt)
        dlg.setReadOnlyPatterns('*.odb')
        dlg.create()
        dlg.showModal()
