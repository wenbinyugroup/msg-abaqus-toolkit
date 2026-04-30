# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from textRepr import *
from caeModules import *
from math import *

from utils.utilities import *
from sg.layup import create_1d_part_with_composite_layup, expand_layup_angles


# ==============================================================================
#
#   Fast Generate
#
# ==============================================================================

def fastGenerate1D(layup, thickness, model_name, material_name, offset_ratio, element_type):
    part_name = 'Laminate'
    layup_ori = expand_layup_angles(layup)
    ply_count = len(layup_ori)
    layup_thicknesses = [float(thickness)] * ply_count
    layup_materials = [material_name] * ply_count

    create_1d_part_with_composite_layup(
        model_name,
        part_name,
        layup_materials,
        layup_thicknesses,
        layup_ori,
        offset_ratio,
        element_type,
    )
    
    return 1
    
