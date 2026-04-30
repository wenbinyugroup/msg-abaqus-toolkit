# -*- coding: utf-8 -*-

from __future__ import print_function

"""Hexagonal 2D Structure Genome generation with interphase for Abaqus."""

try:
    from ._runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config
except ImportError:
    from _runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config

ensure_py3_on_path()

try:
    from ._helpers import (
        assign_material_orientation,
        assign_section_by_points,
        build_reflected_part_names,
        cleanup_temporary_parts,
        create_rectangular_shell_part,
        create_shell_section,
        flip_shell_normal,
        log_square_geometry,
        mesh_quarter_part,
        mirror_quarter_to_full,
        partition_hex_corner_circles,
        resolve_square_element_codes,
        set_sg2d_view_yz_if_possible,
        validate_generated_names,
    )
    from .helpers import DEFAULT_BLOCK_SIZE, calculate_hex_geometry
except ImportError:
    from _helpers import (
        assign_material_orientation,
        assign_section_by_points,
        build_reflected_part_names,
        cleanup_temporary_parts,
        create_rectangular_shell_part,
        create_shell_section,
        flip_shell_normal,
        log_square_geometry,
        mesh_quarter_part,
        mirror_quarter_to_full,
        partition_hex_corner_circles,
        resolve_square_element_codes,
        set_sg2d_view_yz_if_possible,
        validate_generated_names,
    )
    from helpers import DEFAULT_BLOCK_SIZE, calculate_hex_geometry

from abaqus import *


BLOCK_SIZE = DEFAULT_BLOCK_SIZE
PART_NAMES = build_reflected_part_names('hexP3')
SECTION_NAMES = {
    'fiber': 'Fiber_section',
    'interface': 'Interphase_section',
    'matrix': 'Matrix_section',
}
MESH_FACE_MASK = '[#1f ]'


def _interface_probe_points(quarter_width, quarter_height, fiber_radius,
                            interface_radius):
    """Return probe points for hex interphase set assignment."""
    mid_radius = (fiber_radius + interface_radius) / 2.0
    return {
        'fiber': [
            (0.0, 0.0, 0.0),
            (0.0, quarter_width, quarter_height),
        ],
        'matrix': [
            (0.0, quarter_width / 2.0, quarter_height / 2.0),
        ],
        'interface': [
            (0.0, mid_radius, 0.0),
            (0.0, quarter_width - mid_radius, quarter_height),
        ],
    }


def createHexInterfaceV5(model_name, fiber_flag, vf_f, interface_flag,
                         t_interface, fiber_matname, matrix_matname,
                         interface_matname, mesh_size, elem_type):
    """Create a hexagonal 2D Structure Genome part with interphase.

    Parameters
    ----------
    model_name : str
        Abaqus model name.
    fiber_flag : int
        Fiber input mode selector. ``1`` means area fraction, ``2`` means
        radius.
    vf_f : float
        Fiber area fraction or radius, depending on ``fiber_flag``.
    interface_flag : int
        Interphase input mode selector. ``1`` means area fraction, ``2`` means
        thickness.
    t_interface : float
        Interphase area fraction or thickness, depending on
        ``interface_flag``.
    fiber_matname : str
        Fiber material name.
    matrix_matname : str
        Matrix material name.
    interface_matname : str
        Interphase material name.
    mesh_size : float
        Target mesh seed size.
    elem_type : str
        Element family label.

    Returns
    -------
    Part
        Abaqus part containing the merged and meshed SG geometry.
    """
    model = mdb.models[model_name]
    validate_generated_names(model, PART_NAMES, SECTION_NAMES)

    geometry = calculate_hex_geometry(
        fiber_flag,
        vf_f,
        interface_flag=interface_flag,
        t_interface=t_interface,
        block_size=BLOCK_SIZE,
    )
    element_codes = resolve_square_element_codes(elem_type)
    fiber_radius = geometry['fiber_radius']
    fiber_area_fraction = geometry['fiber_area_fraction']
    interface_radius = geometry['interface_radius']
    interface_area_fraction = geometry['interface_area_fraction']
    quarter_width = geometry['quarter_width']
    quarter_height = geometry['quarter_height']

    print('#-------part_name  %s---------------------------' % PART_NAMES['full'])
    print('totalArea: %s' % geometry['total_area'])
    log_square_geometry(
        BLOCK_SIZE,
        fiber_radius,
        fiber_area_fraction,
        interface_radius=interface_radius,
        interface_area_fraction=interface_area_fraction,
    )

    part = create_rectangular_shell_part(
        model,
        PART_NAMES['quarter'],
        quarter_width,
        quarter_height,
    )
    partition_hex_corner_circles(
        part,
        model,
        quarter_width,
        quarter_height,
        [fiber_radius, interface_radius],
    )

    shell_thickness = 0.01 * BLOCK_SIZE
    create_shell_section(
        model,
        SECTION_NAMES['fiber'],
        fiber_matname,
        shell_thickness,
    )
    create_shell_section(
        model,
        SECTION_NAMES['matrix'],
        matrix_matname,
        shell_thickness,
    )
    create_shell_section(
        model,
        SECTION_NAMES['interface'],
        interface_matname,
        shell_thickness,
    )

    probe_points = _interface_probe_points(
        quarter_width,
        quarter_height,
        fiber_radius,
        interface_radius,
    )
    assign_section_by_points(
        part,
        SECTION_NAMES['fiber'],
        SECTION_NAMES['fiber'],
        probe_points['fiber'],
    )
    assign_section_by_points(
        part,
        SECTION_NAMES['interface'],
        SECTION_NAMES['interface'],
        probe_points['interface'],
    )
    assign_section_by_points(
        part,
        SECTION_NAMES['matrix'],
        SECTION_NAMES['matrix'],
        probe_points['matrix'],
    )
    assign_material_orientation(part, SECTION_NAMES['fiber'])
    assign_material_orientation(part, SECTION_NAMES['interface'])
    assign_material_orientation(part, SECTION_NAMES['matrix'])

    mesh_quarter_part(part, mesh_size, element_codes, MESH_FACE_MASK)
    part = mirror_quarter_to_full(model, PART_NAMES, mesh_size)
    flip_shell_normal(part)
    cleanup_temporary_parts(model, PART_NAMES)
    return part


DEFAULT_CONFIG = {
    'model_name': 'Model-1',
    'fiber_flag': 1,
    'vf_f': 0.2,
    'interface_flag': 2,
    't_interface': 0.02,
    'fiber_matname': 'Fiber',
    'matrix_matname': 'Matrix',
    'interface_matname': 'Interface',
    'mesh_size': 0.1,
    'elem_type': 'Linear',
}


def main(config=None):
    """Build a hexagonal 2D SG with interphase outside the GUI."""
    if config is None:
        config = load_cli_config(DEFAULT_CONFIG)

    ensure_materials_exist(
        mdb,
        config['model_name'],
        [
            config['fiber_matname'],
            config['matrix_matname'],
            config['interface_matname'],
        ],
    )
    part = createHexInterfaceV5(**config)
    set_sg2d_view_yz_if_possible(part)
    return part


if __name__ == '__main__':
    main()
