# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from symbolicConstants import *
from utils.utilities import *
from main import utilities_abq as uab
from utils import abq_view
import numpy as np
from sg.offset_side import decide_side_dotproduct, decide_side_crossproduct


# Default factory for each per-model laminate state key.
_MODEL_KEY_DEFAULTS = (
    ('mtrId-Name',  dict),
    ('mtrName-Id',  dict),
    ('Layer types', dict),
)

# Default factory for each per-part laminate state key.
_PART_KEY_DEFAULTS = (
    ('Set name',                  list),
    ('Set-FacePoint',             dict),
    ('Set-SectionAssignment id',  dict),
    ('Set id',                    lambda: 1),
    ('Sketch name',               str),
    ('Partition feature name',    str),
    ('Baseline',                  list),
    ('Baseline id',               lambda: 1),
    ('Interface line id',         dict),
    ('Layer face set name',       dict),
)


def _load_laminate_state(model_name, part_name):
    """Load or initialize laminate state from ``mdb.customData.models``.

    Returns
    -------
    cst_models : dict
        Top-level container; pass back to :func:`_save_laminate_state`.
    cst_model : dict
        Per-model state with all required keys present.
    cst_part : dict
        Per-part state with all required keys present.

    Notes
    -----
    Mutable values (dicts, lists) are returned by reference, so the caller
    may mutate them in place. Scalar fields (``Set id``, ``Baseline id``,
    ``Sketch name``, ``Partition feature name``) must be re-assigned into
    ``cst_part`` before saving.
    """
    try:
        cst_models = mdb.customData.models
    except AttributeError:
        cst_models = {}
    cst_model = cst_models.setdefault(model_name, {})
    for key, factory in _MODEL_KEY_DEFAULTS:
        cst_model.setdefault(key, factory())
    cst_parts = cst_model.setdefault('Parts', {})
    cst_part = cst_parts.setdefault(part_name, {})
    for key, factory in _PART_KEY_DEFAULTS:
        cst_part.setdefault(key, factory())
    return cst_models, cst_model, cst_part


def _save_laminate_state(cst_models):
    """Persist laminate state back to ``mdb.customData.models``."""
    mdb.customData.models = cst_models


# ---------------------------------------------------------------------------
# Topology helpers
# ---------------------------------------------------------------------------

def _classify_topology(p, area, baseline, opposite):
    """Find boundary edges and optional opposite-edge data for a laminate region.

    Parameters
    ----------
    p : Part
    area : Face
    baseline : Edge
    opposite : Edge or None

    Returns
    -------
    bd1_id : int
    bd2_id : int
    bl_pt : tuple
        ``pointOn`` coordinate of the baseline edge.
    bd1_pt : tuple
        ``pointOn`` coordinate of boundary edge 1.
    bd2_pt : tuple
        ``pointOn`` coordinate of boundary edge 2.
    ob_id : int or None
    ob_pt : tuple or None

    Raises
    ------
    ValueError
        If the baseline endpoint is not topologically connected to either
        boundary edge.
    """
    e = p.edges
    eids = list(area.getEdges())
    eids.remove(baseline.index)

    vs_bl = baseline.getVertices()
    boundary = []
    for i in eids:
        vs = e[i].getVertices()
        for j in vs:
            if j in vs_bl:
                boundary.append(i)

    bd1_id = boundary[0]
    bd2_id = boundary[1]
    bl_pt  = baseline.pointOn[0]
    bd1_pt = e[bd1_id].pointOn[0]
    bd2_pt = e[bd2_id].pointOn[0]

    # Validate topology.
    vs_bd1 = e[bd1_id].getVertices()
    vs_bd2 = e[bd2_id].getVertices()
    v1_id = vs_bl[1]
    if v1_id not in vs_bd1 and v1_id not in vs_bd2:
        raise ValueError(
            "baseline end vertex is not on either boundary edge; "
            "the laminate region topology is invalid."
        )

    ob_id = ob_pt = None
    if opposite is not None:
        ob_id = opposite.index
        ob_pt = opposite.pointOn[0]

    return bd1_id, bd2_id, bl_pt, bd1_pt, bd2_pt, ob_id, ob_pt


