# -*- coding: utf-8 -*-

from __future__ import print_function

import codecs
import os

from abaqus import *
from abaqusConstants import *

from utils.utilities import writeFormat


def _iter_non_empty_tokens(filename):
    """Yield tokenized non-empty lines from a text file.

    Parameters
    ----------
    filename : str
        Path to the source file.

    Yields
    ------
    list[str]
        Tokens from one non-empty line.
    """
    with open(filename, 'r') as file:
        for line in file:
            stripped = line.strip()
            if stripped:
                yield stripped.split()


def _read_labelled_vectors(filename, value_start, extension, value_count=3):
    """Read a labelled vector file.

    Parameters
    ----------
    filename : str
        Path to the source file.
    value_start : int
        Starting token index for vector values.
    extension : str
        File extension used in log messages.
    value_count : int, optional
        Number of vector components to read.

    Returns
    -------
    tuple[list[int], list[tuple[float, ...]]]
        Labels and vector values.
    """
    labels = []
    vectors = []

    try:
        for tokens in _iter_non_empty_tokens(filename):
            labels.append(int(tokens[0]))
            vectors.append(tuple(float(value) for value in tokens[value_start:value_start + value_count]))
        print('--> Find .%s file.' % extension)
    except Exception:
        print('--! Cannot find .%s file.' % extension)

    return labels, vectors


def _read_tensor_results(filename, start_index, extension):
    """Read paired strain/stress tensor data from a result file.

    Parameters
    ----------
    filename : str
        Path to the source file.
    start_index : int
        First tensor component index.
    extension : str
        File extension used in log messages.

    Returns
    -------
    tuple[list[tuple[float, ...]], list[tuple[float, ...]]]
        Strain and stress tensor values.
    """
    strain_data = []
    stress_data = []

    try:
        for tokens in _iter_non_empty_tokens(filename):
            strain_data.append(tuple(float(value) for value in tokens[start_index:start_index + 6]))
            stress_data.append(tuple(float(value) for value in tokens[start_index + 6:start_index + 12]))
        print('--> Find .%s file.' % extension)
    except Exception:
        print('--! Cannot find .%s file.' % extension)

    return strain_data, stress_data


def _get_skip_lines(macro_model_dimension, ap_flag):
    """Return SwiftComp header lines skipped before SG metadata.

    Parameters
    ----------
    macro_model_dimension : str
        Macro model dimension label such as ``'1D'`` or ``'2D'``.
    ap_flag : bool
        Flag indicating whether the aperiodic header is present.

    Returns
    -------
    list[int]
        Header line numbers to skip.
    """
    skip_line_map = {
        False: {'1D': [1, 2, 3, 4], '2D': [1, 2, 3], '3D': [1]},
        True: {'1D': [1, 2, 3, 4, 5], '2D': [1, 2, 3, 4], '3D': [1, 2]},
    }
    return skip_line_map[ap_flag][macro_model_dimension]


