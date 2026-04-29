# -*- coding: utf-8 -*-

from __future__ import print_function

try:
    from ._runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config
except ImportError:
    from _runtime import ensure_py3_on_path, ensure_materials_exist, load_cli_config

ensure_py3_on_path()

from abaqus import *
from abaqusConstants import *
from caeModules import *
from textRepr import *
import regionToolset

from utils import abq_view


def _set_displayed_object_if_possible(displayed_object):
    """Update the active viewport when running with a GUI."""
    abq_view.set_displayed_object(displayed_object)


def _set_view_yz_if_possible(part):
    """Set the standard SG YZ view when a viewport exists."""
    abq_view.set_sg_view(nsg=2, obj=part, clr='Material')

def createSqrV5(model_name , fiber_flag,vf_f, fiber_matname,matrix_matname,mesh_size,elem_type):
    
    #---------------------------------------
    #### Define Parameters
    #--------------------------------------
    
    part2DName = 'sqrP2' + 'quater'
    part2DFullName = 'sqrP2'
    partsobj = mdb.models[model_name].parts
    print('#-------part_name  %s---------------------------'  % part2DFullName)

    #-------------------------------
    blockSize = 1.0
    quarterSize = 1.0 / 2.0 * blockSize
    
    if elem_type == 'Linear':
        elementType1 = S4
        elementType2 = S3
    elif elem_type == 'Quadratic':
        elementType1 = S8R
        elementType2 = STRI65
    else:
        raise ValueError('Unknown elem_type: %s' % elem_type)
    
    if fiber_flag == 1 : #vf_f is volume fraction  of the fiber
        vof_fiber = vf_f
        fiberRadius = blockSize * sqrt(vof_fiber/pi)

    elif fiber_flag == 2 :  #vf_f is radius of the fiber
        fiberRadius = vf_f
        vof_fiber = pi * fiberRadius**2 / blockSize**2
    
    if fiberRadius >= blockSize/2.0 :
        raise ValueError('The volume fraction of fiber is out of range. Please adjust the values.' )
    
    print('blockSize: %s' %blockSize)
    print('#---fiber------------------------')
    print('vof_fiber: %s' %vof_fiber)
    print('fiberRadius: %s' %fiberRadius)
    
    fiber_setname = 'Fiber_section'
    matrix_setname = 'Matrix_section'
    
    p = mdb.models[model_name].Part(name=part2DName, dimensionality=THREE_D, 
        type=DEFORMABLE_BODY)
    
    datumPlaneYZ_id = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0).id
    datumAxisZ_id = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS).id
    #---------------------------------------------------
    YZworkPlaneTransform = (0,1,0,   0,0,1,  1,0,0,   0,0,0) #y-z plane
#    YZviewVector = (1.0, 0.0, 0.0)
#    YZcameraUpVector = (0.0, 0.0, 1.0)
    #--------------------------------------------------
    s = mdb.models[model_name].ConstrainedSketch(name='__profile__', 
        sheetSize=200.0,transform=YZworkPlaneTransform)
        
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
#    session.viewports['Viewport: 1'].view.setValues(session.views['Left'])
    
    p = mdb.models[model_name].parts[part2DName]
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.rectangle(point1=(0.0, 0.0), point2=(quarterSize , quarterSize ))
    p = mdb.models[model_name].parts[part2DName]
    e1, d2 = p.edges, p.datums
    p.Shell(sketchPlane=d2[datumPlaneYZ_id], sketchUpEdge=d2[datumAxisZ_id], sketchPlaneSide=SIDE1, 
        sketchOrientation=RIGHT, sketch=s)
    s.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']
    
    p = mdb.models[model_name].parts[part2DName]
    