def _register_section_per_layer(model, layup, mid_name, mname_id, layer_types):
    """Create a HomogeneousShellSection for each layer and return layer data.

    Parameters
    ----------
    model : Model
    layup : sequence of layer objects from a composite section
    mid_name : dict  (mutated in place)
    mname_id : dict  (mutated in place)
    layer_types : dict  (mutated in place)

    Returns
    -------
    layer_thicknesses : list of float
    layer_section_names : list of str
    total_thickness : float
    """
    layer_thicknesses = []
    layer_section_names = []
    total_thickness = 0.0
    for layer in layup:
        tk = layer.thickness
        layer_thicknesses.append(tk)
        total_thickness += tk
        mn = layer.material
        ag = layer.orientAngle
        if mn not in list(mid_name.values()):
            n = len(mid_name)
            mid_name[n + 1] = mn
            mname_id[mn] = n + 1
        mid = mname_id[mn]
        ma = [mid, ag]
        sn = mn + '_' + str(ag)
        layer_section_names.append(sn)
        if ma not in list(layer_types.values()):
            n = len(layer_types)
            layer_types[n + 1] = ma
            model.HomogeneousShellSection(name=sn, material=mn, thickness=1.0)
    return layer_thicknesses, layer_section_names, total_thickness


def _ensure_sketch(model, p, s_name):
    """Return an existing partition sketch or create a new one.

    Parameters
    ----------
    model : Model
    p : Part
    s_name : str

    Returns
    -------
    s : ConstrainedSketch
    """
    try:
        return model.sketches[s_name]
    except KeyError:
        f, d = p.faces, p.datums
        t = p.MakeSketchTransform(
            sketchPlane=f[0], sketchUpEdge=d[2],
            sketchPlaneSide=SIDE1, origin=(0.0, 0.0, 0.0)
        )
        return model.ConstrainedSketch(name=s_name, sheetSize=500.0, transform=t)


def _project_edges_to_sketch(s, p, bl_id, bd1_id, bd2_id, bl_pt, bd1_pt, bd2_pt,
                              ob_id, ob_pt):
    """Project part edges onto the partition sketch and return key geometry.

    Parameters
    ----------
    s : ConstrainedSketch
    p : Part
    bl_id, bd1_id, bd2_id : int
        Edge indices for baseline and both boundary edges.
    bl_pt, bd1_pt, bd2_pt : tuple
        ``pointOn`` coordinates used for geometry lookup.
    ob_id : int or None
    ob_pt : tuple or None

    Returns
    -------
    baseline_sk : sketch geometry object
    bound0_sk : sketch geometry object
    bound1_sk : sketch geometry object
    opposite_sk : sketch geometry object or None
    pt0, pt1 : tuple
        3-tuples (0.0, y, z) of the baseline sketch endpoints.
    pt2 : tuple
        3-tuple of the boundary vertex adjacent to pt1 (direction indicator).
    """
    e = p.edges
    g = s.geometry

    baseline_sk = g.findAt(coordinates=(bl_pt[1], bl_pt[2]), printWarning=False)
    if baseline_sk is None:
        p.projectEdgesOntoSketch(sketch=s, edges=(e[bl_id],))
        baseline_sk = g.findAt(coordinates=(bl_pt[1], bl_pt[2]))
    pt0 = (0.0,) + tuple(baseline_sk.getVertices()[0].coords)
    pt1 = (0.0,) + tuple(baseline_sk.getVertices()[1].coords)

    bound0_sk = g.findAt(coordinates=(bd1_pt[1], bd1_pt[2]), printWarning=False)
    if bound0_sk is None:
        p.projectEdgesOntoSketch(sketch=s, edges=(e[bd1_id],))
        bound0_sk = g.findAt(coordinates=(bd1_pt[1], bd1_pt[2]))
    bound0_v0 = (0.0,) + tuple(bound0_sk.getVertices()[0].coords)
    bound0_v1 = (0.0,) + tuple(bound0_sk.getVertices()[1].coords)

    bound1_sk = g.findAt(coordinates=(bd2_pt[1], bd2_pt[2]), printWarning=False)
    if bound1_sk is None:
        p.projectEdgesOntoSketch(sketch=s, edges=(e[bd2_id],))
        bound1_sk = g.findAt(coordinates=(bd2_pt[1], bd2_pt[2]))
    bound1_v0 = (0.0,) + tuple(bound1_sk.getVertices()[0].coords)
    bound1_v1 = (0.0,) + tuple(bound1_sk.getVertices()[1].coords)

    opposite_sk = None
    if ob_id is not None:
        opposite_sk = g.findAt(coordinates=(ob_pt[1], ob_pt[2]), printWarning=False)
        if opposite_sk is None:
            p.projectEdgesOntoSketch(sketch=s, edges=(e[ob_id],))
            opposite_sk = g.findAt(coordinates=(ob_pt[1], ob_pt[2]))

    # pt2: the boundary vertex adjacent to pt1, used as direction indicator.
    if pt1 == bound0_v0:
        pt2 = bound0_v1
    elif pt1 == bound0_v1:
        pt2 = bound0_v0
    elif pt1 == bound1_v0:
        pt2 = bound1_v1
    else:
        pt2 = bound1_v0

    return baseline_sk, bound0_sk, bound1_sk, opposite_sk, pt0, pt1, pt2