def writeSCInput(
    sc_inp,
    nsg,
    n_coord,
    eid_all,
    eid_lid,
    e_connt_2d,
    e_connt_3d,
    distr_all,
    layer_types,
    materials,
    macro_model=3,
    specific_model=0,
    analysis=0,
    elem_flag=0,
    trans_flag=0,
    temp_flag=0,
    bk=[],
    sk=[],
    cos=[],
    w=1,
):
    """Write a SwiftComp input file.

    Parameters
    ----------
    sc_inp : str
        Output SwiftComp input path.
    nsg : int
        Structure genome dimension.
    n_coord : list[list[float]]
        Node table ``[nid, x, y, z]``.
    eid_all : list[int]
        All element ids.
    eid_lid : dict[int, int]
        Mapping from element id to layer id.
    e_connt_2d : list[list[int]]
        2D element connectivity rows.
    e_connt_3d : list[list[int]]
        3D element connectivity rows.
    distr_all : list[list[float]]
        Element local-coordinate distributions.
    layer_types : list[list[float]]
        Layer-type rows ``[lid, mid, angle]``.
    materials : dict
        Material property map.
    macro_model : int, optional
        Macro model dimension.
    specific_model : int, optional
        Specific beam/shell submodel flag.
    analysis : int, optional
        Analysis type.
    elem_flag : int, optional
        Element flag.
    trans_flag : int, optional
        Transformation/orientation flag.
    temp_flag : int, optional
        Thermal flag.
    bk : list[float], optional
        Beam curvature vector.
    sk : list[float], optional
        Shell curvature vector.
    cos : list[float], optional
        Initial obliqueness vector.
    w : float, optional
        SG volume/area/length weight.
    """
    with codecs.open(sc_inp, encoding='utf-8', mode='w') as fout:
        eid_remaining = list(eid_all)
        nnode = len(n_coord)
        nelem = len(e_connt_2d) + len(e_connt_3d)
        nmate = len(list(materials.keys()))
        nslave = 0
        nlayer = len(layer_types)

        if macro_model == 1:
            writeFormat(fout, 'd', [specific_model])
            fout.write('\n')
            writeFormat(fout, 'EEE', bk)
            fout.write('\n')
            writeFormat(fout, 'EE', cos)
            fout.write('\n')
        elif macro_model == 2:
            writeFormat(fout, 'd', [specific_model])
            fout.write('\n')
            writeFormat(fout, 'EE', sk)
            fout.write('\n')

        writeFormat(fout, 'd' * 4, [analysis, elem_flag, trans_flag, temp_flag])
        fout.write('\n')
        writeFormat(fout, 'd' * 6, [nsg, nnode, nelem, nmate, nslave, nlayer])
        fout.write('\n')

        if nsg == 1:
            for node in n_coord:
                writeFormat(fout, 'dE', [node[0], node[3]])
        elif nsg == 2:
            for node in n_coord:
                writeFormat(fout, 'dEE', [node[0], node[2], node[3]])
        elif nsg == 3:
            for node in n_coord:
                writeFormat(fout, 'dEEE', [node[0], node[1], node[2], node[3]])
        fout.write('\n')

        for element in e_connt_2d:
            eid = element[0]
            row = [eid, eid_lid[eid]] + list(element[1:])
            writeFormat(fout, 'd' * 11, row)
        for element in e_connt_3d:
            eid = element[0]
            row = [eid, eid_lid[eid]] + list(element[1:])
            writeFormat(fout, 'd' * 22, row)
        fout.write('\n')

        if distr_all and len(distr_all) > 0:
            for distr in distr_all:
                eid = int(distr[0])
                if eid in eid_remaining:
                    eid_remaining.remove(eid)
                fout.write('{0:10d}'.format(eid))
                writeFormat(fout, 'E' * 9, distr[1:])
            fout.write('\n')

        for layer_type in layer_types:
            writeFormat(fout, 'ddE', layer_type)
        fout.write('\n')

        for mid, prop in list(materials.items()):
            writeFormat(fout, 'ddd', [mid, prop['isotropy'], prop['ntemp']])
            for i in range(prop['ntemp']):
                elastic = prop['elastic'][i]
                writeFormat(fout, 'EE', elastic[:2])
                if prop['isotropy'] == 0:
                    writeFormat(fout, 'EE', elastic[2:])
                elif prop['isotropy'] == 1:
                    writeFormat(fout, 'EEE', elastic[2:5])
                    writeFormat(fout, 'EEE', elastic[5:8])
                    writeFormat(fout, 'EEE', elastic[8:11])
                elif prop['isotropy'] == 2:
                    writeFormat(fout, 'E' * 6, elastic[2:8])
                    writeFormat(fout, 'E' * 5, elastic[8:13])
                    writeFormat(fout, 'E' * 4, elastic[13:17])
                    writeFormat(fout, 'E' * 3, elastic[17:20])
                    writeFormat(fout, 'E' * 2, elastic[20:22])
                    writeFormat(fout, 'E' * 1, elastic[22:23])
                fout.write('\n')
            fout.write('\n')
        fout.write('\n')

        writeFormat(fout, 'E', [w])
        fout.write('\n')


