"""Runtime helpers for standalone Abaqus SG scripts."""

from __future__ import print_function

import os
import sys


def ensure_py3_on_path():
    """Ensure ``scripts/py3`` is importable for standalone script runs."""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    py3_dir = os.path.dirname(this_dir)
    if py3_dir not in sys.path:
        sys.path.insert(0, py3_dir)
    return py3_dir


def _cast_override(raw_value, current_value):
    """Cast a CLI override using the default value's type.

    Parameters
    ----------
    raw_value : str
        Raw ``key=value`` string value from ``sys.argv``.
    current_value : object
        Existing config value used for type inference.

    Returns
    -------
    object
        Parsed value with a compatible type.
    """
    if isinstance(current_value, bool):
        return raw_value.lower() in ('1', 'true', 'yes', 'on')
    if isinstance(current_value, int) and not isinstance(current_value, bool):
        return int(raw_value)
    if isinstance(current_value, float):
        return float(raw_value)
    return raw_value


def load_cli_config(default_config):
    """Merge ``key=value`` CLI overrides into a copy of ``default_config``.

    Parameters
    ----------
    default_config : dict
        Default config used both as a template and type schema.

    Returns
    -------
    dict
        Config dictionary with CLI overrides applied.

    Raises
    ------
    KeyError
        If an unknown key is provided.
    ValueError
        If an argument is not in ``key=value`` form.
    """
    config = dict(default_config)
    args = list(sys.argv[1:])
    if '--' in args:
        args = args[args.index('--') + 1:]

    for arg in args:
        if '=' not in arg:
            raise ValueError(
                'Expected CLI overrides in key=value form, got: %s' % arg
            )
        key, raw_value = arg.split('=', 1)
        if key not in config:
            raise KeyError('Unknown config key: %s' % key)
        config[key] = _cast_override(raw_value, config[key])

    return config


def ensure_materials_exist(mdb, model_name, material_names):
    """Validate that required materials exist in the target model.

    Parameters
    ----------
    mdb : object
        Abaqus model database handle.
    model_name : str
        Target model name.
    material_names : list[str]
        Required material names.

    Raises
    ------
    ValueError
        If the model or any required material is missing.
    """
    if model_name not in mdb.models:
        raise ValueError(
            'Model "%s" does not exist. Create it first or change model_name.'
            % model_name
        )

    model = mdb.models[model_name]
    missing = [
        material_name for material_name in material_names
        if material_name and material_name not in model.materials
    ]
    if missing:
        raise ValueError(
            'Model "%s" is missing materials: %s'
            % (model_name, ', '.join(missing))
        )
