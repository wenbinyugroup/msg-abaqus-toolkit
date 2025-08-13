# Laminate (1D SG)


## 1D SG preparation

1D SG is simple compared with 2D/3D SG, which allows the GUI save most of the work for the user. This section will introduce 4 methods developed for generating 1D SG respectively. The four methods are: Fast Generate, Composite Layup, Composite Sections, Read from file. Fast Generate function only applies to laminates with constant layer thickness and single material property, while the other 3 methods can apply to general laminates.

Note users must pay attention to the general remarks illustrated in Section 1.2.1 Composite Layup.

The buttons for creating 1D SG are shown in the Fig. 2.1.1.


Fig. 2.1-1 work plane button (in the red frame) and 1D SG button (in the blue frame)

#### _Method 1: Fast Generate_

To create a 1D common SG quickly, Fast Generate function can be applied. Fast Generate function only applies to laminates with constant layer thickness and single material property.

##### _Step 1: Create materials_

The first step is to create a material in Abaqus GUI. The material ‘material-1’ used in this example has the properties as shown in Table 2.1-1.

##### _Step 2: Create geometry and mesh of 1D SG_

Then the user can click the 1D SG button in the blue frame shown in Fig. 2.1-1. In the dialog box popped out in Fig. 2.1-2, choose ‘Fast Generate’, and input the required information: layup, ply thickness, offset ratio, choose model and material which has been created, and element type. Layups can be specified following the tips provided in the dialog box. The meaning of the offset ratio is illustrated in Fig. 2.1-3. The number after bracket means the repeating times and “s” means symmetry.

Table 2.1-1 Material properties

| Material | _E_<sub>1</sub><br><br>GPa | _E_<sub>2</sub><br><br>GPa | _E_<sub>3</sub><br><br>GPa | <sub>12</sub> | <sub>13</sub> | <sub>23</sub> | _G_<sub>12</sub><br><br>GPa | _G_<sub>13</sub><br><br>GPa | _G_<sub>23</sub><br><br>GPa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Material-1 | 117.0 | 8.54 | 8.54 | 0.278 | 0.278 | 0.5 | 3.9 | 3.9 | 2.83 |


Fig. 2.1-2 Create 1D SG dialog box


1. Offset = 0 (b) Offset = -0.5 (c) Offset = +0.5

Fig. 2.1-3 The coordinate origin of the coordinate system in the generated SwiftComp input file (\*.sc) by specifying Offset ratio, where the red hollow circle represents the coordinate origin.

Using the information provided in this dialog box, a 1D SG part named as ‘Laminate’ is created. The layup and offset ratio information are stored in the _Composite Layup_ as shown in Fig. 2.1-4. The offset ratio will not be shown in the geometry of the part ‘Laminate’, but only be saved in the _Offset_ tab book in the dialog box and later be used in generating the input file of SwiftComp™. In other words, Abaqus _Composite Layup_ manager can be used to double check whether the inputs for Fast Generate are correctly provided and interpreted.



Fig. 2.1-4 Composite Layup contain the layup and offset ratio information.

For laminates, the mesh has been generated right after defining laminate. As stated in Section 1.2.1-> Mesh, the element type chosen in Abaqus is B31 with 2 nodes in each element. In this example, we create a 1D SG containing 4 plies (\[45/-45\]s laminate), which require 4 elements in SwiftComp. Each five-noded element in SwiftComp is composed of 4 B31 element in Abaqus, therefore the 1D SG has 16 B31 elements in all as shown in Fig. 2.1-5. Note it is not an approximation but a technique to trick Abaqus to generate 5-noded elements for SwiftComp, which is particularly needed if the macroscopic structural model is a plate/shell model.


Fig. 2.1-5 16 B31 elements are generated for a 4 ply 1D SG with five-noded element type in SwiftComp.

#### _Method 2: Composite Layup_

This method takes advantage of the Composite Layup function of Abaqus GUI, which allows ply thickness and material properties to be different in each ply.

##### _Step 1: Create materials_

To create a customized 1D SG, the first step is to create the materials in Abaqus GUI. In this example, we use the material properties shown in Table 3.1.

Table 2.1-1 Material properties

