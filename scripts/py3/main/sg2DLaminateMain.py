# -*- coding: utf-8 -*-

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from symbolicConstants import *
from utils.utilities import *

from sg.sg2d_laminate import add_laminate

def assignLayups(baseline, area, model_name, section_name, opposite=0, nsp=20):

    add_laminate(baseline, area, model_name, section_name, opposite, nsp)

