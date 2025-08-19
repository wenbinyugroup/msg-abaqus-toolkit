# Spherical Inclusion Microstructure (3D SG)


## 3D SG preparation

In this example, assume that both fiber and matrix are isotropic materials (Material Fiber: Young’s modulus _E_ \= 379.3 GPa, Poisson’s ratio  = 0.1; Material Matrix: Young’s modulus _E_ = 68.3 GPa, Poisson’s ratio = 0.3; Material Interphase: _E_<sub>1</sub>\=117.0 GPa, _E_<sub>2</sub>\=_E_<sub>3</sub>\=8.54 GPa, <sub>13</sub>\=0.278, <sub>23</sub>\=0.5, _G_<sub>12</sub>\=_G_<sub>13</sub>\=3.9 GPa, _G_<sub>23</sub>\=2.83 GPa).

Create Materials in the Property module as shown in Fig. 2.3-1.


Fig. 2.3-1 Material creation

Then click the 3D common SG button in the red frame in Fig. 2.3-2 so that the dialog box in the Fig. 2.2-3 will pop out. This 3D SG has length 1.0 in every dimension. The user is allowed to choose the volume fraction or radius of inclusion and interphase. If there is no interphase, the text field in the Interface group box is set to be the default value 0.0.


Fig. 2.3-2 Create 3D common SG button


Fig. 2.3-3 Create 3D SG dialog box

After setting all the parameters as shown in Fig. 2.3-3, click OK to create the SG (Fig. 2.3-4).


Fig. 2.3-4 The created 3D SG

## Homogenization

Click the homogenization button, a dialog box in Fig. 2.3-5 will pop up. In this example, we choose the 3D solid macro model, then the default file name will be ‘inclusionP3_nSG3_3D_C3D4.sc’. Click OK and wait for preparing the input file of SwiftComp™ and homogenization. After the computation of SwiftComp™, the effective properties will pop up automatically (Fig. 2.3-6).


Fig. 2.3-5 Homogenization dialog box-use 3D solid model


Fig. 2.3-6 Effective properties of 3D solid model

## Dehomogenization

Click the dehomogenization button, the dehomogenization dialog box in Fig.2.3-7 will pop out. We can choose the SG from CAE or choose SwiftComp input file ‘inclusionP3_nSG3_3D_C3D4.sc’, and then specify the required inputs as shown in Fig. 2.3-8.


Fig. 2.3-8 Dehomogenization parameters for 3D solid model

Click OK and wait for SwiftComp™ to finish the computation. Switch to the Visualization model, the user is able to view all the field results. In the odb tree, 3 sections are created, with each section containing the same material properties.


Fig. 2.2-10 Dehomogenization results of 3D model