# ---------------------------------------------------------------------------
# Layer partitioning helpers
# ---------------------------------------------------------------------------

def _partition_layers_linear(s, baseline_sk, bound0_sk, bound1_sk,
                              pt0, pt1, pt2,
                              layer_thicknesses, layer_section_names):
    """Offset and trim a straight baseline to partition laminate layers.

    Parameters
    ----------
    s : ConstrainedSketch
    baseline_sk : sketch geometry
    bound0_sk, bound1_sk : sketch geometry
    pt0, pt1 : tuple
        Baseline sketch endpoints.
    pt2 : tuple
        Direction indicator (adjacent boundary vertex to pt1).
    layer_thicknesses : list of float
    layer_section_names : list of str

    Returns
    -------
    fpt_section : list of [fpt, section_name]
    interface_key_ids : list of list of int
        Sketch geometry key id(s) for each inter-layer interface line.
    """
    fpt_section = []
    interface_key_ids = []
    accumulated_thickness = 0.0
    check_side = True
    offset_side = 'LEFT'

    for i, tk in enumerate(layer_thicknesses):
        milestone('Layer: ' + str(i + 1))
        accumulated_thickness += tk / 2.0

        if offset_side == 'LEFT':
            s.offset(objectList=(baseline_sk,), distance=accumulated_thickness, side=LEFT)
        else:
            s.offset(objectList=(baseline_sk,), distance=accumulated_thickness, side=RIGHT)
        if check_side:
            offset_side = checkOffsetSide2(s, pt0, pt1, pt2, baseline_sk,
                                           accumulated_thickness)
            check_side = False

        try:
            g = s.geometry
            tline_id = list(g.keys())[-1]
            s.trimExtendCurve(
                curve1=g[tline_id], point1=g[tline_id].pointOn,
                curve2=bound0_sk, point2=bound0_sk.pointOn
            )
        except Exception:
            pass
        try:
            g = s.geometry
            tline_id = list(g.keys())[-1]
            s.trimExtendCurve(
                curve1=g[tline_id], point1=g[tline_id].pointOn,
                curve2=bound1_sk, point2=bound1_sk.pointOn
            )
        except Exception:
            pass

        g = s.geometry
        tline_id = list(g.keys())[-1]
        tline = g[tline_id]
        fpt = (0.0,) + tline.getPointAtDistance(
            point=tline.getVertices()[0].coords, distance=50, percentage=True
        )
        fpt_section.append([fpt, layer_section_names[i]])
        s.delete(objectList=(tline,))

        if i < len(layer_thicknesses) - 1:
            accumulated_thickness += tk / 2.0
            if offset_side == 'LEFT':
                s.offset(objectList=(baseline_sk,), distance=accumulated_thickness, side=LEFT)
            else:
                s.offset(objectList=(baseline_sk,), distance=accumulated_thickness, side=RIGHT)
            try:
                g = s.geometry
                tline_id = list(g.keys())[-1]
                s.trimExtendCurve(
                    curve1=g[tline_id], point1=g[tline_id].pointOn,
                    curve2=bound0_sk, point2=bound0_sk.pointOn
                )
            except Exception:
                pass
            try:
                g = s.geometry
                tline_id = list(g.keys())[-1]
                s.trimExtendCurve(
                    curve1=g[tline_id], point1=g[tline_id].pointOn,
                    curve2=bound1_sk, point2=bound1_sk.pointOn
                )
            except Exception:
                pass
            g = s.geometry
            interface_key_ids.append([list(g.keys())[-1]])

    return fpt_section, interface_key_ids


