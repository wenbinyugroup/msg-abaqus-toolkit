# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import shutil

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


def _read_plain_tensor_data(filename, start_index, extension):
    """Read tensor rows from a VABS result file.

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
    list[tuple[float, ...]]
        Tensor rows.
    """
    rows = []
    try:
        print('    -> Reading .%s file...' % extension)
        for tokens in _iter_non_empty_tokens(filename):
            rows.append(tuple(float(value) for value in tokens[start_index:]))
    except Exception:
        print('--! Cannot find .%s file.' % extension)
    return rows


def resolve_vabs_trans_flag(trans_flag, sections, distributions):
    """Resolve whether elemental orientations are required for VABS input.

    Parameters
    ----------
    trans_flag : int | bool | None
        Explicit caller-provided flag. ``None`` means infer from input data.
    sections : list
        Parsed Abaqus section keywords.
    distributions : list
        Parsed Abaqus distribution keywords.

    Returns
    -------
    int
        ``1`` when local elemental orientation data is required, otherwise ``0``.
    """
    if trans_flag is not None:
        return int(trans_flag)

    for section in sections:
        params = {str(key).lower(): value for key, value in section.parameter.items()}
        if 'composite' in params or 'orientation' in params:
            return 1

    for distribution in distributions:
        if getattr(distribution, 'data', None):
            return 1

    return 0


def read_vabs_input_mesh(vabs_input):
    """Read SG mesh and section data from a VABS input file.

    Parameters
    ----------
    vabs_input : str
        Path to the VABS input file.

    Returns
    -------
    dict
        Parsed mesh data and connectivity groups.
    """
    skip_line = [1, 2, 3]
    index = 1
    record_index = 1
    data = {
        'nnode': 0,
        'nelem': 0,
        'node_coord': [],
        'elem_connt': [],
        'elem_sectn': {},
        'elem_label': [],
        'elem_connt_s3': [],
        'elem_connt_s6': [],
        'elem_connt_s4': [],
        'elem_connt_s8': [],
        'elem_connt_s9': [],
    }

    print('--> Reading VABS input file...')
    with open(vabs_input, 'r') as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue

            tokens = stripped.split()
            if index in skip_line:
                index += 1
                continue
            if index == skip_line[-1] + 1:
                data['nnode'] = int(tokens[0])
                data['nelem'] = int(tokens[1])
                index += 1
                continue

            if record_index <= data['nnode']:
                data['node_coord'].append((int(tokens[0]), 0.0, float(tokens[1]), float(tokens[2])))
                record_index += 1
                continue

            if record_index <= data['nnode'] + data['nelem']:
                element_data = tuple(int(value) for value in tokens if value != '0')
                data['elem_label'].append(int(tokens[0]))
                data['elem_connt'].append(element_data)

                if len(element_data) == 4:
                    data['elem_connt_s3'].append(element_data)
                elif len(element_data) == 7:
                    data['elem_connt_s6'].append(element_data)
                elif len(element_data) == 5:
                    data['elem_connt_s4'].append(element_data)
                elif len(element_data) == 9:
                    data['elem_connt_s8'].append(element_data)
                elif len(element_data) == 10:
                    data['elem_connt_s9'].append(element_data)
                record_index += 1
                continue

            if record_index <= data['nnode'] + data['nelem'] + data['nelem']:
                element_id = int(tokens[0])
                section = int(tokens[1])
                if section not in data['elem_sectn']:
                    data['elem_sectn'][section] = []
                data['elem_sectn'][section].append(element_id)
                record_index += 1

    data['elem_label'].sort()
    for key in ('elem_connt_s3', 'elem_connt_s6', 'elem_connt_s4', 'elem_connt_s8', 'elem_connt_s9'):
        data[key].sort()

    print('    Done.')
    return data


