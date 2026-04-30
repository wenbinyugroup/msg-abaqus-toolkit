# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from textRepr import *
from caeModules import *
from math import *

from utils.utilities import *
from sg.layup import create_1d_part_with_composite_layup, get_section_layup_data


# ==============================================================================
#
#   Composite Sections
#
# ==============================================================================

def abaSection1D(model_name = '', part_name = '', section_name = '', offset_ratio = 0.0, element_type = 'five-noded'):
    model = mdb.models[model_name]
    layup_sec = model.sections[section_name].layup
    layup_mat, layup_t, layup_ori = get_section_layup_data(layup_sec)

    create_1d_part_with_composite_layup(
        model_name,
        part_name,
        layup_mat,
        layup_t,
        layup_ori,
        offset_ratio,
        element_type,
    )

    return 1