def _partition_layers_curved(s, baseline_sk, opposite_sk, bound0_sk, bound1_sk,
                              pt0, pt1,
                              layer_thicknesses, layer_section_names,
                              total_thickness, nsp):
    """Extend a curved baseline to cover the full laminate depth and partition layers.

    Offsets ``opposite_sk`` to build a reference curve, optionally extends the
    baseline spline, then runs the same offset/break/clip loop as the linear path.

    Parameters
    ----------
    s : ConstrainedSketch
    baseline_sk : sketch geometry  (original baseline curve, used as reference)
    opposite_sk : sketch geometry  (opposite boundary curve)
    bound0_sk, bound1_sk : sketch geometry  (two boundary edges)
    pt0, pt1 : tuple
        Baseline sketch endpoints (3-tuples with leading 0.0).
    layer_thicknesses : list of float
    layer_section_names : list of str
    total_thickness : float
    nsp : int
        Number of sampling points (already validated as 1–100).

    Returns
    -------
    fpt_section : list of [fpt, section_name]
    interface_key_ids : list of list of int
    """
    spline_constrain = True

    # --- Phase 1: sample baseline and offset-opposite curves ----------------
    s.offset(objectList=(opposite_sk,), distance=total_thickness, side=LEFT)
    # checkOffsetSide has a side effect: re-offsets to the correct side if needed.
    checkOffsetSide(s, pt1, pt0, opposite_sk, total_thickness)
    g = s.geometry
    oob = g[list(g.keys())[-1]]  # offset-opposite boundary

    sbl_vs  = baseline_sk.getVertices()
    sbl_pt1 = sbl_vs[0].coords
    sbl_pt2 = sbl_vs[1].coords
    oob_vs  = oob.getVertices()
    oob_pt1 = oob_vs[0].coords
    oob_pt2 = oob_vs[1].coords

    sbl_pts = [sbl_pt1]
    oob_pts = [oob_pt1]
    for i in range(1, 100, 100 // nsp):
        sbl_pts.append(baseline_sk.getPointAtDistance(point=sbl_pt1, distance=i, percentage=True))
        oob_pts.append(oob.getPointAtDistance(point=oob_pt1, distance=i, percentage=True))
    sbl_pts.append(sbl_pt2)
    oob_pts.append(oob_pt2)

    sbl_len = baseline_sk.getSize()
    oob_len = oob.getSize()
    sbl_r   = sbl_len / nsp / 2.0
    oob_r   = oob_len / nsp / 2.0

    # Identify which oob endpoints are near baseline endpoints.
    oob_kp = {}
    for i, pt in enumerate(oob_pts):
        x0, y0 = pt[0], pt[1]
        d1 = np.sqrt((sbl_pt1[0] - x0) ** 2 + (sbl_pt1[1] - y0) ** 2)
        d2 = np.sqrt((sbl_pt2[0] - x0) ** 2 + (sbl_pt2[1] - y0) ** 2)
        if d1 < oob_r:
            oob_kp[1] = [i, pt]
        if d2 < oob_r:
            oob_kp[2] = [i, pt]

    # --- Phase 2: build the working baseline (sbl) --------------------------
    sbl = baseline_sk
    if len(oob_kp) == 0 or len(oob_kp) == 2:
        if oob_len > sbl_len:
            sbl = oob
    elif len(oob_kp) == 1:
        oob_kp_id = list(oob_kp.values())[0][0]
        kp_id = None
        for i, pt in enumerate(sbl_pts):
            x0, y0 = pt[0], pt[1]
            d1 = np.sqrt((oob_pt1[0] - x0) ** 2 + (oob_pt1[1] - y0) ** 2)
            d2 = np.sqrt((oob_pt2[0] - x0) ** 2 + (oob_pt2[1] - y0) ** 2)
            if d1 < sbl_r:
                kp_id = 0
            if d2 < sbl_r:
                kp_id = -1
        if kp_id is None:
            raise ValueError(
                "cannot locate opposite-edge endpoint on the baseline "
                "within sampling tolerance; check geometry or increase nsp."
            )
        sbl_vec = np.array((0.0,) + sbl_pt2) - np.array((0.0,) + sbl_pt1)
        oob_vec = np.array((0.0,) + oob_pt2) - np.array((0.0,) + oob_pt1)
        dp_ext  = np.dot(sbl_vec, oob_vec)
        if kp_id == 0:
            sbl_pts_extra = oob_pts[oob_kp_id + 1:]
            if dp_ext > 0.0:
                sbl_pts = sbl_pts + sbl_pts_extra
                pt0 = (0.0,) + sbl_pts[-1]
            elif dp_ext < 0.0:
                sbl_pts = list(reversed(sbl_pts_extra)) + sbl_pts
        elif kp_id == -1:
            sbl_pts_extra = oob_pts[:oob_kp_id - 1]
            if dp_ext > 0.0:
                sbl_pts = sbl_pts_extra + sbl_pts
            elif dp_ext < 0.0:
                sbl_pts = sbl_pts + list(reversed(sbl_pts_extra))
                pt0 = (0.0,) + sbl_pts[-1]
        sbl = s.Spline(points=sbl_pts, constrainPoints=spline_constrain)

    # --- Phase 3: compute direction and reorder boundaries ------------------
    vs_sbl0 = baseline_sk.getVertices()
    vs_sbl1 = sbl.getVertices()
    vec_sbl0 = np.array(vs_sbl0[1].coords) - np.array(vs_sbl0[0].coords)
    vec_sbl1 = np.array(vs_sbl1[1].coords) - np.array(vs_sbl1[0].coords)
    dp = np.dot(vec_sbl0, vec_sbl1)

    sbd0 = bound0_sk
    sbd1 = bound1_sk
    if vs_sbl0[0] in sbd1.getVertices():
        sbd0, sbd1 = sbd1, sbd0

    # --- Phase 4: layer loop ------------------------------------------------
    fpt_section = []
    interface_key_ids = []
    accumulated_thickness = 0.0
    check_side = True
    offset_side = 'LEFT'

    for i, tk in enumerate(layer_thicknesses):
        milestone('Layer: ' + str(i + 1))
        accumulated_thickness += tk / 2.0

        if offset_side == 'LEFT':
            s.offset(objectList=(sbl,), distance=accumulated_thickness, side=LEFT)
        else:
            s.offset(objectList=(sbl,), distance=accumulated_thickness, side=RIGHT)
        if check_side:
            offset_side = checkOffsetSide(s, pt0, pt1, sbl, accumulated_thickness)
            check_side = False

        try:
            g = s.geometry
            tline_id = list(g.keys())[-1]
            s.breakCurve(curve1=g[tline_id], point1=g[tline_id].pointOn,
                         curve2=sbd0, point2=sbd0.pointOn)
            g = s.geometry
            if dp > 0.0:
                s.delete(objectList=(g[list(g.keys())[-2]],))
            elif dp < 0.0:
                s.delete(objectList=(g[list(g.keys())[-1]],))
        except Exception:
            pass

        try:
            g = s.geometry
            tline_id = list(g.keys())[-1]
            s.breakCurve(curve1=g[tline_id], point1=g[tline_id].pointOn,
                         curve2=sbd1, point2=sbd1.pointOn)
            g = s.geometry
            if dp > 0.0:
                s.delete(objectList=(g[list(g.keys())[-1]],))
            elif dp < 0.0:
                s.delete(objectList=(g[list(g.keys())[-2]],))
        except Exception:
            pass

        g = s.geometry
        tline_id = list(g.keys())[-1]
        tline = g[tline_id]
        fpt = (0.0,) + tline.getPointAtDistance(
            point=tline.getVertices()[0].coords, distance=50, percentage=True
        )
        fpt_section.append([fpt, layer_section_names[i]])
        s.delete(objectList=(tline,))

        if i < len(layer_thicknesses) - 1:
            temp = []
            accumulated_thickness += tk / 2.0
            if offset_side == 'LEFT':
                s.offset(objectList=(sbl,), distance=accumulated_thickness, side=LEFT)
            else:
                s.offset(objectList=(sbl,), distance=accumulated_thickness, side=RIGHT)

            g = s.geometry
            ledge_id = list(g.keys())[-1]
            temp.append(ledge_id)

            try:
                s.breakCurve(curve1=g[ledge_id], point1=g[ledge_id].pointOn,
                             curve2=sbd0, point2=sbd0.pointOn)
                g = s.geometry
                if dp > 0.0:
                    s.delete(objectList=(g[list(g.keys())[-2]],))
                elif dp < 0.0:
                    s.delete(objectList=(g[list(g.keys())[-1]],))
                g = s.geometry
                ledge_id = list(g.keys())[-1]
                temp[-1] = ledge_id
            except Exception:
                g = s.geometry
                tline_id = list(g.keys())[-1]
                tline_vs = g[tline_id].getVertices()
                tline_pt0 = tline_vs[0].coords
                tline_pt1 = tline_vs[1].coords
                if dp > 0.0:
                    ext_pt = (tline_pt0[0] + (tline_pt0[0] - tline_pt1[0]),
                              tline_pt0[1] + (tline_pt0[1] - tline_pt1[1]))
                    s.Line(point1=tline_pt0, point2=ext_pt)
                elif dp < 0.0:
                    ext_pt = (tline_pt1[0] + (tline_pt1[0] - tline_pt0[0]),
                              tline_pt1[1] + (tline_pt1[1] - tline_pt0[1]))
                    s.Line(point1=tline_pt1, point2=ext_pt)
                g = s.geometry
                sline_id = list(g.keys())[-1]
                s.FixedConstraint(entity=g[tline_id])
                s.TangentConstraint(entity1=g[tline_id], entity2=g[sline_id])
                try:
                    s.breakCurve(curve1=g[sline_id], point1=g[sline_id].pointOn,
                                 curve2=sbd0, point2=sbd0.pointOn)
                    temp.append(list(s.geometry.keys())[-2])
                except Exception:
                    pass
                g = s.geometry
                s.delete(objectList=(g[list(g.keys())[-1]],))

            try:
                s.breakCurve(curve1=g[ledge_id], point1=g[ledge_id].pointOn,
                             curve2=sbd1, point2=sbd1.pointOn)
                g = s.geometry
                if dp > 0.0:
                    s.delete(objectList=(g[list(g.keys())[-1]],))
                elif dp < 0.0:
                    s.delete(objectList=(g[list(g.keys())[-2]],))
                g = s.geometry
                temp.remove(ledge_id)
                ledge_id = list(g.keys())[-1]
                temp.append(ledge_id)
            except Exception:
                g = s.geometry
                tline_id = list(g.keys())[-1]
                tline_vs = g[tline_id].getVertices()
                tline_pt0 = tline_vs[0].coords
                tline_pt1 = tline_vs[1].coords
                if dp > 0.0:
                    ext_pt = (tline_pt1[0] + (tline_pt1[0] - tline_pt0[0]),
                              tline_pt1[1] + (tline_pt1[1] - tline_pt0[1]))
                    s.Line(point1=tline_pt1, point2=ext_pt)
                elif dp < 0.0:
                    ext_pt = (tline_pt0[0] + (tline_pt0[0] - tline_pt1[0]),
                              tline_pt0[1] + (tline_pt0[1] - tline_pt1[1]))
                    s.Line(point1=tline_pt0, point2=ext_pt)
                g = s.geometry
                sline_id = list(g.keys())[-1]
                s.FixedConstraint(entity=g[tline_id])
                s.TangentConstraint(entity1=g[tline_id], entity2=g[sline_id])
                try:
                    s.breakCurve(curve1=g[sline_id], point1=g[sline_id].pointOn,
                                 curve2=sbd1, point2=sbd1.pointOn)
                    temp.append(list(s.geometry.keys())[-2])
                except Exception:
                    pass
                g = s.geometry
                s.delete(objectList=(g[list(g.keys())[-1]],))

            interface_key_ids.append(temp)

    # Cleanup temporary curves used only as offset references.
    s.delete(objectList=(oob,))
    if len(oob_kp) == 1:
        s.delete(objectList=(sbl,))

    return fpt_section, interface_key_ids


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_laminate(baseline, area, model_name, section_name, opposite=None, nsp=20):
    """Add laminate layup partitions to the currently displayed part.

    Parameters
    ----------
    baseline : Edge
        Baseline edge to offset layers from.
    area : Face
        Face region to partition into layers.
    model_name : str
        Name of an existing Abaqus model.
    section_name : str
        Name of an existing composite section in the model.
    opposite : Edge or None
        Required for curved baselines; the edge opposite to the baseline.
    nsp : int
        Number of sampling points (1–100) for curved baselines.

    Notes
    -----
    Side effects: modifies ``mdb.customData.models``, creates Sets,
    SectionAssignments, a ConstrainedSketch, and a PartitionFace feature.

    Raises
    ------
    ValueError
        If ``opposite`` is None for a curved baseline, or if topology is
        invalid, or if ``nsp`` is out of range.
    """
    model = mdb.models[model_name]
    vp = abq_view.current_viewport()
    part_name = abq_view.displayed_part_name(vp)
    p = model.parts[part_name]

    cst_models, cst_model, cst_part = _load_laminate_state(model_name, part_name)
    mid_name     = cst_model['mtrId-Name']
    mname_id     = cst_model['mtrName-Id']
    layer_types  = cst_model['Layer types']
    set_name     = cst_part['Set name']
    set_fpt      = cst_part['Set-FacePoint']
    set_said     = cst_part['Set-SectionAssignment id']
    set_id       = cst_part['Set id']
    blid_pt      = cst_part['Baseline']
    baseline_uid = cst_part['Baseline id']
    sgm_lyr_id   = cst_part['Interface line id']
    sgm_lyr_set  = cst_part['Layer face set name']

    bd1_id, bd2_id, bl_pt, bd1_pt, bd2_pt, ob_id, ob_pt = _classify_topology(
        p, area, baseline, opposite
    )
    blid_pt.append([baseline_uid, bl_pt])

    layup = model.sections[section_name].layup
    layer_thicknesses, layer_section_names, total_thickness = _register_section_per_layer(
        model, layup, mid_name, mname_id, layer_types
    )

    s_name = part_name + '_layer_partition'
    s = _ensure_sketch(model, p, s_name)

    baseline_sk, bound0_sk, bound1_sk, opposite_sk, pt0, pt1, pt2 = \
        _project_edges_to_sketch(
            s, p, baseline.index, bd1_id, bd2_id,
            bl_pt, bd1_pt, bd2_pt, ob_id, ob_pt
        )

    sgm_lyr_id[baseline_uid] = []
    ctype = repr(baseline_sk.curveType)
    if ctype == 'LINE':
        fpt_section, interface_key_ids = _partition_layers_linear(
            s, baseline_sk, bound0_sk, bound1_sk,
            pt0, pt1, pt2,
            layer_thicknesses, layer_section_names
        )
    elif ctype in ('SPLINE', 'ARC', 'CIRCLE', 'ELLIPSE'):
        if opposite is None:
            raise ValueError(
                "curved baseline requires an 'opposite' edge to build the "
                "layer offset reference."
            )
        if nsp <= 0:
            raise ValueError('Number of sampling points must be positive.')
        if nsp > 100:
            raise ValueError('Number of sampling points must not exceed 100.')
        fpt_section, interface_key_ids = _partition_layers_curved(
            s, baseline_sk, opposite_sk, bound0_sk, bound1_sk,
            pt0, pt1,
            layer_thicknesses, layer_section_names,
            total_thickness, nsp
        )
    else:
        raise ValueError('Unsupported baseline curve type: ' + ctype)
    sgm_lyr_id[baseline_uid] = interface_key_ids

    f, d = p.faces, p.datums
    feat_ptt_name = cst_part['Partition feature name']
    try:
        p.features[feat_ptt_name].setValues(sketch=s)
    except KeyError:
        feat = p.PartitionFaceBySketch(faces=f, sketchUpEdge=d[2], sketch=s)
        feat_ptt_name = feat.name
    p.regenerate()

    uab.refreshSets(mdb, model_name, part_name, set_fpt)

    f = p.faces
    sgm_lyr_set[baseline_uid] = []
    for fpt, sn in fpt_section:
        rn = sn.replace('.', 'd') + '/' + str(set_id)
        ff = f.findAt((fpt,))
        rg = p.Set(name=rn, faces=ff)
        p.SectionAssignment(region=rg, sectionName=sn)
        set_name.append(rn)
        set_fpt[rn] = fpt
        set_said[rn] = len(p.sectionAssignments) - 1
        set_id += 1
        sgm_lyr_set[baseline_uid].append(rn)

    baseline_uid += 1
    cst_part['Set id'] = set_id
    cst_part['Sketch name'] = s_name
    cst_part['Partition feature name'] = feat_ptt_name
    cst_part['Baseline id'] = baseline_uid
    _save_laminate_state(cst_models)

    abq_view.apply_color_mapping('Section', vp=vp)


def remove_laminate(baseline, model_name):
    """Remove a previously added laminate partition from the displayed part.

    Parameters
    ----------
    baseline : Edge
        The baseline edge whose associated laminate layers will be removed.
    model_name : str

    Raises
    ------
    ValueError
        If the baseline is not registered in the current part's laminate state.
    """
    model = mdb.models[model_name]
    vp = abq_view.current_viewport()
    part_name = abq_view.displayed_part_name(vp)
    p = model.parts[part_name]

    cst_models, _, cst_part = _load_laminate_state(model_name, part_name)
    set_name      = cst_part['Set name']
    set_fpt       = cst_part['Set-FacePoint']
    set_said      = cst_part['Set-SectionAssignment id']
    feat_ptt_name = cst_part['Partition feature name']
    blid_pt       = cst_part['Baseline']
    sgm_lyr_id    = cst_part['Interface line id']
    sgm_lyr_set   = cst_part['Layer face set name']

    bl_pt  = baseline.pointOn[0]
    s_name = part_name + '_layer_partition'
    s = model.sketches[s_name]
    g = s.geometry

    baseline_uid = None
    index = None
    for i, bl in enumerate(blid_pt):
        if bl_pt == bl[1]:
            baseline_uid = bl[0]
            index = i
    if baseline_uid is None:
        raise ValueError(
            "selected baseline is not registered for this part; "
            "nothing to remove."
        )
    blid_pt.remove(blid_pt[index])

    count_sa_del = 0
    sa = p.sectionAssignments
    for i in sgm_lyr_set[baseline_uid]:
        sa_id = set_said[i] - count_sa_del
        del sa[sa_id]
        set_name.remove(i)
        del p.sets[i]
        del set_fpt[i]
        count_sa_del += 1
    del sgm_lyr_set[baseline_uid]

    for i, rn in enumerate(set_name):
        set_said[rn] = i

    for i in sgm_lyr_id[baseline_uid]:
        for j in i:
            s.delete(objectList=(g[j],))
    del sgm_lyr_id[baseline_uid]

    feat = p.features[feat_ptt_name]
    feat.setValues(sketch=s)
    try:
        p.regenerate()
    except Exception:
        pass

    uab.refreshSets(mdb, model_name, part_name, set_fpt)

    # All state was mutated in place via the references returned from
    # _load_laminate_state; just flush.
    _save_laminate_state(cst_models)

    abq_view.apply_color_mapping('Section', vp=vp)


# ---------------------------------------------------------------------------
# Offset-side decision helpers
# ---------------------------------------------------------------------------

def checkOffsetSide(sketch, point0, point1, line, distance):
    """Check and correct the offset direction using a dot-product test.

    Retrieves the vertex of the most-recently-added offset geometry, calls
    :func:`sg.offset_side.decide_side_dotproduct` to decide the correct side,
    and if the offset landed on the wrong side, deletes it and re-offsets to
    the opposite side.

    Returns
    -------
    offset_side : {'LEFT', 'RIGHT'}
    """
    s   = sketch
    sbl = line
    ttk = distance

    g = s.geometry
    tline_id = list(g.keys())[-1]
    v = g[tline_id].getVertices()
    offset_vertex = (0.0,) + v[1].coords

    offset_side = decide_side_dotproduct(point0, point1, offset_vertex)
    if offset_side == 'RIGHT':
        s.delete(objectList=(g[tline_id],))
        s.offset(objectList=(sbl,), distance=ttk, side=RIGHT)
    return offset_side


def checkOffsetSide2(sketch, point0, point1, point2, line, distance):
    """Check and correct the offset direction using a cross-product test.

    Calls :func:`sg.offset_side.decide_side_crossproduct` to decide the
    correct side.  If the result is ``'RIGHT'``, deletes the last sketch
    geometry and re-offsets to the opposite side.

    Returns
    -------
    offset_side : {'LEFT', 'RIGHT'}
    """
    s   = sketch
    sbl = line
    ttk = distance

    g = s.geometry
    tline_id = list(g.keys())[-1]

    offset_side = decide_side_crossproduct(point0, point1, point2)
    if offset_side == 'RIGHT':
        s.delete(objectList=(g[tline_id],))
        s.offset(objectList=(sbl,), distance=ttk, side=RIGHT)
    return offset_side
