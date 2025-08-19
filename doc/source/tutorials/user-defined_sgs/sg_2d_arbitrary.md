(tutorial-user-defined-sg-2d-arbitrary)=
# Arbitrary Shape Inclusions Microstructure (2D SG)

An example with user-defined microstructure is shown here, which is a rectangular SG with two arbitrarily shaped inclusions.
Users can learn how to create arbitrary shapes in Abaqus-SwiftComp GUI and let SwiftComp calculate such models.


## Step 1: Create materials and sections

In this example, consider the following material properties:
- Material 1: $E$=379.3 GPa, $\nu$=0.1
- Material 2: $E$=279.3 GPa, $\nu$=0.1
- Material 3: $E$=68.3 GPa, $\nu$=0.3

```{figure} /_static/images/sg-2d-custom-any-material-manager-db.png
:align: center

Created materials.
```


## Step 2: Set work plane

Click the **Work plane** button ![](../../../../assets/icons/sc_wp_small.png) to open the dialog box.

Choose **SG Dimension** > **2D**, then click **OK**.

```{figure} /_static/images/sg-2d-set-sketch-plane-db.png
:align: center

Set work plane.
```


## Step 3: Create geometry

In **Module** > **Part**, click the **Create Shell: Planar** to sketch the geometry.

```{figure} /_static/images/sg-2d-set-sketch-plane-after.png
:align: center

Create shell planar.
```

First create the rectangular shape using points (-0.5, -1), (0.5, 1) as shown in Fig. 3.2-2(a).

Use **Partition face: Sketch** to create the two inclusions (Fig. 3.2-2 (b)).

```{figure} /_static/images/sg-2d-custom-any-geo.png
:align: center

Create the overall shape of the SG.
```

Create the isolated points (-0.2, 0.8), (-0.3, 0.7), (-0.3, 0.4), (-0.1, 0.6), (0, 0.8), (0, 0), (-0.1, 0), (-0.2, -0.3), (0.1, -0.5), (0.1, -0.3), and (0.2, -0.1) (see Fig. 3.2-3 (a)).
Create splines through the points as shown in Fig. 3.2-3 (b).

```{figure} /_static/images/sg-2d-custom-any-geo-2.png
:align: center

Create the inclusions of the SG.
```


## Step 4: Create and assign sections

Create and assign sections as shown in Fig. 3.2-4.


```{figure} /_static/images/sg-2d-custom-any-section-manager-db.png
:align: center

Created sections.
```

```{figure} /_static/images/sg-2d-custom-any-section-assign.png
:align: center

Assign sections
```


## Step 5: Generate mesh

In **Module** > **Mesh**, click the **Seed Part** to set the mesh size.
Set **Approximate global size** to 0.05, then click **OK**.

In **Assign Mesh Controls**, set the **Element Shape** to **Quad-dominated**, the **Technique** to **Free**, and the **Algorithm** to **Advanced front** > **Use mapped meshing where appropriate**.

The mesh shown in the Fig. 3.2-5 is quite irregular but can be used for homogenization analysis.
However, it can be seen that there is one element (highlighted in the yellow ellipse) is abnormal.
If use this mesh to do the dehomogenization, there will be an error message in the command window (Fig. 3.2-6).

Such a mesh can be repaired as shown in Fig. 3.2-7.

```{figure} /_static/images/sg-2d-custom-any-mesh.png
:align: center

Fig. 3.2-5 Mesh need to be repaired
```

```{figure} /_static/images/sg-2d-custom-any-mesh-error.png
:align: center

Fig. 3.2-6 Error message in dehomogenization
```

```{figure} /_static/images/sg-2d-custom-any-mesh-repair.png
:align: center

Fig. 3.2-7 repair the mesh
```


## Step 6: Homogenization and dehomogenization

Click the **homogenization** button ![](../../../../assets/icons/sc_homo_small.png) then fill the dialog box as shown in the Fig. 3.2-8

```{figure} /_static/images/sg-2d-custom-any-solid-homog-db.png
:align: center

Homogenization.
```

The effective properties is obtained (Fig. 3.2-9).

```{figure} /_static/images/sg-2d-custom-any-solid-homog-output.png
:align: center

Effective properties.
```


Click the **dehomogenization** button ![](../../../../assets/icons/sc_dehomo_small.png) then fill the dialog box as shown in the Fig. 3.2-10

```{figure} /_static/images/sg-2d-custom-any-solid-dehomog-db-cae.png
:align: center

Dehomogenization.
```

The local fields are obtained (Fig. 3.2-11).

```{figure} /_static/images/sg-2d-custom-any-solid-dehomog-visual.png
:align: center

Dehomogenization result: magnitude of displacement.
```
