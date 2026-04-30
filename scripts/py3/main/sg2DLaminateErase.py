# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *
from utils.utilities import *


from sg.sg2d_laminate import remove_laminate

def eraseLayups(baseline, model_name):

    remove_laminate(baseline, model_name)

