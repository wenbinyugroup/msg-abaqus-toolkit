# -*- coding: utf-8 -*-

from main.scGenInput import generateInputFromCAE
from main.scGen1DInput_aba import generate_1DInputFromCAE
from main.UdetermineVolume import determineVolume
from main.UdetermineNSG import determineNSG
from main.createSCInputMain import createSCInputMain
import subprocess
import time


def homogenization(
        gen_input_only, model_source, macro_model, analysis,
        elem_flag, trans_flag, ap1, ap2, ap3, w='',
        model_name='', part_name='', abaqus_input='', new_filename='',
        specific_model=0, bk=None,
        sk=None, cos=None, temp_flag=0):

    if bk is None:
        bk = [[0.0, 0.0, 0.0]]
    if sk is None:
        sk = [[0.0, 0.0]]
    if cos is None:
        cos = [[1.0, 0.0]]

    if analysis == 33:
        analysis = 3
    elif analysis == 44:
        analysis = 4

    apvector = [0, 0, 0]

    if ap1:
        apvector[0] = 1
    if ap2:
        apvector[1] = 1
    if ap3:
        apvector[2] = 1

    if model_source == 1:
        nSG = determineNSG(model_name, part_name)
        macro_model_dimension = str(macro_model) + 'D'
        print('Dimension of Structure Genome: ' + str(nSG))
        print('Dimension of Macroscopic Model: ' + macro_model_dimension)

        if w == '':
            w = determineVolume(
                model_name, part_name, macro_model_dimension, nSG
            )
        else:
            w = float(w)

        if nSG == 2 or nSG == 3:
            [sc_input, macro_model_dim] = generateInputFromCAE(
                model_source, macro_model_dimension,
                analysis, elem_flag, trans_flag, w, nSG,
                model_name, part_name, abaqus_input, new_filename,
                specific_model, bk[0],
                sk[0], cos[0], temp_flag, apvector
            )

        elif nSG == 1:
            [sc_input, macro_model_dim] = generate_1DInputFromCAE(
                model_source, macro_model_dimension,
                analysis, elem_flag, trans_flag, w, nSG,
                model_name, part_name, abaqus_input, new_filename,
                specific_model, bk[0],
                sk[0], cos[0], temp_flag
            )

        else:
            raise ValueError("Unsupported SG dimension: %d" % nSG)

    elif model_source == 2:
        if w == '':
            w = 1.0
        else:
            w = float(w)

        [sc_input, macro_model_dim] = createSCInputMain(
            abaqus_input, new_filename, macro_model, specific_model,
            analysis, elem_flag, trans_flag, temp_flag,
            bk[0], sk[0], cos[0], w
        )

    print('Finish creating SwiftComp input.')

    if not gen_input_only:
        scTimestart = time.perf_counter()
        cmd = ['Swiftcomp', sc_input, macro_model_dim]
        if apvector == [0, 0, 0]:
            cmd.append('H')
        else:
            cmd.append('HA')
        try:
            result = subprocess.run(cmd, timeout=300, check=False)
        except FileNotFoundError:
            raise RuntimeError(
                'SwiftComp executable not found. '
                'Ensure SwiftComp is installed and on the system PATH.'
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                'SwiftComp did not finish within 300 seconds. '
                'Consider using "Only generate input file" for large models.'
            )
        if result.returncode != 0:
            raise RuntimeError(
                'SwiftComp exited with code %d' % result.returncode
            )

        scTimeEnd = time.perf_counter()
        scTime = scTimeEnd - scTimestart

        print('scTime: ' + str(scTime))
