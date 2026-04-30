# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from sg.layup import fastGenerate, readMaterialFile, readLayupFile

def addLayups(method,
              fg_model_name = '', fg_material_name = '', fg_section_name = '', fg_layup = '', fg_ply_thickness = 0.0, 
              rf_model_name = '', rf_section_name = '', rf_material_file = '', rf_layup_file = ''):
    
    if method == 1:
        fastGenerate(fg_model_name, fg_material_name, fg_section_name, fg_layup, fg_ply_thickness)
    elif method == 2:
        mid_name = readMaterialFile(rf_model_name, rf_material_file)
        readLayupFile(rf_model_name, rf_layup_file, mid_name)
        
    return 1

