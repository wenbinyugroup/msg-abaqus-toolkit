import sys
import inpParser

def parseAbaqusInput(abq_inp_name):
    def to_list(x):
        try: return x.tolist()
        except Exception: return list(x)

    def nodes_from_kwdata(data):
        out = []
        if data is None: return out
        for row in to_list(data):
            r = to_list(row)
            if not r: continue
            # id
            i0 = None
            for v in r:
                if v is None: continue
                try:
                    i0 = int(v); break
                except Exception:
                    pass
            if i0 is None: continue
            # xyz
            coords = []
            for v in r[1:]:
                if v is None: continue
                try: coords.append(float(v))
                except Exception: pass
            while len(coords) < 3:
                coords.append(0.0)
            out.append([i0] + coords[:3])
        return out

    def collect_elements_fixed_width(data, width):
        if data is None: return []
        toks = []
        for row in to_list(data):
            for v in to_list(row):
                if v is None: continue
                try:
                    toks.append(int(v))
                except Exception:
                    pass
        rows, i = [], 0
        while i + width <= len(toks):
            rows.append(toks[i:i+width])
            i += width
        return rows

    inp = inpParser.InputFile(abq_inp_name)
    kws_obj = inp.parse(usePyArray=True)

    # element families
    el_2d3_type  = {'S3','S3R'}
    el_2d4_type  = {'S4','S4R'}
    el_2d6_type  = {'STRI65'}
    el_2d8_type  = {'S8R'}
    el_3d4_type  = {'C3D4'}
    el_3d6_type  = {'C3D6'}
    el_3d8_type  = {'C3D8','C3D8R'}
    el_3d10_type = {'C3D10'}
    el_3d15_type = {'C3D15'}
    el_3d20_type = {'C3D20','C3D20R'}

    # expected widths (eid + nodes)
    widths = {
        '2d3':  1+3,  '2d4':  1+4,  '2d6':  1+6,  '2d8':  1+8,
        '3d4':  1+4,  '3d6':  1+6,  '3d8':  1+8,  '3d10': 1+10,
        '3d15': 1+15, '3d20': 1+20,
    }

    e_connt_2d3=e_connt_2d4=e_connt_2d6=e_connt_2d8=[]
    e_connt_3d4=e_connt_3d6=e_connt_3d8=e_connt_3d10=e_connt_3d15=e_connt_3d20=[]
    elsets_raw, distributions, orientations, sections = [], [], [], []
    materials, densities, elastics = [], [], []
    mtr_name2id, lyt_name2id = {}, {}
    mid = lid = 0
    nsg = 3
    n_coord = []

    for kw in kws_obj:
        if kw.name == 'parameter':
            try: nsg = kw.parameter['sgdim']
            except Exception: nsg = 3

        elif kw.name == 'node':
            n_coord = nodes_from_kwdata(kw.data)

        elif kw.name == 'element':
            et = kw.parameter['type']
            if   et in el_2d3_type:   rows = collect_elements_fixed_width(kw.data, widths['2d3']);  e_connt_2d3  = e_connt_2d3  + rows
            elif et in el_2d4_type:   rows = collect_elements_fixed_width(kw.data, widths['2d4']);  e_connt_2d4  = e_connt_2d4  + rows
            elif et in el_2d6_type:   rows = collect_elements_fixed_width(kw.data, widths['2d6']);  e_connt_2d6  = e_connt_2d6  + rows
            elif et in el_2d8_type:   rows = collect_elements_fixed_width(kw.data, widths['2d8']);  e_connt_2d8  = e_connt_2d8  + rows
            elif et in el_3d4_type:   rows = collect_elements_fixed_width(kw.data, widths['3d4']);  e_connt_3d4  = e_connt_3d4  + rows
            elif et in el_3d6_type:   rows = collect_elements_fixed_width(kw.data, widths['3d6']);  e_connt_3d6  = e_connt_3d6  + rows
            elif et in el_3d8_type:   rows = collect_elements_fixed_width(kw.data, widths['3d8']);  e_connt_3d8  = e_connt_3d8  + rows
            elif et in el_3d10_type:  rows = collect_elements_fixed_width(kw.data, widths['3d10']); e_connt_3d10 = e_connt_3d10 + rows
            elif et in el_3d15_type:  rows = collect_elements_fixed_width(kw.data, widths['3d15']); e_connt_3d15 = e_connt_3d15 + rows
            elif et in el_3d20_type:  rows = collect_elements_fixed_width(kw.data, widths['3d20']); e_connt_3d20 = e_connt_3d20 + rows

        elif kw.name == 'elset':
            elsets_raw.append(kw)
        elif kw.name == 'distribution':
            distributions.append(kw)
        elif kw.name == 'orientation':
            orientations.append(kw)
        elif kw.name == 'solidsection' or kw.name == 'shellsection':
            lid += 1
            lname = kw.parameter['elset']
            lyt_name2id[lname] = lid
            sections.append(kw)
        elif kw.name == 'material':
            mid += 1
            mname = kw.parameter['name']
            mtr_name2id[mname] = mid
            materials.append(kw)
        elif kw.name == 'density':
            densities.append(kw)
        elif kw.name == 'elastic':
            elastics.append(kw)

    e_connt_2d = {3:e_connt_2d3, 4:e_connt_2d4, 6:e_connt_2d6, 8:e_connt_2d8}
    e_connt_3d = {4:e_connt_3d4, 6:e_connt_3d6, 8:e_connt_3d8, 10:e_connt_3d10, 15:e_connt_3d15, 20:e_connt_3d20}

    elsets = {}
    for elset in elsets_raw:
        name = elset.parameter['elset']
        if 'generate' in elset.parameter:
            start, stop, step = to_list(elset.data[0])
            elsets[name] = list(range(int(start), int(stop)+1, int(step)))
        else:
            flat = []
            for row in to_list(elset.data):
                for v in to_list(row):
                    if v is None: continue
                    try: flat.append(int(v))
                    except Exception: pass
            elsets[name] = flat

    return {
        'nsg': nsg,
        'nodes': n_coord,
        'elements 2d': e_connt_2d,
        'elements 3d': e_connt_3d,
        'element sets': elsets,
        'sections': sections,
        'distribution': distributions,
        'orientation': orientations,
        'materials': materials,
        'densities': densities,
        'elastics': elastics
    }
