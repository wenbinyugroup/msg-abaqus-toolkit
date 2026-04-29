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

def createHexV5(model_name , fiber_flag,vf_f, fiber_matname,matrix_matname,mesh_size,elem_type):

    #---------------------------------------------------------
    part2DName = 'hexP2' + 'quater'
    part2DFullName = 'hexP2'
    partsobj = mdb.models[model_name].parts
    
    print('#-------part_name  %s---------------------------'  % part2DFullName)
    #---------------------------------------
    #### Define Parameters
    #--------------------------------------
    
    blockSize = 1.0
    blockSizeA = blockSize / 2.0
    blockSizeB = blockSize * sqrt(3.0) / 2.0
    meshSize = mesh_size
    
    if elem_type == 'Linear':
        elementType1 = S4
        elementType2 = S3
    elif elem_type == 'Quadratic':
        elementType1 = S8R
        elementType2 = STRI65
    else:
        raise ValueError('Unknown elem_type: %s' % elem_type)
    
    totalArea = blockSizeA * blockSizeB * 4.0
    
    if fiber_flag == 1: #vf_f is volume fraction  of the fiber
        vof_fiber = vf_f
        fiberRadius = blockSize * sqrt(sqrt(3.0)*vof_fiber/2.0/pi)
    elif fiber_flag == 2:  #vf_f is radius of the fiber
        fiberRadius = vf_f
        vof_fiber = 2.0 * pi * fiberRadius**2.0 / totalArea

    print('blockSize: %s' %blockSize)
    print('totalArea: %s' %totalArea)               
    
    print('#---fiber------------------------')
    print('vof_fiber: %s' %vof_fiber)
    print('fiberRadius: %s' %fiberRadius)
    
    if fiberRadius >= blockSize/2.0 :
        raise ValueError('The volume fraction of fiber is out of range. Please adjust the values.' )

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
    s.rectangle(point1=(0.0, 0.0), point2=(blockSizeA , blockSizeB ))
    p = mdb.models[model_name].parts[part2DName]
    e1, d2 = p.edges, p.datums
    p.Shell(sketchPlane=d2[datumPlaneYZ_id], sketchUpEdge=d2[datumAxisZ_id], sketchPlaneSide=SIDE1, 
        sketchOrientation=RIGHT, sketch=s)
    s.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']
       
    #Define fiber on the shell
    #--------------------------------------
    p = mdb.models[model_name].parts[part2DName]
    f, e, d1 = p.faces, p.edges, p.datums
    t = p.MakeSketchTransform(sketchPlane=f[0], sketchUpEdge=e[1], 
        sketchPlaneSide=SIDE1, origin=(0.0, 0.0, 0.0))
    s1 = mdb.models[model_name].ConstrainedSketch(name='__profile__', 
        sheetSize=blockSize*4.00, gridSpacing=0.1*blockSize, transform=t)
    g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
    s1.setPrimaryObject(option=SUPERIMPOSE)
    p = mdb.models[model_name].parts[part2DName]
    p.projectReferencesOntoSketch(sketch=s1, filter=COPLANAR_EDGES)
    s1.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, fiberRadius), point2=(fiberRadius, 
        0.0), direction=CLOCKWISE)
    s1.CoincidentConstraint(entity1=v[4], entity2=g[5], addUndoState=False)
    s1.CoincidentConstraint(entity1=v[5], entity2=g[2], addUndoState=False)
    #: Warning: Cannot continue yet--complete the step or cancel the procedure.
    s1.ArcByCenterEnds(center=(blockSizeA, blockSizeA*sqrt(3)), point1=(blockSizeA-fiberRadius,blockSizeA*sqrt(3)), point2=(blockSizeA, 
        blockSizeA*sqrt(3)-fiberRadius), direction=COUNTERCLOCKWISE)
    s1.CoincidentConstraint(entity1=v[6], entity2=g[4], addUndoState=False)
    s1.CoincidentConstraint(entity1=v[7], entity2=g[3], addUndoState=False)
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    pickedFaces = f.getSequenceFromMask(mask=('[#1 ]', ), )
    e1, d2 = p.edges, p.datums
    p.PartitionFaceBySketch(sketchUpEdge=e1[1], faces=pickedFaces, sketch=s1)
    s1.unsetPrimaryObject()
    del mdb.models[model_name].sketches['__profile__']
    
    #Define materials and Sections and assign them
    #--------------------------------------
   
    #create sections
    mdb.models[model_name].HomogeneousShellSection(name=matrix_setname, preIntegrate=OFF, 
        material=matrix_matname, thicknessType=UNIFORM, thickness=0.01*blockSize, 
        thicknessField='', idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT, 
        thicknessModulus=None, temperature=GRADIENT, useDensity=OFF, 
        integrationRule=SIMPSON, numIntPts=5)
    mdb.models[model_name].HomogeneousShellSection(name=fiber_setname, preIntegrate=OFF, 
        material=fiber_matname, thicknessType=UNIFORM, thickness=0.01*blockSize, thicknessField='', 
        idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT, 
        thicknessModulus=None, temperature=GRADIENT, useDensity=OFF, 
        integrationRule=SIMPSON, numIntPts=5)
    #Assign sections    
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    faces = f.getSequenceFromMask(mask=('[#3 ]', ), )
    region = p.Set(faces=faces, name=fiber_setname)
    p = mdb.models[model_name].parts[part2DName]
    p.SectionAssignment(region=region, sectionName=fiber_setname, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    faces = f.getSequenceFromMask(mask=('[#4 ]', ), )
    region = p.Set(faces=faces, name=matrix_setname)
    p = mdb.models[model_name].parts[part2DName]
    p.SectionAssignment(region=region, sectionName=matrix_setname, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
    
    #generate mesh on the quarter shell part   
    #----------------------------------------------    
    p = mdb.models[model_name].parts[part2DName]
    p.seedPart(size=meshSize, deviationFactor=0.1, minSizeFactor=0.1)
    elemType1 = mesh.ElemType(elemCode=elementType1, elemLibrary=STANDARD)
    elemType2 = mesh.ElemType(elemCode=elementType2, elemLibrary=STANDARD)
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    faces = f.getSequenceFromMask(mask=('[#7 ]', ), )
    pickedRegions =(faces, )
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2))
    
    p = mdb.models[model_name].parts[part2DName]
    f = p.faces
    pickedRegions = f.getSequenceFromMask(mask=('[#7 ]', ), )
    p.setMeshControls(regions=pickedRegions, elemShape=QUAD, algorithm=MEDIAL_AXIS)
    p = mdb.models[model_name].parts[part2DName]
    p.generateMesh()
    
    #import the quarter Shell part in the Assembly
    # generate the full shell model by doing 2 reflect
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
        nodeMergingTolerance=0.0001*meshSize, domain=MESH, originalInstances=DELETE)
    
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
        nodeMergingTolerance=0.0001*meshSize, domain=MESH, originalInstances=DELETE)
    
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
#   Hexagonal Unidirectional Fiber with Interphase
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
    """Build a hexagonal 2D SG outside the GUI."""
    if config is None:
        config = load_cli_config(DEFAULT_CONFIG)

    ensure_materials_exist(
        mdb,
        config['model_name'],
        [config['fiber_matname'], config['matrix_matname']],
    )
    part = createHexV5(**config)
    _set_view_yz_if_possible(part)
    return part


if __name__ == '__main__':
    main()

