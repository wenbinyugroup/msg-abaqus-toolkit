# SG Preparation


SG creation tool buttons (3-8) can help the user to set up the configurations of SGs.

Abaqus functions are highly integrated in building the SGs, such as materials, composite layup, section assignment, mesh etc. But some settings in the original Abaqus GUI are not used, and the meanings of some parameters are different, which needs special attentions from the user. The details will be explained in the following sections. For convenience, the term ‘**Abaqus GUI**’ is referred in this manual when using the functions of the original Abaqus, otherwise ‘**Abaqus-SwiftComp GUI**’ is explicitly specified. _Italic texts_ represents the terms shown in dialog box of Abaqus GUI, and texts in ‘ ’ represents terms shown in dialog box of Abaqus-SwiftComp GUI.

## Geometry

Users can create common SGs using the 1D SG button (3), 2D SG button (4), or 3D SG button (8), which provides common microstructures of composites for 1D, 2D and 3D SGs respectively. Or they can build customized 2D SGs using button 5, 6, 7 or Abaqus functions.

According to the convention of SwiftComp<sup>TM</sup>, for 1D SGs, the geometry should be aligned with Z direction in the global coordinate system; for 2D SGs, the geometry should be in the Y-Z plane in the global coordinate system. The work plane button help the user set up the work plane for customized 1D SGs and 2D SGs.

For 1D customized SG, the work plane button also creates a temporary line geometry in Z direction, and a set named ‘Set_Layup’. Then the user can use _Create Composite Layup_ tool button of Abaqus GUI to create composite layup, in which _Region_ is assigned using the set ‘Set_Layup’. The next step to create a 1D customized SG is to choose the ‘Composite Layup’ method in dialog box of the 1D SG button. After this step, the temporary line geometry will be deleted, and the actual 1D SG composed of consecutive line segments is created, of which each line segment represents a ply.

To create the geometry for a 2D customized SG, the next step is to use _Create Shell: Planar_ button. Other procedures are the same as creating a 3D shell part in Abaqus GUI.

The procedure to create 3D customized SG geometry is the same as that to create a 3D part in Abaqus GUI.

## Material

In the Material module, the _elastic_ materials properties can be defined by types: _Isotropic, Engineering Constants, Orthotropic_ and _Anisotropic_. If effective density of SG is required, _density_ of the material should be specified; if thermoelastic analysis is conducted, _Expansion_ and _Specific Heat_ should be specified. If density, expansion and specific heat are required in the analysis but not specified, Abaqus-SwiftComp GUI will not ask for it, but use the default values, information will be shown in the message area. All the material properties can only be defined in the most basic way, advanced options such as _temperature-dependent data_, _discrete fields_ cannot be used in the current version. Just like in Abaqus GUI, materials not used in SGs are allowed to exist.

Materials can also be imported from a file, whose format is XML. For more details, please go to section 3.3.2.

## Sections

In Abaqus-SwiftComp GUI, section types _Solid-Homogeneous_, _Shell-Homogeneous, Solid-Composite, Shell-Composite_ are applied. Sections are defined in the same way as in Abaqus GUI. Material sections not assigned to SGs are allowed to exist. Note: For 2D SGs, the geometry should be in the Y-Z plane in the global coordinate system. Abaqus only allow shell feature in 3D space to be placed in the Y-Z plane, thus practically, user can only use _Shell-Homogeneous_ sections.

## Section Assignment

Material section assignment is defined in the same way as in Abaqus GUI. Section assignments are allowed to be depressed, and the depressed sections assignment will be ignored.

## Composite Layup

_Composite Layup of Conventional Shell_ of Abaqus GUI is used in creating composite layup for 1D SGs and 2D SGs. Plies are allowed to be depressed or be edited using the tools in the dialog box. However the current version of Abaqus-SwiftComp GUI sometimes will crash when the user revises an existing composite layup or changes the part name of a 1D SG part, so it is highly recommended to save your work before the revision.

For 1D SG, information of the _Index of the plies (_not the _Ply Name), Material, Thickness, Rotation Angle_ and _Offset_ setting of this dialog box will be read into the input file (\*.sc) of SwiftComp<sup>TM</sup> when doing homogenization. _Region_ should be the set ‘Set_Layup’ which contains the whole 1D SG geometry. The same as that in Abaqus, the laminate is stacked from index ‘1’ to the maximum ply index. Things need to know also include:

1) The _layup orientation_ can only be defined based on the _Part global_ coordinate system.

2) Different from what defined in Abaqus, _Thickness_ in the table is the actual thickness of each ply.