#    session.viewports['Viewport: 1'].view.setViewpoint(viewVector = (1.0, 0.0, 0.0), cameraUpVector = (0.0, 0.0, 1.0))
#    session.viewports['Viewport: 1'].view.fitView()
    #-------------------------------------------------------------
    #    Define fiber on the shell
    #--------------------------------------
    p = mdb.models[model_name].parts[part2DName]
    f, e, d = p.faces, p.edges, p.datums
    t = p.MakeSketchTransform(sketchPlane=f[0], sketchUpEdge=e[1], 
        sketchPlaneSide=SIDE1, origin=(0.0, 0.0, 0.0))
    s = mdb.models[model_name].ConstrainedSketch(name='__profile__', 
        sheetSize=2.0, gridSpacing=0.02, transform=t)
    g, v, d1, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=SUPERIMPOSE)
    p = mdb.models[model_name].parts[part2DName]
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(0.0,fiberRadius))
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    pickedFaces = f 
    e1, d2 = p.edges, p.datums
    p.PartitionFaceBySketch(sketchUpEdge=e1[1], faces=pickedFaces, sketch=s)
    s.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']
#    session.viewports['Viewport: 1'].view.setViewpoint(viewVector = (1.0, 0.0, 0.0), cameraUpVector = (0.0, 0.0, 1.0))
#    session.viewports['Viewport: 1'].view.fitView()
    
    #Define Sections and assign them
    #--------------------------------------
    mdb.models[model_name].HomogeneousShellSection(name=fiber_setname, preIntegrate=OFF, 
        material=fiber_matname, thicknessType=UNIFORM, thickness=0.01*blockSize, thicknessField='', 
        idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT, 
        thicknessModulus=None, temperature=GRADIENT, useDensity=OFF, 
        integrationRule=SIMPSON, numIntPts=5)
    
    mdb.models[model_name].HomogeneousShellSection(name=matrix_setname, preIntegrate=OFF, 
        material=matrix_matname, thicknessType=UNIFORM, thickness=0.01*blockSize, 
        thicknessField='', idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT, 
        thicknessModulus=None, temperature=GRADIENT, useDensity=OFF, 
        integrationRule=SIMPSON, numIntPts=5)
    
    #-------
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    faces = f.getSequenceFromMask(mask=('[#2 ]', ), )
    region = p.Set(faces=faces, name=fiber_setname)
    p = mdb.models[model_name].parts[part2DName]
    p.SectionAssignment(region=region, sectionName=fiber_setname, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
    
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    faces = f.getSequenceFromMask(mask=('[#1 ]', ), )
    region = p.Set(faces=faces, name=matrix_setname)
    p = mdb.models[model_name].parts[part2DName]
    p.SectionAssignment(region=region, sectionName=matrix_setname, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
    
    #assign material direction
    #-----------------------------------------
    p = mdb.models[model_name].parts[part2DName]
    region = p.sets[fiber_setname]
    orientation = None
    mdb.models[model_name].parts[part2DName].MaterialOrientation(region=region, 
        orientationType=GLOBAL, axis=AXIS_1, additionalRotationType=ROTATION_NONE, 
        localCsys=None, fieldName='')
    #: Specified material orientation has been assigned to the selected regions.
    p = mdb.models[model_name].parts[part2DName]
    region = p.sets[matrix_setname]
    orientation = None
    mdb.models[model_name].parts[part2DName].MaterialOrientation(region=region, 
        orientationType=GLOBAL, axis=AXIS_1, additionalRotationType=ROTATION_NONE, 
        localCsys=None, fieldName='')    
    
#    session.viewports['Viewport: 1'].setValues(displayedObject=p)
    
    #generate mesh on the quarter shell part
    #-----------------------------------------
    p = mdb.models[model_name].parts[part2DName]
    p.seedPart(size=mesh_size, deviationFactor=0.1, minSizeFactor=0.1)
    elemType1 = mesh.ElemType(elemCode=elementType1, elemLibrary=STANDARD)
    elemType2 = mesh.ElemType(elemCode=elementType2, elemLibrary=STANDARD)
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    pickedRegions = f.getSequenceFromMask(mask=('[#3 ]', ), )
    p.setMeshControls(regions=pickedRegions, elemShape=QUAD, algorithm=MEDIAL_AXIS)
    pickedRegions =(faces, )
    
    faces = f.getSequenceFromMask(mask=('[#3 ]', ), )
    pickedRegions = (faces, )
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2))
    p = mdb.models[model_name].parts[part2DName]
    p.generateMesh()
    #-------------------------
    
    #import the quarter Shell part in the Assembly
    # generate the full shell model by doing 2 reflect
    #-------------------------------------------------------
    a1 = mdb.models[model_name].rootAssembly
    p = mdb.models[model_name].parts[part2DName]
    a1.Instance(name=part2DName+'-1', part=p, dependent=ON)
    a1.Instance(name=part2DName+'-2', part=p, dependent=ON)
    
    a1 = mdb.models[model_name].rootAssembly
    a1.rotate(instanceList=(part2DName+'-2', ), axisPoint=(0.0, 0.0, 0.0), 
        axisDirection=(0.0, 10.0, 0.0), angle=180.0)
    
    a1 = mdb.models[model_name].rootAssembly
    a1.InstanceFromBooleanMerge(name=part2DName+'half', instances=(a1.instances[part2DName+'-1'], 
        a1.instances[part2DName+'-2'], ), mergeNodes=BOUNDARY_ONLY, 
        nodeMergingTolerance=0.0001*mesh_size, domain=MESH, originalInstances=DELETE)
    
    p1 = mdb.models[model_name].parts[part2DName+'half']
    
     
    
    
    a1 = mdb.models[model_name].rootAssembly
    p = mdb.models[model_name].parts[part2DName+'half']
    a1.Instance(name=part2DName+'half'+'-2', part=p, dependent=ON)
    a1 = mdb.models[model_name].rootAssembly
    a1.rotate(instanceList=(part2DName+'half'+'-2', ), axisPoint=(0.0, 0.0, 0.0), 
        axisDirection=(10.0, 0.0, 0.0), angle=180.0)
    ##: The instance Part-3-2 was rotated by 180. degrees about the axis defined by the point 0., 0., 0. and the vector 10., 0., 0.
    
    a1 = mdb.models[model_name].rootAssembly
    a1.InstanceFromBooleanMerge(name=part2DFullName, instances=(a1.instances[part2DName+'half'+'-1'], 
        a1.instances[part2DName+'half'+'-2'], ), mergeNodes=BOUNDARY_ONLY, 
        nodeMergingTolerance=0.0001*mesh_size, domain=MESH, originalInstances=DELETE)
    
    
    #make the final merged part (shell model) has the same shell element normal (make the element connectivity arranged in the anticlockwise direction)
    p = mdb.models[model_name].parts[part2DFullName]
    z1 = p.elements
    regions = regionToolset.Region(elements=z1)
    p.flipNormal(referenceRegion=z1[1], regions=regions)
    
      
    
    #delete the unwanted part and instances 
    #a.deleteFeatures((part2DName+'-1', part2DName+'-2', part2DName+'half-1',  part2DName+'half-2', ))
    del mdb.models[model_name].parts[ part2DName+'half']
    del mdb.models[model_name].parts[part2DName]
    a = mdb.models[model_name].rootAssembly
    del a.features[part2DFullName+'-1']
    
