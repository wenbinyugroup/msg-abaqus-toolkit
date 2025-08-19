# -*- coding: utf-8 -*-

# ******************************************************************************
# Custom VABS GUI Application 
# This script creates and launches the Beam GUI application 
# ******************************************************************************

import sys
from abaqusGui import AFXApp

from vabsCaeMainWindow import VABSCaeMainWindow

# Initialize application object 
# In AFXApp, appName and vendorName are displayed if productName is set to ''
# otherwise productName is displayed. 
app = AFXApp(appName = 'ABAQUS/CAE', 
             vendorName = 'SIMULIA', 
             productName = 'Abaqus-VABS GUI', 
             majorNumber = -1, 
             minorNumber = -1, 
             updateNumber = -1, 
             prerelease = False)

app.init(sys.argv)

# Construct main window
VABSCaeMainWindow(app)

# Create application
app.create()

# Run application
app.run()
