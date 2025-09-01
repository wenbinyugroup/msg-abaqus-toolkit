import os

def reorgAbaqusInput(
    nsg,
    nodes, elements2d, elements3d, elsets,
    sections, distributions, orientations,
    materials, densities, elastics,
    trans_flag
):
    material_type = {
        'ISOTROPIC': 0,
        'ENGINEERINGCONSTANTS': 1,
        'ORTHOTROPIC': 2,
        'ANISOTROPIC': 2
    }

    def to_list(a):
        try:
            return a.tolist()
        except Exception:
            return list(a)

    n_coord = nodes

    mtr_id = 0
    mtr = {}
    mtr_name2id = {}
    for i in range(len(materials)):
        mname_raw = str(materials[i].parameter.get('name', '')).strip()
        if not mname_raw:
            raise ValueError(f"material[{i}] has no name")
        mname_key = mname_raw.upper()
        mtr_id += 1
        mtr_name2id[mname_key] = mtr_id
        try:
            mtr_type_str = elastics[i].parameter['type'] if i < len(elastics) and elastics[i] is not None else 'ISOTROPIC'
        except KeyError:
            mtr_type_str = 'ISOTROPIC'
        mtr_type = material_type.get(str(mtr_type_str).upper(), 0)
        mtr[mtr_id] = {'isotropy': mtr_type, 'ntemp': 1, 'elastic': []}

        # Density
        if i < len(densities) and densities[i] and densities[i].data:
            try:
                rho = float(densities[i].data[0][0])
            except Exception as e:
                raise ValueError(f"density parse failed for material '{mname_raw}': {e}")
        else:
            print(f"!! density missing for material '{mname_raw}', defaulting to 0.0")
            rho = 0.0

        # Elastic constants
        els = []
        if i < len(elastics) and elastics[i] and getattr(elastics[i], 'data', None):
            for j in elastics[i].data:
                for k in j:
                    if k is not None:
                        try:
                            els.append(float(k))
                        except Exception as e:
                            raise ValueError(f"elastic constant '{k}' not numeric for '{mname_raw}': {e}")
        else:
            raise ValueError(f"elastic block missing for material '{mname_raw}'")

        if mtr_type == 0:
            elastic = els
        elif mtr_type == 1:
            if len(els) < 9:
                raise ValueError(f"ENGINEERINGCONSTANTS for '{mname_raw}' has {len(els)} values (<9)")
            elastic = [els[0], els[1], els[2], els[6], els[7], els[8], els[3], els[4], els[5]]
        elif mtr_type == 2:
            if len(els) == 9:
                elastic = [
                    els[0], els[1], els[3], 0.0, 0.0, 0.0,
                            els[2], els[4], 0.0, 0.0, 0.0,
                                    els[5], 0.0, 0.0, 0.0,
                                            els[8], 0.0, 0.0,
                                                    els[7], 0.0,
                                                            els[6]
                ]
            elif len(els) == 21:
                elastic = [
                    els[0], els[1], els[3], els[15], els[10], els[6],
                            els[2], els[4], els[16], els[11], els[7],
                                    els[5], els[17], els[12], els[8],
                                            els[20], els[19], els[18],
                                                     els[14], els[13],
                                                              els[9]
                ]
            else:
                raise ValueError(f"ORTHO/ANISO for '{mname_raw}' has unexpected length {len(els)} (expected 9 or 21)")
        else:
            elastic = els
        mtr[mtr_id]['elastic'].append([0.0, rho] + list(elastic))

    # Orientations
    ori_deg = {}
    for o in orientations:
        name = o.parameter.get('name', '')
        ang = 0.0
        if getattr(o, 'data', None):
            done = False
            for row in o.data:
                for v in row:
                    try:
                        ang = float(v)
                        done = True
                        break
                    except Exception:
                        pass
                if done:
                    break
        ori_deg[name] = ang

    # Distributions
    dist_by_name = {}
    for d in distributions:
        dname = d.parameter.get('name', '')
        if getattr(d, 'data', None):
            rows = d.data[1:] if len(d.data) else []
            if rows:
                maxlen = max(len(r) for r in rows)
                padded = []
                for r in rows:
                    rr = [x for x in r if x is not None]
                    rr = rr + [0.0] * (maxlen - len(rr))
                    try:
                        rr = [float(x) for x in rr]
                    except Exception as e:
                        raise ValueError(f"distribution '{dname}' row parse failed: {r} ({e})")
                    if rr:
                        padded.append(rr)
                arr = padded
            else:
                arr = []
        else:
            arr = []
        dist_by_name[dname] = arr

    eid_lid = {}
    lyt = []
    lid_map = {}
    def get_lid(mid, angle):
        key = (mid, float(angle))
        if key not in lid_map:
            lid = len(lid_map) + 1
            lid_map[key] = lid
            lyt.append([lid, mid, float(angle)])
        return lid_map[key]

    def _elem_angle_for(name, eid, base):
        arr = dist_by_name.get(name, [])
        if arr:
            for row in arr:
                try:
                    if int(row[0]) == int(eid):
                        return base + float(row[-1])
                except Exception:
                    continue
        return base

    # elements that have no composite/orientation but need identity transform
    plain_eids = set()

    for s in sections:
        elset_key = s.parameter['elset']
        if elset_key not in elsets:
            raise ValueError(f"section refers to missing elset '{elset_key}'")

        es   = elsets[elset_key]
        onam = s.parameter.get('orientation', '')
        base = ori_deg.get(onam, 0.0)
        params = {k.lower(): v for k, v in s.parameter.items()}

        if trans_flag == 0:
            if ('composite' in params) or ('orientation' in params):
                raise ValueError("Composite layup or orientation detected but elemental orientation is Global. Please set elemental orientation to Local.")
            mraw = str(s.parameter.get('material', '')).strip()
            mkey = mraw.upper()
            if   mkey in mtr_name2id: mid = mtr_name2id[mkey]
            elif mraw in mtr_name2id: mid = mtr_name2id[mraw]
            else:
                raise ValueError(f"section material not found: '{mraw}'")
            for e in es:
                eid_lid[int(e)] = mid

        else:
            if 'composite' in params:
                rows = getattr(s, 'data', []) or []
                ply_row = None
                for r in rows:
                    rr = [x for x in r if x is not None]
                    if len(rr) >= 4:
                        ply_row = rr
                        break
                if ply_row is None:
                    raise ValueError(f"no usable ply row found in composite section '{elset_key}'")

                mat_raw = str(ply_row[2]).strip()
                mat_key = mat_raw.upper()
                if   mat_key in mtr_name2id: mid = mtr_name2id[mat_key]
                elif mat_raw in mtr_name2id: mid = mtr_name2id[mat_raw]
                else:
                    raise ValueError(f"composite ply material not found: raw='{mat_raw}' upper='{mat_key}' available={sorted(mtr_name2id.keys())}")

                try:
                    ang = float(ply_row[3])
                except Exception as e:
                    raise ValueError(f"composite ply angle not found or not numeric in section '{elset_key}': {e}")

                lid = get_lid(mid, ang)
                for e in es:
                    eid_lid[int(e)] = lid

            elif 'orientation' in params:
                raise ValueError(f"Orientations are currently not supported by SwiftComp. Please use Composite Layups to define orientations.")

            else:
                mraw = str(s.parameter.get('material', '')).strip()
                mkey = mraw.upper()
                if   mkey in mtr_name2id: mid = mtr_name2id[mkey]
                elif mraw in mtr_name2id: mid = mtr_name2id[mraw]
                else:
                    raise ValueError(f"section material not found: '{mraw}'")
                lid = get_lid(mid, 0.0)
                for e in es:
                    eid = int(e)
                    eid_lid[eid] = lid
                    plain_eids.add(eid)

    def rows_from_block(block):
        out = []
        if block is None:
            return out
        try:
            block = to_list(block)
        except Exception:
            block = list(block)
        for row in block:
            r = to_list(row)
            try:
                r = [int(x) for x in r if x is not None]
            except Exception as e:
                raise ValueError(f"element row parse failed: {row} ({e})")
            if r:
                out.append(r)
        return out

    e_connt_2d3  = rows_from_block(elements2d.get(3, []))
    e_connt_2d4  = rows_from_block(elements2d.get(4, []))
    e_connt_2d6  = rows_from_block(elements2d.get(6, []))
    e_connt__2d8 = rows_from_block(elements2d.get(8, []))

    e_connt_3d4  = rows_from_block(elements3d.get(4, []))
    e_connt_3d6  = rows_from_block(elements3d.get(6, []))
    e_connt_3d8  = rows_from_block(elements3d.get(8, []))
    e_connt_3d10 = rows_from_block(elements3d.get(10, []))
    e_connt_3d15 = rows_from_block(elements3d.get(15, []))
    e_connt_3d20 = rows_from_block(elements3d.get(20, []))

    def drop_zero_eid(rows):
        return [r for r in rows if len(r) > 0 and int(r[0]) != 0]

    e_connt_2d3  = drop_zero_eid(e_connt_2d3)
    e_connt_2d4  = drop_zero_eid(e_connt_2d4)
    e_connt_2d6  = drop_zero_eid(e_connt_2d6)
    e_connt_2d8  = drop_zero_eid(e_connt__2d8)
    e_connt_3d4  = drop_zero_eid(e_connt_3d4)
    e_connt_3d6  = drop_zero_eid(e_connt_3d6)
    e_connt_3d8  = drop_zero_eid(e_connt_3d8)
    e_connt_3d10 = drop_zero_eid(e_connt_3d10)
    e_connt_3d15 = drop_zero_eid(e_connt_3d15)
    e_connt_3d20 = drop_zero_eid(e_connt_3d20)

    def pad2d(rows):
        out = []
        for r in rows:
            rr = r + [0] * (9 - len(r))
            out.append(rr[:9])
        return out

    def pad3d(rows):
        out = []
        for r in rows:
            rr = r + [0] * (21 - len(r))
            out.append(rr[:21])
        return out

    e2d = []
    if e_connt_2d3:
        e2d += pad2d(e_connt_2d3)
    if e_connt_2d4:
        e2d += pad2d(e_connt_2d4)
    if e_connt_2d6:
        ins = []
        for r in e_connt_2d6:
            rr = r[:4] + [0] + r[4:]
            ins.append(rr)
        e2d += pad2d(ins)
    if e_connt__2d8:
        e2d += pad2d(e_connt__2d8)
    elements2d_list = e2d

    e3d = []
    if e_connt_3d4:
        e3d += pad3d(e_connt_3d4)
    if e_connt_3d8:
        e3d += pad3d(e_connt_3d8)
    if e_connt_3d10:
        ins = []
        for r in e_connt_3d10:
            rr = r[:6] + [0] + r[6:]
            ins.append(rr)
        e3d += pad3d(ins)
    if e_connt_3d20:
        e3d += pad3d(e_connt_3d20)
    if e_connt_3d6:
        e3d += pad3d(e_connt_3d6)
    if e_connt_3d15:
        ins = []
        for r in e_connt_3d15:
            eid   = [r[0]]
            nodes = r[1:16]
            order = [0,1,2, 3,4,5, 6,7,8, 9,10,11, 12,13,14]
            nodes = [nodes[i] for i in order]
            keep  = eid + nodes
            keep  = keep[:7] + [0] + keep[7:]
            ins.append(keep)
        e3d += pad3d(ins)
    elements3d_list = e3d

    # count elements
    nelem = len(elements2d_list) + len(elements3d_list)

    # renumber element labels to be contiguous starting at 1
    blocks = [elements2d_list, elements3d_list]
    new_id = 1
    id_map = {}
    for blk in blocks:
        for r in blk:
            old = int(r[0])
            if old not in id_map:
                id_map[old] = new_id
                new_id += 1
            r[0] = id_map[old]

    # update mappings that depend on element id
    eid_lid = {id_map[e]: lid for e, lid in eid_lid.items() if e in id_map}

    # build distributions (and add identities for material-only elements if needed)
    distr_all = []
    need_cols = 7 if int(nsg) == 3 else 4
    rows = []
    for distr in distributions:
        if getattr(distr, 'data', None):
            for row in distr.data[1:]:
                flat = []
                for v in row:
                    if v is None:
                        continue
                    try:
                        flat.append(float(v))
                    except Exception as e:
                        raise ValueError(f"distribution value '{v}' not numeric: {e}")
                if not flat:
                    continue
                eid = int(flat[0])
                rest = (flat[1:] + [0.0] * (need_cols - 1))[:need_cols - 1]
                rows.append([eid] + rest)

    # ensure identity transforms for elements without composite/orientation
    if trans_flag != 0 and plain_eids:
        have = {int(r[0]) for r in rows}
        missing = sorted(e for e in plain_eids if e not in have)
        if int(nsg) == 3:
            rows.extend([[float(e), 1.0, 0.0, 0.0, 0.0, 1.0, 0.0] for e in missing])
        else:
            rows.extend([[float(e), 0.0, 1.0, 0.0] for e in missing])

    if rows:
        seen = set()
        dedup = []
        for r in rows:
            if r[0] not in seen:
                seen.add(r[0])
                dedup.append(r)
        if int(nsg) == 2:
            out = []
            for r in dedup:
                r2 = r[:1] + [1.0, 0.0, 0.0] + r[1:]
                out.append(r2)
            dedup = out
        for i in range(len(dedup)):
            dedup[i] = dedup[i] + [0.0, 0.0, 0.0]
        # apply renumber mapping for distributions
        for r in dedup:
            e_old = int(r[0])
            if e_old in id_map:
                r[0] = id_map[e_old]
        distr_all = dedup

    # rebuild all element ids
    eid_all = list(range(1, nelem + 1))

    return {
        'nodes': n_coord,
        'all elements ids': eid_all,
        'element to layer type': eid_lid,
        'elements 2d': elements2d_list,
        'elements 3d': elements3d_list,
        'distributions': distr_all,
        'layer types': lyt,
        'materials': mtr
    }
