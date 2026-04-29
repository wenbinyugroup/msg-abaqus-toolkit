# -*- coding: utf-8 -*-

"""GUI-facing dispatch for 3D Structure Genome creation."""

from sg.sg3d_spherical import create3DsphericV5


def create3DV5SG(profile, fiber_flag, vf_f, interface_flag, t_interface,
                 modelName, fiber_matname, matrix_matname, interface_matname,
                 mesh_size, elem_type):
    """Create a 3D SG variant from the GUI command path.

    Parameters
    ----------
    profile : int
        SG profile selector. Only spherical inclusion is currently supported.
    fiber_flag : int
        Fiber input mode selector from the GUI.
    vf_f : float
        Inclusion volume fraction or radius, depending on ``fiber_flag``.
    interface_flag : int
        Interphase input mode selector from the GUI.
    t_interface : float
        Interphase thickness or volume fraction, depending on
        ``interface_flag``.
    modelName : str
        Abaqus model name.
    fiber_matname : str
        Inclusion material name.
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
    if profile != 1:
        raise ValueError('Unknown 3D SG profile: %s' % profile)

    create3DsphericV5(
        modelName, fiber_flag, vf_f, interface_flag, t_interface,
        fiber_matname, matrix_matname, interface_matname, mesh_size,
        elem_type
    )
    return 1