def writeMaterials(matDict, analysis, model_name, file):
    """Write Abaqus material data in SwiftComp input format.

    Parameters
    ----------
    matDict : dict[str, int]
        Mapping from Abaqus material name to SwiftComp material id.
    analysis : int
        Analysis type. ``1`` requires thermal properties.
    model_name : str
        Abaqus model name.
    file : file
        Open output stream.
    """
    ntemp = 1
    temperature = 0
    model = mdb.models[model_name]
    for mat_name, mat_id in matDict.items():
        mat_type = model.materials[mat_name].elastic.type
        mp = model.materials[mat_name].elastic.table[0]

        try:
            model.materials[mat_name].density
        except Exception:
            print('density is not defined in material "%s" ' % mat_name)
            print('default values density = 0.1, temperature = 0 will be used,')
            print('which will not influence the results if analysis is not temperature related.')
            model.materials[mat_name].Density(table=((0.0,),))
        density = model.materials[mat_name].density.table[0][0]

        if analysis == 1:
            mp1sheat = model.materials[mat_name].specificHeat.table[0]
            mp1cte = model.materials[mat_name].expansion.table[0]
            mp1 = list(mp1cte) + list(mp1sheat)

        if mat_type == ISOTROPIC:
            writeFormat(file, 'ddd', [int(mat_id), 0, ntemp])
            writeFormat(file, 'EE', [float(temperature), float(density)])
            writeFormat(file, 'EE', mp[:2])
            if analysis == 1:
                writeFormat(file, 'EE', mp1)
        elif mat_type == ENGINEERING_CONSTANTS:
            writeFormat(file, 'ddd', [int(mat_id), 1, ntemp])
            writeFormat(file, 'EE', [float(temperature), float(density)])
            writeFormat(file, 'EEE', mp[:3])
            writeFormat(file, 'EEE', mp[6:9])
            writeFormat(file, 'EEE', mp[3:6])
            if analysis == 1:
                writeFormat(file, 'E' * 4, mp1)
        elif mat_type == ORTHOTROPIC:
            writeFormat(file, 'ddd', [int(mat_id), 2, ntemp])
            writeFormat(file, 'EE', [float(temperature), float(density)])
            writeFormat(file, 'E' * 6, [mp[0], mp[1], mp[3], 0.0, 0.0, 0.0])
            writeFormat(file, 'E' * 5, [mp[2], mp[4], 0.0, 0.0, 0.0])
            writeFormat(file, 'E' * 4, [mp[5], 0.0, 0.0, 0.0])
            writeFormat(file, 'E' * 3, [mp[6], 0.0, 0.0])
            writeFormat(file, 'E' * 2, [mp[7], 0.0])
            writeFormat(file, 'E' * 1, [mp[8]])
            if analysis == 1:
                writeFormat(file, 'E' * 4, mp1)
        elif mat_type == ANISOTROPIC:
            writeFormat(file, 'ddd', [int(mat_id), 2, ntemp])
            writeFormat(file, 'EE', [float(temperature), float(density)])
            writeFormat(file, 'E' * 6, [mp[0], mp[1], mp[3], mp[6], mp[10], mp[15]])
            writeFormat(file, 'E' * 5, [mp[2], mp[4], mp[7], mp[11], mp[16]])
            writeFormat(file, 'E' * 4, [mp[5], mp[8], mp[12], mp[17]])
            writeFormat(file, 'E' * 3, [mp[9], mp[13], mp[18]])
            writeFormat(file, 'E' * 2, [mp[14], mp[19]])
            writeFormat(file, 'E' * 1, [mp[20]])
            if analysis == 1:
                writeFormat(file, 'E' * 7, mp1)


