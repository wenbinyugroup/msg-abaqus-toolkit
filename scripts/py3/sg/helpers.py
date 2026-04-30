"""Pure Python helpers for SG geometry calculations."""

from __future__ import print_function

from math import pi


DEFAULT_BLOCK_SIZE = 1.0


def sphere_volume_fraction(radius, block_size):
    """Return the sphere volume fraction inside a cubic SG.

    Parameters
    ----------
    radius : float
        Sphere radius.
    block_size : float
        Side length of the cubic SG.

    Returns
    -------
    float
        Sphere volume fraction within the cube.
    """
    return 4.0 * pi * radius ** 3 / (3.0 * block_size ** 3)


def calculate_spherical_fiber_geometry(fiber_flag, vf_f, block_size):
    """Compute spherical inclusion geometry from GUI inputs.

    Parameters
    ----------
    fiber_flag : int
        ``1`` means ``vf_f`` is a volume fraction, ``2`` means radius.
    vf_f : float
        Inclusion volume fraction or radius.
    block_size : float
        Side length of the cubic SG.

    Returns
    -------
    tuple
        Fiber radius and volume fraction.

    Raises
    ------
    ValueError
        Raised when the input mode or numeric range is invalid.
    """
    if fiber_flag == 1:
        if vf_f <= 0.0:
            raise ValueError('Fiber volume fraction must be positive.')
        fiber_radius = block_size * pow(3.0 * vf_f / (4.0 * pi), 1.0 / 3.0)
        vof_fiber = vf_f
    elif fiber_flag == 2:
        if vf_f <= 0.0:
            raise ValueError('Fiber radius must be positive.')
        fiber_radius = vf_f
        vof_fiber = sphere_volume_fraction(fiber_radius, block_size)
    else:
        raise ValueError('Unsupported fiber_flag "%s". Expected 1 or 2.' % fiber_flag)

    if fiber_radius >= block_size / 2.0:
        raise ValueError(
            'Fiber radius %.6f exceeds the half block size %.6f.'
            % (fiber_radius, block_size / 2.0)
        )

    return fiber_radius, vof_fiber


def calculate_spherical_interface_geometry(interface_flag, t_interface,
                                           fiber_radius, vof_fiber,
                                           block_size):
    """Compute spherical interphase geometry from GUI inputs.

    Parameters
    ----------
    interface_flag : int
        ``1`` means ``t_interface`` is a volume fraction, ``2`` means thickness.
    t_interface : float
        Interphase volume fraction or thickness.
    fiber_radius : float
        Inclusion radius.
    vof_fiber : float
        Inclusion volume fraction.
    block_size : float
        Side length of the cubic SG.

    Returns
    -------
    tuple
        Interface radius and interface volume fraction, or ``(None, 0.0)`` when
        no interface is requested.

    Raises
    ------
    ValueError
        Raised when the input mode or numeric range is invalid.
    """
    if t_interface < 0.0:
        raise ValueError('Interphase thickness should be equal or larger than zero.')
    if t_interface == 0.0:
        return None, 0.0

    if interface_flag == 1:
        if t_interface <= 0.0:
            raise ValueError('Interphase volume fraction must be positive.')
        vof_interface = t_interface
        interface_radius = block_size * pow(
            3.0 * (vof_fiber + vof_interface) / (4.0 * pi), 1.0 / 3.0
        )
    elif interface_flag == 2:
        interface_radius = fiber_radius + t_interface
        vof_interface = (
            sphere_volume_fraction(interface_radius, block_size)
            - sphere_volume_fraction(fiber_radius, block_size)
        )
    else:
        raise ValueError(
            'Unsupported interface_flag "%s". Expected 1 or 2.'
            % interface_flag
        )

    if interface_radius <= fiber_radius:
        raise ValueError('Interphase radius must be larger than the fiber radius.')
    if interface_radius >= block_size / 2.0:
        raise ValueError(
            'The volume fraction of inclusion and interphase is out of range. '
            'Please adjust the values.'
        )

    return interface_radius, vof_interface


