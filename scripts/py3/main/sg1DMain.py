# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *

from textRepr import *
from caeModules import *
from math import *

from utils.utilities import *


from sg.sg1d_fast_generate import fastGenerate1D
from sg.sg1d_composite_layup import abaLayupGenerate
from sg.sg1d_composite_section import abaSection1D
from sg.sg1d_read_file import fromInputfile1D

def create1DSG(method,
               layup_fg='', thickness_fg='1.0', model_name_fg='', material_name='', offset_ratio_fg=0.0,
               model_name_abq='', part_name='', layup_abq='',
               rf_model_name = '', rf_part_name='', rf_section_name='', rf_offset_ratio=0.0,
               file_layup_input='', model_name_file='',
               element_type='five-noded'):

    if method == 1:
        fastGenerate1D(layup_fg, thickness_fg, model_name_fg, material_name, 
                       offset_ratio_fg, element_type)

    elif method == 2:
        #print 'other methods need to be added'
        abaLayupGenerate(model_name_abq, part_name, layup_abq, element_type)

    elif method == 3:
#        print 'abaSection1D method'
        abaSection1D(rf_model_name, rf_part_name, rf_section_name, rf_offset_ratio, element_type)

    elif method == 4:
        fromInputfile1D(file_layup_input, model_name_file,  element_type)    

    return 1