def checkMaterials(matDict, analysis, model_name):
    """Validate materials required for SwiftComp input generation.

    Parameters
    ----------
    matDict : dict[str, int]
        Mapping from Abaqus material name to SwiftComp material id.
    analysis : int
        Analysis type. ``1`` requires thermal properties.
    model_name : str
        Abaqus model name.
    """
    for mat_name, mat_id in matDict.items():
        del mat_id
        model = mdb.models[model_name]
        model.materials[mat_name].elastic.type
        model.materials[mat_name].elastic.table[0]

        try:
            model.materials[mat_name].density
        except Exception:
            print('density is not defined in material "%s" ' % mat_name)
            print('default values density = 0.1, temperature = 0 will be used,')
            print('which will not influence the results if analysis is not temperature related.')
            model.materials[mat_name].Density(table=((0.0,),))

        if analysis == 1:
            try:
                model.materials[mat_name].specificHeat
            except Exception:
                raise ValueError('specificHeat is not defined in material \'%s\' ' % mat_name)

            try:
                model.materials[mat_name].expansion
            except Exception:
                raise ValueError('expansion is not defined in material \'%s\' ' % mat_name)


def read_swiftcomp_input_mesh(sc_input, macro_model_dimension, ap_flag):
    """Read SG mesh and section data from a SwiftComp input file.

    Parameters
    ----------
    sc_input : str
        Path to the SwiftComp input file.
    macro_model_dimension : str
        Macro model dimension label such as ``'1D'`` or ``'2D'``.
    ap_flag : bool
        Flag indicating whether the aperiodic header is present.

    Returns
    -------
    dict
        Parsed mesh data and connectivity groups.
    """
    skip_line = _get_skip_lines(macro_model_dimension, ap_flag)
    index = 1
    record_index = 1

    data = {
        'nsg': 0,
        'nnode': 0,
        'nelem': 0,
        'node_coord': [],
        'elem_sectn': {},
        'elem_label': [],
        'elem_connt_s3': [],
        'elem_connt_s6': [],
        'elem_connt_s4': [],
        'elem_connt_s8': [],
        'elem_connt_s9': [],
        'elem_connt_c4': [],
        'elem_connt_c6': [],
        'elem_connt_c10': [],
        'elem_connt_c8': [],
        'elem_connt_c20': [],
        'elem_connt_c15': [],
        'elem_connt_b31_temp': [],
    }

    print('--> Reading SwiftComp input file...')
    with open(sc_input, 'r') as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue

            tokens = stripped.split()
            if index in skip_line:
                index += 1
                continue
            if index == skip_line[-1] + 1:
                data['nsg'] = int(tokens[0])
                data['nnode'] = int(tokens[1])
                data['nelem'] = int(tokens[2])
                print('nsg %d' % data['nsg'])
                print('nnode %d' % data['nnode'])
                print('nelem %d' % data['nelem'])
                index += 1
                continue

            if record_index <= data['nnode']:
                if data['nsg'] == 1:
                    data['node_coord'].append((int(tokens[0]), 0.0, 0.0, float(tokens[1])))
                elif data['nsg'] == 2:
                    data['node_coord'].append((int(tokens[0]), 0.0, float(tokens[1]), float(tokens[2])))
                elif data['nsg'] == 3:
                    data['node_coord'].append((int(tokens[0]), float(tokens[1]), float(tokens[2]), float(tokens[3])))
                record_index += 1
                continue

            if record_index <= data['nnode'] + data['nelem']:
                element_label = int(tokens[0])
                connectivity = [int(value) for value in tokens[2:] if value != '0']
                connectivity = [element_label] + connectivity
                data['elem_label'].append(element_label)

                if len(tokens) == 7:
                    data['elem_connt_b31_temp'].append(tuple(connectivity))
                elif len(tokens) == 11:
                    if len(connectivity) == 4:
                        data['elem_connt_s3'].append(tuple(connectivity))
                    elif len(connectivity) == 7:
                        data['elem_connt_s6'].append(tuple(connectivity))
                    elif len(connectivity) == 5:
                        data['elem_connt_s4'].append(tuple(connectivity))
                    elif len(connectivity) == 9:
                        data['elem_connt_s8'].append(tuple(connectivity))
                    elif len(connectivity) == 10:
                        data['elem_connt_s9'].append(tuple(connectivity))
                elif len(tokens) >= 22:
                    if len(connectivity) == 5:
                        data['elem_connt_c4'].append(tuple(connectivity))
                    elif len(connectivity) == 7:
                        data['elem_connt_c6'].append(tuple(connectivity))
                    elif len(connectivity) == 11:
                        data['elem_connt_c10'].append(tuple(connectivity))
                    elif len(connectivity) == 9:
                        data['elem_connt_c8'].append(tuple(connectivity))
                    elif len(connectivity) == 16:
                        data['elem_connt_c15'].append(tuple(connectivity))
                    elif len(connectivity) == 21:
                        data['elem_connt_c20'].append(tuple(connectivity))

                section = tokens[1]
                if section not in data['elem_sectn']:
                    data['elem_sectn'][section] = []
                data['elem_sectn'][section].append(element_label)
                record_index += 1

    for key in (
        'elem_connt_s3',
        'elem_connt_s6',
        'elem_connt_s4',
        'elem_connt_s8',
        'elem_connt_s9',
        'elem_connt_c4',
        'elem_connt_c6',
        'elem_connt_c10',
        'elem_connt_c8',
        'elem_connt_c15',
        'elem_connt_c20',
        'elem_connt_b31_temp',
    ):
        data[key].sort()

    print('    Done.')
    return data


