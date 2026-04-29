import codecs
from logic.core.utilities import *
# from logic.core.parseAbaqusInput import *

def writeSCInput(
    sc_inp,
    nsg, n_coord, eid_all, eid_lid, e_connt_2d, e_connt_3d,
    distr_all, layer_types, materials,
    macro_model=3, specific_model=0,
    analysis=0, elem_flag=0, trans_flag=0, temp_flag=0,
    bk=[], sk=[], cos=[], w=1
):

    # ================================================================
    # Structures of Inputs
    # ---------------------------------
    # n_coord = [
    #     [nid1, x1, y1, z1],
    #     [nid2, x2, y2, z2],
    #     ...
    # ]
    # ---------------------------------
    # e_connt = [
    #     [eid1, mid1/lid1, nid11, nid12, nid13, ...],
    #     [eid2, mid2/lid2, nid21, nid22, nid23, ...],
    #     ...
    # ]
    # ---------------------------------
    # distr_all = [
    #     [eid1, a11, a12, a13, b11, b12, b13, c11, c12, c13],
    #     [eid2, a21, a22, a23, b21, b22, b23, c21, c22, c23],
    #     ...
    # ]
    # ---------------------------------
    # layer_type = [
    #     [lid1, mid1, fiber_orient1],
    #     [lid2, mid2, fiber_orient2],
    #     ...
    # ]
    # ---------------------------------
    # materials = {
    #     mid1: {
    #         'isotropy': type,
    #         'ntemp': ntemp,
    #         'elastic': [
    #             [T1, density1, const11, const12, ...]
    #             [T2, density2, const21, const22, ...]
    #             ...
    #         ]
    #     }
    #     ...
    # }
    # *** Arrangement of elastic constants ***
    # *** isotropy=0: E, nu
    # *** isotropy=1: E1, E2, E3, G12, G13, G23, nu12, nu13, nu23
    # *** isotropy=2: c1111, c1122, c1133, c1123, c1113, c1112,
    #                        c2222, c2233, c2223, c2213, c2212,
    #                               c3333, c3323, c3313, c3312,
    #                                      c2323, c2313, c2312,
    #                                             c1313, c1312,
    #                                                    c1212
    # ================================================================

    with codecs.open(sc_inp, encoding='utf-8', mode='w') as fout:
        eid_remaining = list(eid_all)
        nnode = len(n_coord)
        nelem = len(e_connt_2d) + len(e_connt_3d)
        nmate = len(list(materials.keys()))
        nslave = 0
        nlayer = len(layer_types)

        # ----- Write header -----------------------------------------
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

        writeFormat(fout, 'd'*4, [analysis, elem_flag, trans_flag, temp_flag])
        fout.write('\n')
        writeFormat(fout, 'd'*6, [nsg, nnode, nelem, nmate, nslave, nlayer])
        fout.write('\n')

        # ----- Write nodal coordinates ------------------------------
        if nsg == 1:
            for n in n_coord:
                writeFormat(fout, 'dE', [n[0], n[3]])
        elif nsg == 2:
            for n in n_coord:
                writeFormat(fout, 'dEE', [n[0], n[2], n[3]])
        elif nsg == 3:
            for n in n_coord:
                writeFormat(fout, 'dEEE', [n[0], n[1], n[2], n[3]])
        fout.write('\n')

        # ----- Write element connectivities -------------------------
        for e in e_connt_2d:
            eid = e[0]
            lid = eid_lid[eid]
            row = [eid, lid] + list(e[1:])
            writeFormat(fout, 'd'*11, row)
        for e in e_connt_3d:
            eid = e[0]
            lid = eid_lid[eid]
            row = [eid, lid] + list(e[1:])
            writeFormat(fout, 'd'*22, row)
        fout.write('\n')

        # ----- Write local coordinates ------------------------------
        if distr_all and len(distr_all) > 0:
            for distr in distr_all:
                eid = int(distr[0])
                if eid in eid_remaining:
                    eid_remaining.remove(eid)
                fout.write('{0:10d}'.format(eid))
                writeFormat(fout, 'E'*9, distr[1:])
            fout.write('\n')

        # ----- Write layer types ------------------------------------
        for lyt in layer_types:
            writeFormat(fout, 'ddE', lyt)
        fout.write('\n')

        # ----- Write materials --------------------------------------
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
                    writeFormat(fout, 'E'*6, elastic[2:8])
                    writeFormat(fout, 'E'*5, elastic[8:13])
                    writeFormat(fout, 'E'*4, elastic[13:17])
                    writeFormat(fout, 'E'*3, elastic[17:20])
                    writeFormat(fout, 'E'*2, elastic[20:22])
                    writeFormat(fout, 'E'*1, elastic[22:23])
                fout.write('\n')
            fout.write('\n')
        fout.write('\n')

        writeFormat(fout, 'E', [w])
        fout.write('\n')