| Material name | _E_<sub>1</sub><br><br>GPa | _E_<sub>2</sub><br><br>GPa | _E_<sub>3</sub><br><br>GPa | <sub>12</sub> | <sub>13</sub> | <sub>23</sub> | _G_<sub>12</sub><br><br>GPa | _G_<sub>13</sub><br><br>GPa | _G_<sub>23</sub><br><br>GPa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Laminate-mat1 | 250.0 | 50.0 | 50.0 | 0.25 | 0.25 | 0.25 | 2.0 | 2.0 | 5.0 |
| Laminate-mat2 | 200.0 | 20.0 | 20.0 | 0.3 | 0.3 | 0.3 | 2.0 | 2.0 | 5.0 |

##### _Step 2: Set work plane_

As stated in section 1.2.1 Geometry, 1D SG must align with Z axis. This is achieved by the work plane button (in the red frame in Fig. 2.1-1). Click the work plane button, the dialog box in Fig. 2.1-6 pops out, then choose the model and give the part name for the 1D SG part, choose the SG dimension to be 1D. The work plane button will create a datum plane and a datum axis in the part. The work plane button also creates a temporary line geometry in Z direction, and a set named ‘Set_Layup’ as shown in Fig. 2.1-7.


Fig. 2.1-6 work plane button dialog box


Fig. 2.1-7 After use the work plane button

##### _Step 3: Create Composite Layup_

Then the user can use _Create Composite Layup_ tool in the Property module to create composite layup and assign _Region_ using the set ‘Set_Layup’ as shown in Fig. 2.1-8 and Fig. 2.1-9. The first 4 options of the ‘Offset’ tab book can be used to specify offset of the coordinate origin in the \*.sc file. In this example, the default offset ratio (0.0) is kept. The parameter ‘Offset’ has the same meaning of ‘Offset ratio’ as explained in Section 2.1.


Fig. 2.1-8 Create composite layup


Fig. 2.1-9 Configure the composite layup

##### _Step 4: Create geometry and mesh of 1D SG_

The next step to create a 1D customized SG is to choose the ‘Composite Layup’ method in dialog box of the 1D SG button (Fig. 2.1-10). After this step, the temporary line geometry will be deleted, and the actual 1D SG composed of consecutive edges is created, of which each edge represents a ply.


Fig. 2.1-10 Use Composite Layup method to create general 1D SG


Fig. 2.1-11 The 1D SG created (numbers in orange are element numbers)

After Step 4, the 1D SG has been built. The user can check the element number in the Mesh module as shown in Fig. 2.1-11. Similar to the 1D SG generated by fast generated method, each edge represents an element in SG, which contains 4 B31 elements. Therefore there are 16 B31 elements in the model. The created part can be used for homogenization and dehomogenization analysis. Clearly the ‘Fast Generate’ method does the same thing as what does in ‘Composite Layup’ method for simple laminate cases.

#### _Method 3: Composite sections_

This method take advantage of the Sections-> _Composite sections_ function of Abaqus GUI, which allows ply thickness and material properties to be different in each ply.

##### _Step 1: Create materials and Composite sections_

To use this method, first the user need to create mateirals and composite sections in the model, as shown in Fig. 2.1-12. The _Element Relative Thickness_ is the actual ply thickness. _Symmetric layers, Layup name_ and _Ply Name_ in the dialog box are ignored in creating 1D SG.


Fig. 2.1-12 Create Composite Sections


##### _Step 2: : Create geometry and mesh of 1D SG_

The next step to create a 1D customized SG is to choose the ‘Composite Section’ method in dialog box of the 1D SG button (Fig. 2.1-13) and input the required parameters. The parameter ‘Offset’ has the same meaning of ‘Offset ratio’ as explained in Section 2.1.

Click OK, the 1D SG will be created. An Composite Layup containing the information from the Composite Section will also be created. In Homogenization, the information of the 1D SG will be read from the Composite Layup instead of the Composite Section. Therefore multiple Composite Sections are allowed to exist, but only 1 Composite Layup is allowed to exist in a SG.


Fig. 2.1-13 Use Composite Section method to create general 1D SG

#### _Method 4: Read from file_

This method also allows ply thickness and material properties to be different in each ply. The information except material properties will be read from a \*.dat file.

In this example, we use the file showin in Fig. 2.1.14.

##### _Step 1: Create materials_

To use this method, first the user need to create mateirals in the model. Here we use the material properties in Table 2.1.

##### _Step 2: Prepare layup input file_

In this example we prepare a file as shown in Fig. 2.1-14. The format has explained in the Section 1.2.1 Layup file format.


Fig. 2.1-14 layup input file (\*.dat)

##### _Step 3: Create geometry and mesh of 1D SG_

Choose this file in the dialog box: 1D Structure Genome as shown in Fig. 2.1-15.