def calculate_spherical_geometry(fiber_flag, vf_f, interface_flag,
                                 t_interface, block_size=DEFAULT_BLOCK_SIZE):
    """Compute the derived spherical SG geometry.

    Parameters
    ----------
    fiber_flag : int
        Inclusion input mode selector.
    vf_f : float
        Inclusion volume fraction or radius, depending on ``fiber_flag``.
    interface_flag : int
        Interphase input mode selector.
    t_interface : float
        Interphase volume fraction or thickness, depending on
        ``interface_flag``.
    block_size : float, optional
        Side length of the cubic SG.

    Returns
    -------
    dict
        Derived geometry values used by Abaqus-side builders.
    """
    fiber_radius, fiber_volume_fraction = calculate_spherical_fiber_geometry(
        fiber_flag,
        vf_f,
        block_size,
    )
    interface_radius, interface_volume_fraction = (
        calculate_spherical_interface_geometry(
            interface_flag,
            t_interface,
            fiber_radius,
            fiber_volume_fraction,
            block_size,
        )
    )
    return {
        'fiber_radius': fiber_radius,
        'fiber_volume_fraction': fiber_volume_fraction,
        'interface_radius': interface_radius,
        'interface_volume_fraction': interface_volume_fraction,
    }


def circle_area_fraction(radius, block_size):
    """Return the circle area fraction inside a square SG.

    Parameters
    ----------
    radius : float
        Circle radius.
    block_size : float
        Side length of the square SG.

    Returns
    -------
    float
        Circle area fraction within the square.
    """
    return pi * radius ** 2 / block_size ** 2


def calculate_square_fiber_geometry(fiber_flag, vf_f,
                                    block_size=DEFAULT_BLOCK_SIZE):
    """Compute square-cell fiber geometry from GUI inputs.

    Parameters
    ----------
    fiber_flag : int
        ``1`` means ``vf_f`` is an area fraction, ``2`` means radius.
    vf_f : float
        Fiber area fraction or radius.
    block_size : float, optional
        Side length of the square SG.

    Returns
    -------
    dict
        Derived fiber geometry values used by Abaqus-side builders.

    Raises
    ------
    ValueError
        Raised when the input mode or numeric range is invalid.
    """
    if fiber_flag == 1:
        if vf_f <= 0.0:
            raise ValueError('Fiber volume fraction must be positive.')
        fiber_radius = block_size * pow(vf_f / pi, 0.5)
        fiber_area_fraction = vf_f
    elif fiber_flag == 2:
        if vf_f <= 0.0:
            raise ValueError('Fiber radius must be positive.')
        fiber_radius = vf_f
        fiber_area_fraction = circle_area_fraction(fiber_radius, block_size)
    else:
        raise ValueError('Unsupported fiber_flag "%s". Expected 1 or 2.' % fiber_flag)

    if fiber_radius >= block_size / 2.0:
        raise ValueError(
            'The volume fraction of fiber is out of range. Please adjust the values.'
        )

    return {
        'fiber_radius': fiber_radius,
        'fiber_area_fraction': fiber_area_fraction,
        'quarter_size': block_size / 2.0,
    }