def read_vabs_results(vabs_input):
    """Read displacement and tensor result files produced by VABS.

    Parameters
    ----------
    vabs_input : str
        Path to the VABS input file.

    Returns
    -------
    dict
        Parsed displacement and tensor result data.
    """
    print('--> Reading result files...')
    node_label = []
    u_data = []

    try:
        print('    -> Reading .U file...')
        for tokens in _iter_non_empty_tokens(vabs_input + '.U'):
            node_label.append(int(tokens[0]))
            u_data.append((float(tokens[3]), float(tokens[4]), float(tokens[5])))
    except Exception:
        print('--! Cannot find .U file.')

    result = {
        'node_label': node_label,
        'u_data': u_data,
        'sg_strain': _read_plain_tensor_data(vabs_input + '.E', 2, 'E'),
        'sg_stress': _read_plain_tensor_data(vabs_input + '.S', 2, 'S'),
        'sn_strain': _read_plain_tensor_data(vabs_input + '.EN', 3, 'EN'),
        'sn_stress': _read_plain_tensor_data(vabs_input + '.SN', 3, 'SN'),
        'sgm_strain': _read_plain_tensor_data(vabs_input + '.EM', 2, 'EM'),
        'sgm_stress': _read_plain_tensor_data(vabs_input + '.SM', 2, 'SM'),
        'snm_strain': _read_plain_tensor_data(vabs_input + '.EMN', 3, 'EMN'),
        'snm_stress': _read_plain_tensor_data(vabs_input + '.SMN', 3, 'SMN'),
    }
    print('    Done.')
    return result


def create_vabs_recovery_input(
    vabs_rec_name,
    vabs_inp_name2,
    model_recover,
    u,
    c,
    sf,
    sm,
    df,
    dm,
    gamma,
    kappa,
    kappa_p,
):
    """Create the VABS recovery input and copy required side files.

    Parameters
    ----------
    vabs_rec_name : str
        New recovery job stem.
    vabs_inp_name2 : str
        Existing VABS input path.
    model_recover : int
        Recovery model flag.
    u, c, sf, sm, df, dm, gamma, kappa, kappa_p : sequence
        Recovery load/state inputs used by VABS.

    Returns
    -------
    str
        Path to the generated recovery input file.
    """
    directory = os.path.dirname(vabs_inp_name2)
    fn_inp_rec = os.path.join(directory, vabs_rec_name + '.dat')

    for extension in ('.ech', '.K', '.opt', '.v0'):
        shutil.copyfile(vabs_inp_name2 + extension, fn_inp_rec + extension)
    if model_recover == 2:
        shutil.copyfile(vabs_inp_name2 + '.v1S', fn_inp_rec + '.v1S')
        shutil.copyfile(vabs_inp_name2 + '.v22', fn_inp_rec + '.v22')

    with open(fn_inp_rec, 'w') as fout:
        with open(vabs_inp_name2, 'r') as fin:
            before_change = True
            for line in fin:
                if before_change:
                    flags = line.split()
                    if len(flags) == 3:
                        flags = [int(flags[0]), 1, int(flags[2])]
                        writeFormat(fout, 'ddd', flags)
                        before_change = False
                        continue
                fout.write(line)

        writeFormat(fout, 'EEE', u[0])
        fout.write('\n')
        writeFormat(fout, 'EEE', c[0])
        writeFormat(fout, 'EEE', c[1])
        writeFormat(fout, 'EEE', c[2])
        fout.write('\n')
        if model_recover == 3:
            writeFormat(fout, 'E' * 7, gamma[0] + kappa[0] + kappa_p[0])
            fout.write('\n')
        else:
            writeFormat(fout, 'E' * 4, [sf[0][0]] + list(sm[0]))
            if model_recover == 2:
                writeFormat(fout, 'EE', sf[0][1:])
                writeFormat(fout, 'E' * 6, df[0] + dm[0])
                writeFormat(fout, 'E' * 6, df[1] + dm[1])
                writeFormat(fout, 'E' * 6, df[2] + dm[2])
                writeFormat(fout, 'E' * 6, df[3] + dm[3])
        fout.write('\n')

    return fn_inp_rec
