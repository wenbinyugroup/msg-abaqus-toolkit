# Square Pack Microstructure (2D SG)


### 2.2.1 2D SG preparation

In this example, assume that both fiber and matrix are isotropic materials (Material Fiber: Young’s modulus _E_ \= 379.3 GPa, Poisson’s ratio  = 0.1; Material Matrix: Young’s modulus _E_ = 68.3 GPa, Poisson’s ratio = 0.3). Create Materials in the Property module as shown in Fig. 2.2-1.

Fig. 2.2-1 Material creation

Then click the 2D SG button in the red frame in Fig. 2.2-2 so that the dialog box in Fig. 2.2-3 will pop out. The square pack microstructure SG has width 1.0. The user is allowed to choose the volume fraction or radius of fiber and interphase. If there is no interphase, the text field in the Interface group box is set to the default value 0.0.


Fig. 2.2-2 Create 2D common SG button


Fig. 2.2-3 Create 2D SG dialog box

After setting all the parameters as shown in Fig. 2.2-3, click OK to create the SG (Fig. 2.2-4).


Fig. 2.2-4

### 2.2.2 Homogenization

Click the homogenization button in the red frame of Fig. 2.2-5, a dialog box in Fig. 2.2-6 will pop up. In this example, we choose the 3D solid macro model, then the default file name will be ‘sqrP2_nSG2_3D_S8R.sc’. Click OK and wait for preparing the input file of SwiftComp™ and homogenization. After the computation of SwiftComp™, the effective properties will pop up automatically (Fig. 2.2-7).


Fig. 2.2-5 Homogenization button


Fig. 2.2-6 Homogenization dialog box-use 3D solid model


Fig. 2.2-7 Effective properties of 3D solid model


Fig. 2.2-8 Command line window shows the progress and error messages

### 2.2.3 Dehomogenization

Click the dehomogenization button in the red frame of Fig. 2.2-9, the dehomogenization dialog box in Fig. 2.2-10 will pop out. We can choose the SG from CAE or choose SwiftComp input file ‘sqrP2_nSG2_3D_S8R.sc’, and then specify the required inputs as shown in Fig. 2.2-10.


Fig. 2.2-9 Dehomogenization button


Fig. 2.2-10 Dehomogenization parameters for 3D solid model

Click OK and wait for SwiftComp™ to finish the computation. Switch to the Visualization model, the user is able to view all the field results components. In the odb tree, 2 sections are created, with each section containing the same material properties. The nodal stress SN11 component is shown in Fig. 2.2-11.


Fig. 2.2-11 Dehomogenization results of 3D model