def calculate_square_interface_geometry(interface_flag, t_interface,
                                        fiber_radius, fiber_area_fraction,
                                        block_size=DEFAULT_BLOCK_SIZE):
    """Compute square-cell interphase geometry from GUI inputs.

    Parameters
    ----------
    interface_flag : int
        ``1`` means ``t_interface`` is an area fraction, ``2`` means thickness.
    t_interface : float
        Interphase area fraction or thickness.
    fiber_radius : float
        Fiber radius.
    fiber_area_fraction : float
        Fiber area fraction.
    block_size : float, optional
        Side length of the square SG.

    Returns
    -------
    dict
        Derived interface geometry values used by Abaqus-side builders.

    Raises
    ------
    ValueError
        Raised when the input mode or numeric range is invalid.
    """
    if t_interface < 0.0:
        raise ValueError('Interphase thickness should be equal or larger than zero.')
    if t_interface == 0.0:
        return {
            'interface_radius': None,
            'interface_area_fraction': 0.0,
        }

    if interface_flag == 1:
        if t_interface <= 0.0:
            raise ValueError('Interphase volume fraction must be positive.')
        interface_area_fraction = t_interface
        interface_radius = block_size * pow(
            (fiber_area_fraction + interface_area_fraction) / pi,
            0.5,
        )
    elif interface_flag == 2:
        interface_radius = fiber_radius + t_interface
        interface_area_fraction = (
            circle_area_fraction(interface_radius, block_size)
            - circle_area_fraction(fiber_radius, block_size)
        )
    else:
        raise ValueError(
            'Unsupported interface_flag "%s". Expected 1 or 2.'
            % interface_flag
        )

    if interface_radius <= fiber_radius:
        raise ValueError('Interphase radius must be larger than the fiber radius.')
    if interface_radius >= block_size / 2.0:
        raise ValueError(
            'The volume fraction of fiber and interphase is out of range. '
            'Please adjust the values.'
        )

    return {
        'interface_radius': interface_radius,
        'interface_area_fraction': interface_area_fraction,
    }


def calculate_square_geometry(fiber_flag, vf_f, interface_flag=None,
                              t_interface=0.0,
                              block_size=DEFAULT_BLOCK_SIZE):
    """Compute the derived square SG geometry.

    Parameters
    ----------
    fiber_flag : int
        Fiber input mode selector.
    vf_f : float
        Fiber area fraction or radius, depending on ``fiber_flag``.
    interface_flag : int, optional
        Interphase input mode selector.
    t_interface : float, optional
        Interphase area fraction or thickness, depending on
        ``interface_flag``.
    block_size : float, optional
        Side length of the square SG.

    Returns
    -------
    dict
        Derived geometry values used by Abaqus-side builders.
    """
    geometry = calculate_square_fiber_geometry(
        fiber_flag,
        vf_f,
        block_size=block_size,
    )

    if interface_flag is None:
        geometry['interface_radius'] = None
        geometry['interface_area_fraction'] = 0.0
        return geometry

    geometry.update(
        calculate_square_interface_geometry(
            interface_flag,
            t_interface,
            geometry['fiber_radius'],
            geometry['fiber_area_fraction'],
            block_size=block_size,
        )
    )
    return geometry


def hex_total_area(block_size):
    """Return the area of the hexagonal 2D SG cell.

    Parameters
    ----------
    block_size : float
        Side-to-side width basis used by the hexagonal SG builder.

    Returns
    -------
    float
        Total cell area.
    """
    return block_size ** 2 * pow(3.0, 0.5) / 2.0


def circle_area_fraction_in_hex(radius, block_size):
    """Return the circle area fraction inside a hexagonal SG cell.

    Parameters
    ----------
    radius : float
        Circle radius.
    block_size : float
        Side-to-side width basis used by the hexagonal SG builder.

    Returns
    -------
    float
        Circle area fraction within the hexagonal cell.
    """
    return 2.0 * pi * radius ** 2 / hex_total_area(block_size)


def calculate_hex_fiber_geometry(fiber_flag, vf_f,
                                 block_size=DEFAULT_BLOCK_SIZE):
    """Compute hex-cell fiber geometry from GUI inputs.

    Parameters
    ----------
    fiber_flag : int
        ``1`` means ``vf_f`` is an area fraction, ``2`` means radius.
    vf_f : float
        Fiber area fraction or radius.
    block_size : float, optional
        Side-to-side width basis used by the hexagonal SG builder.

    Returns
    -------
    dict
        Derived fiber geometry values used by Abaqus-side builders.

    Raises
    ------
    ValueError
        Raised when the input mode or numeric range is invalid.
    """
    if fiber_flag == 1:
        if vf_f <= 0.0:
            raise ValueError('Fiber volume fraction must be positive.')
        fiber_radius = block_size * pow(pow(3.0, 0.5) * vf_f / (2.0 * pi), 0.5)
        fiber_area_fraction = vf_f
    elif fiber_flag == 2:
        if vf_f <= 0.0:
            raise ValueError('Fiber radius must be positive.')
        fiber_radius = vf_f
        fiber_area_fraction = circle_area_fraction_in_hex(fiber_radius, block_size)
    else:
        raise ValueError('Unsupported fiber_flag "%s". Expected 1 or 2.' % fiber_flag)

    if fiber_radius >= block_size / 2.0:
        raise ValueError(
            'The volume fraction of fiber is out of range. Please adjust the values.'
        )

    return {
        'fiber_radius': fiber_radius,
        'fiber_area_fraction': fiber_area_fraction,
        'quarter_width': block_size / 2.0,
        'quarter_height': block_size * pow(3.0, 0.5) / 2.0,
        'total_area': hex_total_area(block_size),
    }


