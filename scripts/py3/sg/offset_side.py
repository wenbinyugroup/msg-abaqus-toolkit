# -*- coding: utf-8 -*-
"""Pure-geometric offset-side decision helpers.

These functions take plain coordinate arrays and return ``'LEFT'`` or
``'RIGHT'`` — no Abaqus objects required.  They can therefore be unit-tested
with only NumPy.

Two geometric criteria are provided:

* **Dot-product test** (``decide_side_dotproduct``): used when the offset
  result vertex is compared against the baseline direction.  Returns
  ``'RIGHT'`` when the offset vertex lies on the opposite side of the
  baseline start from the baseline end.
* **Cross-product test** (``decide_side_crossproduct``): used when two
  reference directions define the expected half-plane.  Returns ``'RIGHT'``
  when the signed 2-D cross product (the first component of the 3-D cross
  product with x = 0) is positive.
"""

import numpy as np


def decide_side_dotproduct(baseline_start, baseline_end, offset_point):
    """Decide offset side by dot product of baseline and offset vectors.

    Parameters
    ----------
    baseline_start : array-like, shape (3,)
        Start point of the baseline (typically ``pt0``).
    baseline_end : array-like, shape (3,)
        End point of the baseline (typically ``pt1``).
    offset_point : array-like, shape (3,)
        The vertex of the offset geometry to test.

    Returns
    -------
    str
        ``'LEFT'`` if the offset point lies on the same side as the baseline
        direction; ``'RIGHT'`` if on the opposite side (dot product < 0).

    Notes
    -----
    The vectors live in the yz-plane (x-component is always 0.0 for sketch
    geometry).  Only the 3-D dot product sign matters.
    """
    vec_baseline = np.array(baseline_end) - np.array(baseline_start)
    vec_offset = np.array(offset_point) - np.array(baseline_start)
    return 'RIGHT' if np.dot(vec_baseline, vec_offset) < 0.0 else 'LEFT'


def decide_side_crossproduct(point0, point1, point2):
    """Decide offset side by the z-component of a 3-D cross product.

    Parameters
    ----------
    point0 : array-like, shape (3,)
        The point whose side is being tested (e.g. the offset vertex).
    point1 : array-like, shape (3,)
        Reference origin (baseline start).
    point2 : array-like, shape (3,)
        Direction indicator (boundary vertex adjacent to baseline end).

    Returns
    -------
    str
        ``'RIGHT'`` if the first component of ``cross(p0-p1, p2-p1)`` is
        positive; ``'LEFT'`` otherwise.

    Notes
    -----
    Because the input coordinates are of the form ``(0.0, y, z)``, the
    cross product reduces to ``(y0*z2 - z0*y2, 0, 0)``.  The sign of the
    first component is the signed area of the 2-D parallelogram in the
    yz-plane.
    """
    vec1 = np.array(point0) - np.array(point1)
    vec2 = np.array(point2) - np.array(point1)
    c = np.cross(vec1, vec2)
    return 'RIGHT' if c[0] > 0 else 'LEFT'