def read_swiftcomp_results(sc_input, nsg):
    """Read SwiftComp displacement and tensor result files.

    Parameters
    ----------
    sc_input : str
        Path to the SwiftComp input file without extension changes.
    nsg : int
        Structure genome dimension.

    Returns
    -------
    dict
        Parsed displacement and tensor result data.
    """
    print('--> Reading result files...')
    node_label, u_data = _read_labelled_vectors(sc_input + '.u', 1, 'u')
    sg_strain, sg_stress = _read_tensor_results(sc_input + '.sg', nsg, 'sg')
    sn_strain, sn_stress = _read_tensor_results(sc_input + '.sn', nsg, 'sn')
    sgm_strain, sgm_stress = _read_tensor_results(sc_input + '.sgm', nsg, 'sgm')
    snm_strain, snm_stress = _read_tensor_results(sc_input + '.snm', nsg, 'snm')
    print('    Done.')
    return {
        'node_label': node_label,
        'u_data': u_data,
        'sg_strain': sg_strain,
        'sg_stress': sg_stress,
        'sn_strain': sn_strain,
        'sn_stress': sn_stress,
        'sgm_strain': sgm_strain,
        'sgm_stress': sgm_stress,
        'snm_strain': snm_strain,
        'snm_stress': snm_stress,
    }


def write_swiftcomp_glb(
    sc_global,
    macro_displacement,
    macro_rotation,
    load_measure,
    macro_model_dimension,
    beam_values=None,
    shell_values=None,
    solid_values=None,
    temperature_increment=None,
    shell_model='Kirchhoff',
    mindlin_extra=None,
):
    """Write the SwiftComp localization ``.glb`` file.

    Parameters
    ----------
    sc_global : str
        Output ``.glb`` path.
    macro_displacement : sequence[float]
        Macroscopic displacement vector.
    macro_rotation : sequence[sequence[float]]
        Macroscopic rotation matrix rows.
    load_measure : int
        ``0`` for stress resultants/stresses and ``1`` for strains.
    macro_model_dimension : str
        Macro model dimension label such as ``'1D'`` or ``'2D'``.
    beam_values : sequence[float], optional
        1D generalized quantities.
    shell_values : sequence[float], optional
        2D generalized quantities.
    solid_values : sequence[float], optional
        3D generalized quantities.
    temperature_increment : sequence[float], optional
        Temperature increment values written for thermal analysis.
    shell_model : str, optional
        Shell submodel label.
    mindlin_extra : sequence[float], optional
        Extra Mindlin pair appended after the six shell values.
    """
    with open(sc_global, 'w') as file:
        writeFormat(file, 'EEE', macro_displacement)
        file.write('\n')
        writeFormat(file, 'EEE', macro_rotation[0])
        file.write('\n')
        writeFormat(file, 'EEE', macro_rotation[1])
        file.write('\n')
        writeFormat(file, 'EEE', macro_rotation[2])
        file.write('\n')
        writeFormat(file, 'd', [load_measure])
        file.write('\n')

        if macro_model_dimension == '1D':
            file.write(' '.join(str(float(value)) for value in beam_values) + '\n')
        elif macro_model_dimension == '2D':
            if shell_model.lower() in ('mindlin', 'reissner-mindlin') and mindlin_extra:
                values = list(shell_values) + list((list(mindlin_extra) + [0.0, 0.0])[:2])
                file.write(' '.join(str(float(value)) for value in values) + '\n')
            else:
                file.write(' '.join(str(float(value)) for value in shell_values) + '\n')
        elif macro_model_dimension == '3D':
            file.write(' '.join(str(float(value)) for value in solid_values) + '\n')

        file.write('\n')
        if temperature_increment is not None:
            writeFormat(file, 'E', temperature_increment)


