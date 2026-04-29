from abaqus import *
from logic.core.parseAbaqusInput import *
from logic.core.reorgAbaqusInput import *
from logic.core.writeVABSInput import *
import os

def _resolve_vabs_trans_flag(trans_flag, sections, distributions):
    """Resolve the elemental-orientation mode for VABS input conversion.

    Parameters
    ----------
    trans_flag : int | bool | None
        Explicit caller-provided elemental orientation flag. ``None`` means
        infer from the parsed Abaqus input.
    sections : list
        Parsed Abaqus section keyword objects.
    distributions : list
        Parsed Abaqus distribution keyword objects.

    Returns
    -------
    int
        ``1`` when local elemental orientation data is required, otherwise
        ``0``.
    """
    if trans_flag is not None:
        return int(trans_flag)

    for section in sections:
        params = {str(k).lower(): v for k, v in section.parameter.items()}
        if 'composite' in params or 'orientation' in params:
            return 1

    for distribution in distributions:
        if getattr(distribution, 'data', None):
            return 1

    return 0

def createVABSInputMain(
    abq_inp, new_filename,
    timoshenko_flag, thermal_flag, trapeze_flag, vlasov_flag,
    curve_flag, ik, oblique_flag, cos, trans_flag=0
):

    if new_filename == '':
        vabs_inp = abq_inp[:-4] + r'_vabs.dat'
    else:
        dir = os.path.dirname(abq_inp)
        new_filename = new_filename + '.dat'
        vabs_inp = os.path.join(dir, new_filename)

    # ========== Parse data from Abaqus input ==========
    milestone('Parsing data from Abaqus input...')
    results = parseAbaqusInput(abq_inp)
    # nsg = results['nsg']
    nsg = 2
    nodes = results['nodes']
    elements2d = results['elements 2d']
    elements3d = results['elements 3d']
    elsets = results['element sets']
    sections = results['sections']
    distributions = results['distribution']
    orientations = results['orientation']
    materials = results['materials']
    densities = results['densities']
    elastics = results['elastics']
    trans_flag = _resolve_vabs_trans_flag(
        trans_flag, sections, distributions
    )

    # ========== Reorganize data for VABS input ==========
    milestone('Reorganizing data for VABS input...')
    results = reorgAbaqusInput(
        nsg, nodes, elements2d, elements3d, elsets,
        sections, distributions, orientations,
        materials, densities, elastics, trans_flag
    )
    n_coord = results['nodes']
    eid_all = results['all elements ids']
    eid_lid = results['element to layer type']
    e_connt_2d = results['elements 2d']
    # e_connt_3d = results['elements 3d']
    distr_all = results['distributions']
    layer_types = results['layer types']
    materials = results['materials']

    # ========== Write VABS input ==========
    milestone('Writing VABS input...')
    writeVABSInput(
        vabs_inp,
        nsg, n_coord, eid_all, eid_lid, e_connt_2d,
        distr_all, layer_types, materials,
        timoshenko_flag, thermal_flag, trapeze_flag, vlasov_flag,
        curve_flag, ik, oblique_flag, cos
    )

    # vabs_inp = os.path.basename(vabs_inp)
    return vabs_inp


