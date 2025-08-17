(guide-add-layup)=
# Add Layup

Users can use function "New layups" to create Solid-Composite sections which will be used later.
There are two ways to do this. One is through fast generation, the other one is reading from file.

## Fast generation

In this method, user can generate a layup through a rule, such as \[0/90/45/-45\]2s. User needs to first create a material. Then provide a new composite section name and the layup rule. The thickness at the last is for each ply. This method is only suitable for layups with a single material having different fiber orientations and all plies with the same thickness, which is the most common case in industry


## Read from file

In this method, user needs to prepare a material file and a layup file. To create composite sections, select ‘Read from file’ in the dialog box, and choose the material file and the layup file, then click ‘OK’. Both the material file and layup file should use the XMLformat and details are described below. Users are encouraged to have some basic knowledge on XML files. A quick and simple tutorial can be found at <http://www.tutorialspoint.com/xml/index.htm>.


1. Material file

The root element is ‘&lt;materials&gt;&lt;/materials&gt;’ and each ‘&lt;material&gt;&lt;/material&gt;’ sub-element store one material. For the current version, we can only deal with materials with density and elastic properties.

&lt;materials&gt;

&lt;material type = "ENGINEERING CONSTANTS"&gt;

&lt;id&gt;**1**&lt;/id&gt;

&lt;name&gt;**iso5_1**&lt;/name&gt;

&lt;density&gt;**1.860000E+03**&lt;/density&gt;

&lt;e1&gt;**3.7000E+10**&lt;/e1&gt;

&lt;e2&gt;**9.0000E+09**&lt;/e2&gt;

&lt;e3&gt;**9.0000E+09**&lt;/e3&gt;

&lt;g12&gt;**4.0000E+09**&lt;/g12&gt;

&lt;g13&gt;**4.0000E+09**&lt;/g13&gt;

&lt;g23&gt;**4.0000E+09**&lt;/g23&gt;

&lt;nu12&gt;**0.28**&lt;/nu12&gt;

&lt;nu13&gt;**0.28**&lt;/nu13&gt;

&lt;nu23&gt;**0.28**&lt;/nu23&gt;

&lt;/material&gt;

&lt;material&gt;

...

&lt;/material&gt;

...

&lt;/materials&gt;

Each material has a ‘type’ attribute, which has the same definition as Abaqus, ISOTROPIC, ENGINEERING CONSTANTS, ORTHOTROPIC or ANISOTROPIC. For each material, user needs to provide a unique ‘id’ and ‘name’. The ‘density’ is optional. When omitted, it will use the default value 1.0. The components of elastic properties for each type are the same as those in Abaqus, and the arrangement of components will not be a problem. For ISOTROPIC, we have 2 components, ‘e’ and ‘nu’. For ENGINEERING CONSTANTS, we have 9 components, ‘e1’, ‘e2’, ‘e3’, ‘g12’, ‘g13’, ‘g23’, ‘nu12’, ‘nu13’ and ‘nu23’. For ORTHOTROPIC, we have 9 components, ‘d1111’, ‘d1122’, ‘d2222’, ‘d1133’, ‘d2233’, ‘d3333’, ‘d1212’, ‘d1313’ and ‘d2323’. For ANISOTROPIC, we have 21 components, ‘d1111’, ‘d1122’, ‘d2222’, ‘d1133’, ‘d2233’, ‘d3333’, ‘d1112’, ‘d2212’, ‘d3312’, ‘d1212’, ‘d1113’, ‘d2213’, ‘d3313’, ‘d1213’, ‘d1313’, ‘d1123’, ‘d2223’, ‘d3323’, ‘d1223’, ‘d1323’ and ‘d2323’.

1. Layup file

The root element is ‘&lt;layups&gt;&lt;/layups&gt;’ and each ‘&lt;layup&gt;&lt;/layup&gt;’ sub-element stores one layup.

&lt;layups&gt;

&lt;layup&gt;

&lt;id&gt;**1**&lt;/id&gt;

&lt;name&gt;**layup1**&lt;/name&gt;

&lt;data&gt;

**0.0003810000000 3 0**

**0.0005099999960 4 0**

**0.0095400001224 2 20**

&lt;/data&gt;

&lt;/layup&gt;

...

&lt;/layups&gt;

For each layup, user need to provide a unique ‘id’ and ‘name’. In the ‘&lt;data&gt;&lt;/data&gt;’ sub-element, each line is a ply, where the first number is the thickness, the second one is the material id defined in materials.xml and the last one is the fiber orientation angle in degrees.