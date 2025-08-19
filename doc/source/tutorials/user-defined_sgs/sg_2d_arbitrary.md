# Arbitrary Shape Inclusions Microstructure (2D SG)



One more user-defined model is shown here, which is a rectangle SG with two arbitrary inclusions. Users can understand how to create complex shape in Abaqus-SwiftComp GUI, and also know the capability of SwiftComp™ to calculate such models.

## Step 1: Create materials and sections

In this example, assume that both inclusions and matrix are isotropic materials (Material 1: _E_ = 379.3 GPa,  = 0.1; Material 2: _E_ = 279.3 GPa,  = 0.1; Material 3: _E_ = 68.3 GPa,  = 0.3).


Fig. 3.2-1 Create materials and sections

## Step 2: Set work plane

Following the procedure as shown in section 3.2 Step 2, the work plane of 2D SG can be created.

## Step 3: Create geometry of 2D customized SG

First create the rectangular shell using points (-0.5, -1), (0.5, 1) as shown in Fig. 3.2-2(a).


1. (b)

Fig. 3.2-2 Create geometry of the SG

Click the tool button ‘Partition face: Sketch’ (Fig. 3.2-2 (b)), then create the isolated points (-0.2, 0.8, 0), (-0.3, 0.7, 0,), (-0.3, 0.4, 0), (-0.1, 0.6, 0), (0, 0.8, 0), (0, 0, 0), (-0.1, 0, 0), (-0.2, -0.3, 0), (0.1, -0.5, 0), (0.1, -0.3, 0) and (0.2, -0.1, 0) (see Fig. 3.2-3 (a)). Create splines through the points as shown in Fig. 3.2-3 (b).


## Step 4: Assign material sections, create mesh for the 2D customized SG

In the property module, the user can assign the material sections created in the first step to the geometry (Fig. 3.2-4).


Fig. 3.2-4 Assign material sections

## Step 5: Generate User-defined Model Mesh

In this example, _Global seeds_ are applied, and the mesh is generated using the _Mesh Controls setting_: _Quad-dominated Element Shape, Free-Technique, Advanced front–use mapped meshing where appropriate Algorithm_. The mesh shown in the Fig. 3.2-5 is quite irregular but can be used for homogenization analysis. However, it can be seen that there is one element (highlighted in the yellow ellipse is abnormal. If use this mesh to do the dehomogenization, there will be an error message in the command window (Fig. 3.2-6). Such a mesh can be repaired as shown in Fig. 3.2-7.


Fig. 3.2-5 Mesh need to be repaired


Fig. 3.2-6 Error message in dehomogenization


Fig. 3.2-7 repair the mesh

## Step 6: Homogenization and dehomogenization

Click the homogenization button, and fill the dialog box as shown in the Fig. 3.2-8, the effective properties is obtained (Fig. 3.2-9).

Click the dehomogenization button, and fill the dialog box as shown in the Fig. 3.2-10, the local fields are obtained (Fig. 3.2-11).


Fig. 3.2-8 Homogenization


Fig. 3.2.9 Effective properties


Fig. 3.3-10 Dehomogenization


Fig. 3.3-11 Dehomogenization result: magnitude of displacement