def calculate_hex_interface_geometry(interface_flag, t_interface,
                                     fiber_radius, fiber_area_fraction,
                                     block_size=DEFAULT_BLOCK_SIZE):
    """Compute hex-cell interphase geometry from GUI inputs.

    Parameters
    ----------
    interface_flag : int
        ``1`` means ``t_interface`` is an area fraction, ``2`` means thickness.
    t_interface : float
        Interphase area fraction or thickness.
    fiber_radius : float
        Fiber radius.
    fiber_area_fraction : float
        Fiber area fraction.
    block_size : float, optional
        Side-to-side width basis used by the hexagonal SG builder.

    Returns
    -------
    dict
        Derived interface geometry values used by Abaqus-side builders.

    Raises
    ------
    ValueError
        Raised when the input mode or numeric range is invalid.
    """
    if t_interface < 0.0:
        raise ValueError('Interphase thickness should be equal or larger than zero.')
    if t_interface == 0.0:
        return {
            'interface_radius': None,
            'interface_area_fraction': 0.0,
        }

    if interface_flag == 1:
        if t_interface <= 0.0:
            raise ValueError('Interphase volume fraction must be positive.')
        interface_area_fraction = t_interface
        interface_radius = block_size * pow(
            pow(3.0, 0.5) * (fiber_area_fraction + interface_area_fraction)
            / (2.0 * pi),
            0.5,
        )
    elif interface_flag == 2:
        interface_radius = fiber_radius + t_interface
        interface_area_fraction = (
            circle_area_fraction_in_hex(interface_radius, block_size)
            - circle_area_fraction_in_hex(fiber_radius, block_size)
        )
    else:
        raise ValueError(
            'Unsupported interface_flag "%s". Expected 1 or 2.'
            % interface_flag
        )

    if interface_radius <= fiber_radius:
        raise ValueError('Interphase radius must be larger than the fiber radius.')
    if interface_radius >= block_size / 2.0:
        raise ValueError(
            'The volume fraction of fiber and interphase is out of range. '
            'Please adjust the values.'
        )

    return {
        'interface_radius': interface_radius,
        'interface_area_fraction': interface_area_fraction,
    }


def calculate_hex_geometry(fiber_flag, vf_f, interface_flag=None,
                           t_interface=0.0,
                           block_size=DEFAULT_BLOCK_SIZE):
    """Compute the derived hexagonal SG geometry.

    Parameters
    ----------
    fiber_flag : int
        Fiber input mode selector.
    vf_f : float
        Fiber area fraction or radius, depending on ``fiber_flag``.
    interface_flag : int, optional
        Interphase input mode selector.
    t_interface : float, optional
        Interphase area fraction or thickness, depending on
        ``interface_flag``.
    block_size : float, optional
        Side-to-side width basis used by the hexagonal SG builder.

    Returns
    -------
    dict
        Derived geometry values used by Abaqus-side builders.
    """
    geometry = calculate_hex_fiber_geometry(
        fiber_flag,
        vf_f,
        block_size=block_size,
    )

    if interface_flag is None:
        geometry['interface_radius'] = None
        geometry['interface_area_fraction'] = 0.0
        return geometry

    geometry.update(
        calculate_hex_interface_geometry(
            interface_flag,
            t_interface,
            geometry['fiber_radius'],
            geometry['fiber_area_fraction'],
            block_size=block_size,
        )
    )
    return geometry
