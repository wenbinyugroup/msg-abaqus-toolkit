# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from textRepr import *
from caeModules import *
from math import *

from utils.utilities import *
from utils import abq_view as abv
from sg.layup import get_active_composite_layup_thicknesses, update_1d_part_geometry


# ==============================================================================
#
#   Composite Layups
#
# ==============================================================================

def abaLayupGenerate(model_name_abq, part_name,layup_abq, element_type):
    cv = abv.current_viewport()
    model_name = model_name_abq

    model = mdb.models[model_name]
    part  = model.parts[part_name]
    abv.set_displayed_object(part, vp=cv)
    layup_name_inuse = layup_abq
    layup_t = get_active_composite_layup_thicknesses(part.compositeLayups[layup_name_inuse])
    update_1d_part_geometry(model_name, part_name, layup_t, element_type)

    return 1

