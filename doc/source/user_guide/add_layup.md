(guide-add-layup)=
# Add Layup

Users can use function **New layups** ![](../../../assets/icons/add_layups_small.png) to create Solid-Composite sections which will be used later.
There are two ways to do this: **Fast generation** and **Read from file**.

## Fast generation

In this method, user can generate a layup through a rule, such as \[0/90/45/-45\]2s.
User needs to first create a material.
Then provide a new composite section name and the layup rule.
The thickness at the last is for each ply.
This method is only suitable for layups with a single material having different fiber orientations and all plies with the same thickness, which is the most common case in industry

```{figure} /_static/images/create-layups-db-fast.png
:align: center

Fast generation of layup.
```


## Read from file

In this method, user needs to prepare a material file and a layup file.
To create composite sections, select **Read from file** in the dialog box, and choose the material file and the layup file, then click **OK**.
Both the material file and layup file should use the XML format and details are described below.
Users are encouraged to have some basic knowledge on XML files.
A quick and simple tutorial can be found at <http://www.tutorialspoint.com/xml/index.htm>.

```{figure} /_static/images/create-layups-db-file.png
:align: center

Read from file.
```


### Material file

The root element is `<materials></materials>` and each `<material></material>` sub-element store one material.
For the current version, we can only deal with materials with density and elastic properties.
```xml
<materials>
    <material type="ENGINEERING CONSTANTS">
        <name>iso5_1</name>
        <density>1.860000E+03</density>
        <e1>3.7000E+10</e1>
        <e2>9.0000E+09</e2>
        <e3>9.0000E+09</e3>
        <g12>4.0000E+09</g12>
        <g13>4.0000E+09</g13>
        <g23>4.0000E+09</g23>
        <nu12>0.28</nu12>
        <nu13>0.28</nu13>
        <nu23>0.28</nu23>
    </material>
    <material>
        ...
    </material>
    ...
</materials>
```

Each material has a **type** attribute, which has the same definition as Abaqus, ISOTROPIC, ENGINEERING CONSTANTS, ORTHOTROPIC or ANISOTROPIC.
For each material, user needs to provide a unique **name**.
The **density** is optional.
When omitted, the default value 1.0 will be used.
The constants of elastic properties for each type are the same as those in Abaqus.
- For ISOTROPIC, 2 constants are needed: 'e' and 'nu'.
- For ENGINEERING CONSTANTS, 9 constants are needed: 'e1', 'e2', 'e3', 'g12', 'g13', 'g23', 'nu12', 'nu13', and 'nu23'.
- For ORTHOTROPIC, 9 constants are needed: 'd1111', 'd1122', 'd2222', 'd1133', 'd2233', 'd3333', 'd1212', 'd1313', and 'd2323'.
- For ANISOTROPIC, 21 constants are needed: 'd1111', 'd1122', 'd2222', 'd1133', 'd2233', 'd3333', 'd1112', 'd2212', 'd3312', 'd1212', 'd1113', 'd2213', 'd3313', 'd1213', 'd1313', 'd1123', 'd2223', 'd3323', 'd1223', 'd1323', and 'd2323'.

### Layup file

The root element is `<layups></layups>` and each `<layup></layup>` sub-element stores one layup.

```xml
<layups>
    <layup>
        <name>layup_1</name>
        <layer>
            <thickness>0.1</thickness>
            <material>mat_1</material>
            <fiber_orient>0</fiber_orient>
        </layer>
        <layer>
            ...
        </layer>
        ...
    </layup>
    ...
</layups>
```

For each layup, user needs to provide a unique 'name'.
Each layup has any number of layers, and for each layer, user needs to provide thickness, material name and fiber orientation.