def read_swiftcomp_homogenized_properties(sc_input_k):
    """Read homogenized properties from a SwiftComp ``.k`` file.

    Parameters
    ----------
    sc_input_k : str
        Path to the SwiftComp ``.k`` output file.

    Returns
    -------
    dict
        Parsed stiffness, engineering constants, thermal expansion,
        specific heat, and density values.
    """
    prop_matrix = []
    prop_engi = []
    cte = []
    sheat = []
    density = 0.0
    title = None

    with open(sc_input_k, 'r') as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue

            tokens = stripped.split()
            if 'Stiffness' in tokens:
                title = 'Stiffness'
                continue
            if 'Engineering' in tokens:
                title = 'Engineering'
                continue
            if 'Compliance' in tokens:
                title = 'Compliance'
                continue
            if 'Thermal' in tokens:
                title = 'Thermal'
                continue
            if 'Heat' in tokens:
                title = 'Heat'
                continue
            if 'Density' in tokens:
                density = float(tokens[-1])
                continue
            if len(tokens) == 1 and tokens[0].startswith('-'):
                continue
            if title is None:
                raise ValueError('Unknown section header in %s: %s' % (sc_input_k, ' '.join(tokens)))

            if title == 'Stiffness':
                prop_matrix.append(list(map(float, tokens)))
            elif title == 'Engineering':
                prop_engi.append(float(tokens[-1]))
            elif title == 'Thermal':
                cte.append(float(tokens[-1]))
            elif title == 'Heat':
                sheat.append(float(tokens[-1]))
            elif title != 'Compliance':
                raise ValueError('Unknown section header in %s: %s' % (sc_input_k, title))

    prop_matrix_tuple = None
    if prop_matrix:
        prop_matrix_tuple = (
            prop_matrix[0][0],
            prop_matrix[1][0], prop_matrix[1][1],
            prop_matrix[2][0], prop_matrix[2][1], prop_matrix[2][2],
            prop_matrix[3][0], prop_matrix[3][1], prop_matrix[3][2], prop_matrix[3][3],
            prop_matrix[4][0], prop_matrix[4][1], prop_matrix[4][2], prop_matrix[4][3], prop_matrix[4][4],
            prop_matrix[5][0], prop_matrix[5][1], prop_matrix[5][2], prop_matrix[5][3], prop_matrix[5][4], prop_matrix[5][5],
        )

    prop_engi_tuple = None
    if prop_engi:
        prop_engi = [
            prop_engi[0], prop_engi[1], prop_engi[2],
            prop_engi[6], prop_engi[7], prop_engi[8],
            prop_engi[3], prop_engi[4], prop_engi[5],
        ]
        prop_engi_tuple = tuple(prop_engi)

    cte_tuple = tuple(cte) if cte else None
    sheat_tuple = tuple(sheat) if sheat else None

    return {
        'density': density,
        'prop_matrix': prop_matrix,
        'prop_matrix_tuple': prop_matrix_tuple,
        'prop_engi': prop_engi,
        'prop_engi_tuple': prop_engi_tuple,
        'cte': cte,
        'cte_tuple': cte_tuple,
        'sheat': sheat,
        'sheat_tuple': sheat_tuple,
    }
