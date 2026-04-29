# -*- coding: utf-8 -*-

"""GUI-facing dispatch for 2D Structure Genome creation."""

from __future__ import print_function

from main import utilities_abq as uab
from sg.sg2d_hex import createHexV5
from sg.sg2d_hex_interface import createHexInterfaceV5
from sg.sg2d_square import createSqrV5
from sg.sg2d_square_interface import createSqrInterfaceV5


def create2DV5SG(profile, fiber_flag, vf_f, interface_flag, t_interface,
                 model_name, fiber_matname, matrix_matname, interface_matname,
                 mesh_size, elem_type):
    """Create a 2D SG variant from the GUI command path.

    Parameters
    ----------
    profile : int
        SG profile selector. ``1`` is square and ``2`` is hexagonal.
    fiber_flag : int
        Fiber input mode selector from the GUI.
    vf_f : float
        Fiber volume fraction or radius, depending on ``fiber_flag``.
    interface_flag : int
        Interphase input mode selector from the GUI.
    t_interface : float
        Interphase thickness or volume fraction, depending on
        ``interface_flag``.
    model_name : str
        Abaqus model name.
    fiber_matname : str
        Fiber material name.
    matrix_matname : str
        Matrix material name.
    interface_matname : str
        Interphase material name.
    mesh_size : float
        Target mesh size.
    elem_type : str
        Element family label from the GUI.

    Returns
    -------
    int
        ``1`` for Abaqus GUI command compatibility.
    """
    if profile == 1:
        if t_interface == 0.0:
            part = createSqrV5(
                model_name, fiber_flag, vf_f, fiber_matname,
                matrix_matname, mesh_size, elem_type
            )
        else:
            part = createSqrInterfaceV5(
                model_name, fiber_flag, vf_f, interface_flag,
                t_interface, fiber_matname, matrix_matname,
                interface_matname, mesh_size, elem_type
            )
    elif profile == 2:
        if t_interface == 0.0:
            part = createHexV5(
                model_name, fiber_flag, vf_f, fiber_matname,
                matrix_matname, mesh_size, elem_type
            )
        else:
            part = createHexInterfaceV5(
                model_name, fiber_flag, vf_f, interface_flag,
                t_interface, fiber_matname, matrix_matname,
                interface_matname, mesh_size, elem_type
            )
    else:
        raise ValueError('Unknown 2D SG profile: %s' % profile)

    try:
        uab.setViewYZ(nsg=2, obj=part, clr='Material')
    except Exception:
        pass

    return 1