Fig. 2.1-15 The 1D SG created (numbers in orange are element numbers)

Then the 1D SG will be created, of which the composite layup information can be checked in the Composite Layup Dialog box as shown in the Fig.2.1-16.


Fig. 2.1-16 The composite layup of the1D SG created

## Homogenization

We will use the model generated by fast generate to show the results of Homogenization and Dehomogenization.

Click the homogenization button in the red frame of Fig. 2.1-17, a dialog box in Fig. 2.1-18 will pop up.

In this example, if we choose 3D (solid) for the macro model dimension, then the default file name will be Laminate_nSG1_3D_n5.sc, where 3D stands for 3D solid model.


Fig. 2.1-17 Homogenization button


Fig. 2.1-18 Homogenization dialog box for 3D solid model

Click OK and wait for preparing the input file of SwiftComp™ and homogenization.

After the computation of SwiftComp™, the effective properties will pop up automatically (Fig. 2.1-19).


Fig. 2.1-19 Effective properties of 3D solid model

In the homogenization, the basic information of the SG model as shown in Fig. 2.1-20 have been saved into sg model, which can be accessed by python script using the path ‘mdb.customData.sgs\[sg_name\]’, where ‘sg_name’ is the SwiftComp file name in homogenization.


Fig. 2.1-20 sg model data created after homogenization

If we choose plate/shell model (Fig. 2.1-21), the default file name will be Laminate_nSG1_2D_n5.sc where 2D stands for a plate/shell model (2D). After homogenization, the ABD matrix of the homogenized plate/shell will be obtained (Fig. 2.1-22). The offset ratio will influence the results of plate/shell model as it effectively sets the reference surface at different locations. Note 1D SG cannot be used for beam model.


Fig. 2.1-21 Homogenization dialog box-use 2D shell model


Fig. 2.1-22 ABD matrix of classical plate/shell model

## Dehomogenization

Click the dehomogenization button in the red frame of Fig. 2.1-23, the dehomogenization dialog box in Fig. 2.2-24 (a) will pop out.


Fig. 2.1-23 Dehomogenization button

There are two methods provided to choose the SG we have created previously. The first method is to choose the sg_name shown in the list while the SG model source is ‘CAE’. The second method is to choose the SwiftComp input file ‘Laminate_nSG1_3D_n5.sc’ if the SG model source is ‘SwiftComp input file’. Using this method, the Analysis type and the Macroscopic model type must be specified correctly, otherwise there will be an error message popped up (Fig.2.1-24 (b)). For both methods, the SwiftComp input file (.sc), the homogenization result files (.sc.k and .sc.opt) should be in the current work directory, which are needed in the dehomogenization. If you used CAE to generate the model, carried out the homogenization, the files are already stored in the work directory.

Specify the required inputs as shown in Fig. 2.2-24. Please refer to SwiftComp™ manual for meaning of the global behavior parameters.


1. Two methods to choose the homogenizaiton results files (.sc, .sc.k, .sc.opt)


1. Error message if choose the wrong macroscopic model type

Fig. 2.1-24 Dehomogenization parameters for 3D solid model

Click OK and wait for SwiftComp™ to finish the computation. The post-processing results will be automatically loaded. However the user need to switch to the Visualization model to view all the field results components, including displacement (U1, U2, U3) and its magnitude, six nodal strain components (EN11, EN22, EN33, 2EN23, 2EN13, 2EN12) and the derived quantities such as Mises strain, six nodal stress components (SN11, SN22, SN33, SN23, SN13, SN12) and the derived quantities such as Mises stress. The nodal stress SN12 components is shown in Fig. 2.1-25. In the odb tree, sections ‘nlayer - 1’, ‘nlayer - 2’ are created, with each section containing the plies with the same material properties and the same layer angle.


Fig. 2.1-25 Dehomogenization results of 3D model

If using shell model, choose the SwiftComp input file ‘Laminate_nSG1_2D_n5.sc’ and specify the required inputs as shown in Fig. 2.1.26. Please refer to SwiftComp™ manual for meaning of the global behavior parameters.


Fig. 2.1-26 Dehomogenization parameters for shell model

Contour plots are available for all local fields. In the odb tree, sections ‘nlayer - 1’, ‘nlayer - 2’ are created, with each section containing the plies with the same material properties and the same layer angle. The nodal stress SN12 component is shown in Fig. 2.1-27.


Fig. 2.1-27 Dehomogenization results of shell model

