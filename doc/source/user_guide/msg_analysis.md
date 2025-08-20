# MSG Analysis

SwiftComp toolbar provides three buttons for analysis, including **Homogenization** ![](../../../assets/icons/sc_homo_small.png), **Macro model** ![](../../../assets/icons/sc_import_k_small.png), and **Dehomogenization** ![](../../../assets/icons/sc_dehomo_small.png).


## Homogenization: Calculate effective properties

Users can invoke SwiftComp to compute the effective properties for different structural models (beam, plate/shell or 3D solid).
Please refer to the SwiftComp manual for the meaning of the parameters.
In the **Dimensionally Reducible Structures** group box, only the **Classical** in the specific model is supported in the current version.
In the **Options** group box, only **Elastic** and **Thermoelastic** analysis types are supported, the other options should be kept as default.

```{note}
Note 1D SG cannot be used for beam model.
```

The Abaqus-SwiftComp GUI can generate the SwiftComp input file (`*.sc`) from a CAE model or an Abaqus input file.
The user can check the box before **New SwiftComp file name** to specify the SwiftComp input file name, such as "Layup2s", which will generate a file `Layup2s.sc`.
If the file name is not specified, the default file name will be in the form of `<partName>_nSG#_<macroModelDimension>_<elementType>.sc`

For 1D SG, `<elementType>` is in the form of `n#`, where `#` is the number of nodes in each element of the SG.
For 2D and 3D SG, the `<elementType>` is the element type name of the first element in the model, using the term in Abaqus.

The GUI can determine **Omega** (the volume of SG in the irreducible directions) by itself in simple cases as follows:

1. When the SG part has geometry information, and is a line, rectangle or cube.
2. When the SG part has no geometry information, and is a line, rectangle or cube (voids can be in the SG). In this case, when the SG has a huge a number of nodes, specifying **Omega** by the user will speedup the preparation of the model needed for homogenization.

After the homogenization of SwiftComp, the effective properties will pop up automatically.
In some situations that error may occur, the user can check the command line window and it should report the error message of running SwiftComp, which gives your indication what is wrong with the model.


## Macro model: Import the homogenized properties

The effective properties obtained from homogenization can be used in macro model analysis.
Using this button can help user import the effective properties into a newly created model with the name of the SwiftComp input file.
In the current version of Abaqus-SwiftComp GUI, effective properties of 1D macroscopic model (beam) will not be imported into Abaqus, since no beam element in Abaqus can take a fully populated stiffness matrix.
Thus user need to choose other methods to carry out the macroscopic model analysis for beams.
More details are explained in Section 4.0.


## Dehomogenization: Calculate local fields

To conduct dehomogenization analysis, users must provide the homogenization files (`*.sc`, `*.sc.k`, `*.sc.opt`) of the SG and the global behavior parameters.
The homogenization files must be in the current work directory.
There are two methods to provide the homogenizations files.
The details are explained in Section 2.1.3.

User must specify the global behavior parameters.
Please refer to SwiftComp manual for the meaning of each the global behavior parameter in this dialog box.
With provided global behavior, users can invoke SwiftComp to compute the local fields including displacements, stresses and strains and other possible fields of interests, depending on the analysis.
The information will then be used to create an odb file with the same name as the SwiftComp input file, so that the user can use the functions in the **Visualization** module of Abaqus/CAE for postprocessing of the results.
The post-processing results are automatically loaded, but the users need to change to the **Visualization** model by themselves.
Contour plots are available for all local fields including three displacement components (U1, U2, U3) and its magnitude, six nodal strain components (EN11, EN22, EN33, 2EN23, 2EN13, 2EN12) and the derived quantities such as Mises strain, six nodal stress components (SN11, SN22, SN33, SN23, SN13, SN12), and other possible fields of interest, depending on the analysis and the derived quantities such as Mises stress.

In the current version, the ODB file contains no information of geometry and material properties and geometry, although sections are kept.
Under the `*.odb` trunk of the **Output Database** tree, sections can be found, and each section contains the elements with the same material properties.
For 1D SGs, each section contains elements with the same material properties and the same layer angle.
