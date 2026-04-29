# -*- coding: utf-8 -*-

from main.sg2DAirfoil import createAirfoil
import sys

project_name = sys.argv[-2]
control_file = sys.argv[-1]
createAirfoil(project_name, control_file)