#    setYZview()
    p = mdb.models[model_name].parts[part2DFullName]
#    session.viewports['Viewport: 1'].setValues(displayedObject = a)
#    session.viewports['Viewport: 1'].view.setViewpoint(viewVector = (1.0, 0.0, 0.0), cameraUpVector = (0.0, 0.0, 1.0))
#    session.viewports['Viewport: 1'].view.fitView()
#    cmap=session.viewports['Viewport: 1'].colorMappings['Material']
#    session.viewports['Viewport: 1'].setColor(colorMapping=cmap)
#    session.viewports['Viewport: 1'].disableMultipleColors()
    
    return p
    


# ==============================================================================
#
#   Square Unidirectional Fiber with Interphase
#
# ==============================================================================

DEFAULT_CONFIG = {
    'model_name': 'Model-1',
    'fiber_flag': 1,
    'vf_f': 0.25,
    'fiber_matname': 'Fiber',
    'matrix_matname': 'Matrix',
    'mesh_size': 0.1,
    'elem_type': 'Linear',
}


def main(config=None):
    """Build a square 2D SG outside the GUI."""
    if config is None:
        config = load_cli_config(DEFAULT_CONFIG)

    ensure_materials_exist(
        mdb,
        config['model_name'],
        [config['fiber_matname'], config['matrix_matname']],
    )
    part = createSqrV5(**config)
    _set_view_yz_if_possible(part)
    return part


if __name__ == '__main__':
    main()

