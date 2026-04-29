# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import re

from abaqus import *

from utils.utilities import debug


def _iter_noncomment_lines(path):
    """Yield non-empty, non-comment lines from a text file.

    Parameters
    ----------
    path : str
        Path to the input file.

    Yields
    ------
    str
        Stripped file line.
    """
    with open(path, 'r') as file:
        for line in file:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                yield stripped


def infer_swiftcomp_dimension_submodel(sc_path):
    """Infer the macro model dimension and submodel from a SwiftComp input.

    Parameters
    ----------
    sc_path : str
        Path to the SwiftComp input file.

    Returns
    -------
    tuple[str, str]
        Dimension and submodel labels.
    """
    lines = list(_iter_noncomment_lines(sc_path))
    if not lines:
        return ('3D', 'Solid')

    tokens = re.split(r'\s+', lines[0])
    if not tokens:
        return ('3D', 'Solid')

    try:
        model_flag = int(tokens[0])
    except Exception:
        return ('3D', 'Solid')

    if model_flag not in (0, 1, 2, 3):
        return ('3D', 'Solid')

    def _count_numeric_tokens(line):
        count = 0
        for token in re.split(r'\s+', line):
            if not token:
                continue
            try:
                float(token)
                count += 1
            except ValueError:
                pass
        return count

    line2_count = _count_numeric_tokens(lines[1]) if len(lines) > 1 else 0
    line3_count = _count_numeric_tokens(lines[2]) if len(lines) > 2 else 0

    if line2_count == 3 and line3_count >= 2:
        return ('1D', {0: 'Euler', 1: 'Timoshenko', 2: 'Vlasov', 3: 'Trapeze'}.get(model_flag, 'Unknown'))
    if line2_count == 2:
        return ('2D', {0: 'Kirchhoff', 1: 'Mindlin'}.get(model_flag, 'Unknown'))
    return ('3D', 'Solid')


def resolve_sgmodel_info(sgmodel_source, sg_name, sc_input, analysis, macro_model, ap_flag):
    """Resolve SG metadata from an SG model name or a SwiftComp input path.

    Parameters
    ----------
    sgmodel_source : int
        ``1`` for a stored SG model, ``2`` for a SwiftComp input path.
    sg_name : str
        Structure genome name when ``sgmodel_source == 1``.
    sc_input : str
        SwiftComp input path when ``sgmodel_source == 2``.
    analysis : int
        Analysis type.
    macro_model : int
        Macro model dimension as ``1``, ``2``, or ``3``.
    ap_flag : bool
        Aperiodic flag.

    Returns
    -------
    tuple
        ``(SCfileName, sc_input, analysis, macro_model, macro_model_dimension,
        ap_flag, sc_dim, sc_sub)``.
    """
    if sgmodel_source == 1:
        sc_filename = mdb.customData.sgs[sg_name].swiftcomp_filename
        current_path = os.getcwd()
        sc_input = os.path.join(current_path, sc_filename)
        sc_file_name = sg_name

        if debug == 1:
            print('\n')
            print('--->sc_input corresponding to the sg model is  %s' % sc_input)
            print('\n')
    elif sgmodel_source == 2:
        sc_input = os.path.normpath(sc_input)
        sc_path = os.path.dirname(sc_input)
        current_path = os.getcwd()
        if debug == 1:
            print('\n')
            print('when sgmodel_source == 2: ')
            print('sc_input %s chosen in dialog box: ' % sc_path)
            print('scpath = os.path.dirname(sc_input) : %s' % sc_path)
            print('currentpath = os.getcwd() : %s' % current_path)
            print('\n')

        sc_file_name = os.path.basename(sc_input).split('.')[0]
        if sc_path != current_path:
            raise ValueError(
                'File %s.sc is at %s, \n the work directory is %s. \n File %s.sc and the homogenization output files should be in the work directory.'
                % (sc_file_name, sc_path, current_path, sc_file_name)
            )

        if debug == 1:
            print('\n')
            print('---> sc_input selected is %s ' % sc_input)
            print('\n')
    else:
        raise ValueError('Unknown sgmodel_source: %s' % sgmodel_source)

    if sgmodel_source == 1:
        sg = mdb.customData.sgs[sg_name]
        analysis = sg.analysis
        macro_model_dimension = sg.macro_model_dimension
        macro_model = int(macro_model_dimension.strip('D'))
        if hasattr(sg, 'apstr'):
            ap_flag = sg.apstr != 'pbc'
    else:
        macro_model_dimension = str(macro_model) + 'D'

    sc_dim, sc_sub = infer_swiftcomp_dimension_submodel(sc_input)
    return (
        sc_file_name,
        sc_input,
        analysis,
        macro_model,
        macro_model_dimension,
        ap_flag,
        sc_dim,
        sc_sub,
    )