3) If Plate/Shell analysis is conducted, the first 4 option of _Offset_ tab book can be used to shift the coordinate in the input file of SwiftComp™, which have the same definition as that of Abaqus. The shift will not show on the geometry of the SG. This will be further explained in Section 2.1.1 and Section 3.1.1.

4) Only one Composite layup is allowed to exist in a 1D SG part.

## Layup file format

Composite Layup information can also be imported into Abaqus-SwiftComp GUI by choosing layup file (\*.dat) with specific format. Currently this format is only valid for 1D SG. An example of the format is shown in Fig.1.2.1.

The file is composed of 3 parts.

In the first part (in the red frame) it is the layup control parameters.

The second part (in the blue frame) contains the information of each ply from bottom to top, which arranged in the sequence of: ply thickness (integer/float), ply angle (integer/float), material ID (integer).

The third part (in the green frame) provide the corresponding relationship between the material ID and the material name. The material with names shown in this part must be defined previously.

In details, in the first part, the first integer ‘4’ is the number of layers written in the second part, which is not necessarily the actual total number of the laminate). The second integer ‘2’ is the number of material types written in the third part. The character ‘s’ in the third place means ‘symmetric’, therefore the current layup angle is \[45/30/60/-45\]s. This character can also be ‘a’ which means ‘antisymmetric’, if in the current example it is changed to ‘a’, the layup angle will be \[45/30/60/-45/60/30/45\]. The last float ‘0.005’ is the offset ratio, which is explained in Section 2.1.1.


Fig. 1.2.1 layup file format example

Other notes:

1. The character in the third place to denote ‘symmetric/antisymmetric’ can also be any string beginning with ‘s’ or ‘S’ for symmetric laminate (for example ‘sym’), or any string beginning with ‘a’ or ‘A’ for antisymmetric laminate (for example ‘Antisym’). If the laminate is not symmetric or antisymmetric, any other string can be inputed in the third place of the first row.
2. If no offset is necessary, the float in the fourth place is not needed.

A layup can also be imported from a XML file. The ‘New layups’ function will read the material file and layup file and create one or more _Solid-Composite_ sections. For more details, please go to section 3.3.2.

## Orientation Assignment

User can use Abaqus’s own function to assign local element orientation. For 2D cross-section (shell feature in 3D space), there are several things user need to pay attention to. First, no matter what choices user makes for local axes numbering, the two axes shown at last will always be labeled 1 and 2. However, different choices may cause unexpected pointing directions of the two axes. Hence we need to set a rule here: following the convention of local coordinates used in SwiftComp, if a series of elemental coordinates changes along a curve C, the axis 1 in Abaqus will be the axis y2 in SwiftComp and tangent to C, and the axis 2 in Abaqus will be the axis y3 in SwiftComp and perpendicular to C. Second, it doesn’t matter for axis 2 pointing inward or outward, as long as it keeps consistency with the global coordinate **_and_** fiber orientation defined by user, since the fiber orientation will change if the direction of axis 2 (y3) changes.



## Mesh

Mesh must be generated on _Part_ instead of on _Instance_. For 2D customized SGs, element types assigned in Abaqus GUI can be triangular (_TRI_) and quadrangular (_QUAD_), linear or quadratic such as S3, STRI3, S4, S4R, S8R, S8R5, etc. For 3D customize SGs, element types assigned in Abaqus GUI can be hexagonal (_Hex_) and tetrahedral (_Tet_), linear or quadratic such as C3D4, C3D10M, C3D8R, C3D8, C3D20R, C3D20 etc. However, only the nodal coordinates and element connectivities are read into SwiftComp<sup>TM</sup> for analysis, therefore the results are the same whether C3D4 or C3D4R is used.

For 1D SGs, mesh will be done automatically by using the 1D SG button. The element type assigned in GUI is B31, but just as shown in the dialog box of the 1D SG button, the actual element type used in the SG can be two-noded, three-noded, four-noded or five-noded. Each edge in the geometry of 1D SG represents 1 ply and has only 1 element in SwiftComp<sup>TM</sup>. Two-noded elements will be accurate for 3D solid, but five-noded elements are recommended for 2D Plate/Shell.

Special attention needs to be paid on generating periodic mesh. For periodic materials or heterogeneous materials with local periodicity, SwiftComp<sup>TM</sup> requires a mesh with periodic nodes on the edges to rigorously satisfy the periodicity requirement. Theoretically speaking, a node on the boundary surface must have a corresponding node on the parallel boundary surface with the same coordinates except the coordinate component normal to the boundary surface. However, currently this can only be guaranteed by the user. However, for complex microstructures, if it is difficult to create corresponding nodes on the periodic edges, SwiftComp<sup>TM</sup> provides a way to automatically provide the best approximate solution.
