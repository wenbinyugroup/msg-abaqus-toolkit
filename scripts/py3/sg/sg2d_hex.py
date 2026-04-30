# -*- coding: utf-8 -*-

from __future__ import print_function

"""Hexagonal 2D Structure Genome generation for Abaqus."""

try:
    from ._runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config
except ImportError:
    from _runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config

ensure_py3_on_path()

try:
    from ._helpers import (
        assign_section,
        build_reflected_part_names,
        cleanup_temporary_parts,
        create_rectangular_shell_part,
        create_shell_section,
        flip_shell_normal,
        log_square_geometry,
        mesh_quarter_part,
        mirror_quarter_to_full,
        partition_hex_corner_arcs,
        resolve_square_element_codes,
        set_sg2d_view_yz_if_possible,
        validate_generated_names,
    )
    from .helpers import DEFAULT_BLOCK_SIZE, calculate_hex_geometry
except ImportError:
    from _helpers import (
        assign_section,
        build_reflected_part_names,
        cleanup_temporary_parts,
        create_rectangular_shell_part,
        create_shell_section,
        flip_shell_normal,
        log_square_geometry,
        mesh_quarter_part,
        mirror_quarter_to_full,
        partition_hex_corner_arcs,
        resolve_square_element_codes,
        set_sg2d_view_yz_if_possible,
        validate_generated_names,
    )
    from helpers import DEFAULT_BLOCK_SIZE, calculate_hex_geometry

from abaqus import *


BLOCK_SIZE = DEFAULT_BLOCK_SIZE
PART_NAMES = build_reflected_part_names('hexP2')
SECTION_NAMES = {
    'fiber': 'Fiber_section',
    'matrix': 'Matrix_section',
}
MESH_FACE_MASK = '[#7 ]'
SECTION_MASKS = {
    'fiber': '[#3 ]',
    'matrix': '[#4 ]',
}


def createHexV5(model_name, fiber_flag, vf_f, fiber_matname, matrix_matname,
                mesh_size, elem_type):
    """Create a hexagonal 2D Structure Genome part.

    Parameters
    ----------
    model_name : str
        Abaqus model name.
    fiber_flag : int
        Fiber input mode selector. ``1`` means area fraction, ``2`` means
        radius.
    vf_f : float
        Fiber area fraction or radius, depending on ``fiber_flag``.
    fiber_matname : str
        Fiber material name.
    matrix_matname : str
        Matrix material name.
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

    geometry = calculate_hex_geometry(fiber_flag, vf_f, block_size=BLOCK_SIZE)
    element_codes = resolve_square_element_codes(elem_type)
    fiber_radius = geometry['fiber_radius']
    fiber_area_fraction = geometry['fiber_area_fraction']

    print('#-------part_name  %s---------------------------' % PART_NAMES['full'])
    print('totalArea: %s' % geometry['total_area'])
    log_square_geometry(BLOCK_SIZE, fiber_radius, fiber_area_fraction)

    part = create_rectangular_shell_part(
        model,
        PART_NAMES['quarter'],
        geometry['quarter_width'],
        geometry['quarter_height'],
    )
    partition_hex_corner_arcs(
        part,
        model,
        geometry['quarter_width'],
        geometry['quarter_height'],
        fiber_radius,
    )

    shell_thickness = 0.01 * BLOCK_SIZE
    create_shell_section(
        model,
        SECTION_NAMES['matrix'],
        matrix_matname,
        shell_thickness,
    )
    create_shell_section(
        model,
        SECTION_NAMES['fiber'],
        fiber_matname,
        shell_thickness,
    )
    assign_section(
        part,
        SECTION_NAMES['fiber'],
        SECTION_NAMES['fiber'],
        SECTION_MASKS['fiber'],
    )
    assign_section(
        part,
        SECTION_NAMES['matrix'],
        SECTION_NAMES['matrix'],
        SECTION_MASKS['matrix'],
    )

    mesh_quarter_part(part, mesh_size, element_codes, MESH_FACE_MASK)
    part = mirror_quarter_to_full(model, PART_NAMES, mesh_size)
    flip_shell_normal(part)
    cleanup_temporary_parts(model, PART_NAMES)
    return part


DEFAULT_CONFIG = {
    'model_name': 'Model-1',
    'fiber_flag': 1,
    'vf_f': 0.25,
    'fiber_matname': 'Fiber',
    'matrix_matname': 'Matrix',
    'mesh_size': 0.1,
    'elem_type': 'Linear',
}


def main(config=None):
    """Build a hexagonal 2D SG outside the GUI."""
    if config is None:
        config = load_cli_config(DEFAULT_CONFIG)

    ensure_materials_exist(
        mdb,
        config['model_name'],
        [config['fiber_matname'], config['matrix_matname']],
    )
    part = createHexV5(**config)
    set_sg2d_view_yz_if_possible(part)
    return part


if __name__ == '__main__':
    main()
