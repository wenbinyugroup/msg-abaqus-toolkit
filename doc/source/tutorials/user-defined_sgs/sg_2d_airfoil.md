# Cross-section with Airfoil Shape (2D SG)


Cross-sections with airfoil shape usually contain several parts, like surfaces, webs and fillings, and the surface part has several segments and each segment has dozens or hundreds of layers, which makes it very difficult to build the model by hand as what we have shown in the previous section. The SwiftComp GUI will help user to draw the cross-section and prepare the SwiftComp input file automatically from airfoil data. Thus the main topic of this section is the preparation of data files. Once those files are ready, the whole process will be done by one click. A sample set of files are also given in the folder airfoil which the users can use as template to adapt for their own cross-sections.

### 3.5.2 Input data files

User needs to provide four files: control file, shape file, material file and layup file, which are all XML files. All files should be placed in the same folder. Now we will describe each file in details.

1. Control file

This is the main input that will be used in the SwiftComp GUI.

&lt;project type="airfoil"&gt;

&lt;shapes&gt;**shape_filename**&lt;/shapes&gt;

&lt;materials&gt;**material_filename**&lt;/materials&gt;

&lt;layups&gt;**layup_filename**&lt;/layups&gt;

&lt;pitch_axis_yz&gt;**0.4750054 0.0**&lt;/pitch_axis_yz&gt;

&lt;twisted_angle&gt;**0.0**&lt;/twisted_angle&gt;

&lt;chord_length&gt;**1.89999874**&lt;/chord_length&gt;

&lt;flip&gt;**No**&lt;/flip&gt;

&lt;/project&gt;

‘&lt;project&gt;&lt;/project&gt;’ is the root element, which has an attribute ‘type=“airfoil”’. Since the ‘Read File’ function mainly deals with cross-sections with airfoil shape, this arribute can be omitted for the current version. There are seven sub-elements below ‘&lt;project&gt;&lt;/project&gt;’. The first three sub-elements indicate the names of the other three data files, with file extensions “.xml” being appended or omitted. The next three lines tell the general shape parameter for the airfoil. Element ‘&lt;pitch_axis_yz&gt;&lt;/pitch_axis_yz&gt;’ indicates the normalized location of the pitch axis in the Y-Z plane, which is the cross-section plane. The two numbers are separated by spaces. Element ‘&lt;twisted_angle&gt;&lt;/twisted_angle&gt;’ contains the angle in degree between the actual chord line and the horizontal line. In the figure below, the ‘angle of attack’ is what we mean by ‘twisted angle’ here. Element ‘&lt;chord_length&gt;&lt;/chord_length&gt;’ stores the actual length of the chord line. The last element ‘&lt;flip&gt;&lt;/flip&gt;’ is used to indicate whether user want to switch the orientation of the airfoil. By default, the leading edge is on the left. See the figure below for a sketch of a typical cross-section of airfoil shape.


1. Shape file

This file stores the shape data of the surfaces, webs and fillings, including the geometry information like coordinates of points and the segment division information like the dividing point number and the layup id that will be assigned to this segment. The structure is shown below.



&lt;?xml version = "1.0" encoding = "UTF-8"?&gt;

&lt;assembly type = "airfoil"&gt;

&lt;part structure = "surface"&gt;

&lt;baseline type = "spline" format = "lednicer"&gt;

&lt;lps&gt;

**0 0**

**0.00035937 0.0029595**

**0.00162747 0.00696192**

**... ...**

**9.97E-01 1.33E-04**

**1.00E+00 0.00E+00**

&lt;/lps&gt;

&lt;hps&gt;

**0 0**

**0.00062671 -0.00294872**

**0.0030035 -0.00629665**

**... ...**

**0.9970425 -0.00036119**

**1 0**

&lt;/hps&gt;

&lt;/baseline&gt;

&lt;layup side = "left"&gt;

&lt;lps&gt;

**1 3 1**

**...**

&lt;/lps&gt;

&lt;hps&gt;

**1 3 1**

**...**

&lt;/hps&gt;

&lt;/layup&gt;

&lt;/part&gt;

&lt;part structure = "web"&gt;

&lt;baseline&gt;

&lt;y_z_angle&gt;**0.15 0.0 90.0**&lt;/y_z_angle&gt;

...

&lt;/baseline&gt;

&lt;layup side = "both"&gt;

**5**

...

&lt;/layup&gt;

&lt;/part&gt;

&lt;part structure = "filling"&gt;

&lt;region material = "6"&gt;**3**&lt;/region&gt;

...

&lt;/part&gt;

&lt;/assembly&gt;

There is a root element ‘&lt;assembly&gt;&lt;/assembly&gt;’, whose attribute ‘type’ can be omitted for the current version. The child element is ‘&lt;part&gt;&lt;/part&gt;’ and the attribute ‘structure’ for each part tells what the part is, surface, web or filling. For laminate-like part, surface and web, there are two sub-elements, ‘&lt;baseline&gt;&lt;/baseline&gt;’ and ‘&lt;layup&gt;&lt;/layup&gt;’.

The ‘baseline’ element of the ‘surface’ part contains two sub-elements, ‘&lt;lps&gt;&lt;/lps&gt;’ and ‘&lt;hps&gt;&lt;/hps&gt;’, which store the raw data of the airfoil low pressure surface and high pressure surface, respectively. Two attributes, ‘type’ and ‘format’ may be used in the future version and can be omitted here. The arrangement of data for both ‘lps’ and ‘hps’ is from (0, 0) to (1, 0), which is from the leading edge to the trailing edge. The ‘baseline’ element for the ‘web’ part contains any number of sub-elements ‘&lt;y_z_angle&gt;&lt;/y_z_angle&gt;’, each of whom stands for a web. Here a web is represented by a straight line. The first two numbers are the normalized position of the baseline on the chord line and the last number is the angle in degree measured from the chord line segment near the leading edge to the upper part of the web baseline.

The ‘layup’ element has an attribute ‘side’, which can have the value ‘left’, ‘right’ or ‘both’. The ‘side’ is defined according to the direction of the surface baseline, which starts from the trailing edge, goes along the low pressure surface baseline to the leading edge and back to the trailing edge along high pressure surface baseline. So basically, if the ‘side’ is ‘left’, then the plies are laid towards the inside of the airfoil. Thus if the surface baseline is the outmost profile and the leading edge is on the left, then the ‘side’ should be ‘left’. The value ‘both’ means doing the layup on both sides of the baseline, but will not double the layup. Or more precisely, this means that the baseline is at the middle of the layup. For the current version, this case can only handle symmetric layup. Otherwise, user needs to translate the baseline to one side and change some values in the file accordingly. The ‘layup’ element for the ‘surface’ part contains two sub-elements ‘&lt;lps&gt;&lt;/lps&gt;’ and ‘&lt;hps&gt;&lt;/hps&gt;’. In each of them, there are several lines of data and each line represents a segment and has three numbers. The first two numbers are the starting and ending points for the segment and the last one is the layup id that will be defined in the layup file. The first number of the first line must be 1 and the second number of the last line has to be the total number of points for low pressure surface or high pressure surface. The ‘layup’ element for ‘web’ part is much simpler. Each line only contains the layup id for the web.

For the ‘filling’ part, such as foam, has only one type of sub-element, ‘&lt;region&gt;&lt;/region&gt;’. The number stored between the two tags is region id, which is defined as follows. If there are two webs, then the inner space of the airfoil is divided into three regions. Starting from the leading edge, those regions are labeled as ‘1’, ‘2’ and ‘3’. The attribute ‘material’ stores the material id, which is defined in the material file. Here we make the assumption that the materials used for the fillings are homogeneous, could not generally anisotropic, with material properties given in the global coordinates.

1. Material file

Please see section 3.3.2

1. Layup file

Please see section 3.3.2

### 3.5.3 Create cross-section model in Abaqus from input files

**Step 1: Set working directory**

The working directory should contain those data files.

**Step 2: Read input files**

Click ‘Read File’ 

Once done, user should see a meshed airfoil cross-section with different colors representing different layer types, as shown in the figure below.


**Step 3: Make some changes (optional)**

At this stage, user can change material properties or meshes. Following these modifications, user need to re-write the Abaqus input file from the job.

User can also do the creation in command line without entering Abaqus/CAE. First, user needs to enter the directory where the script ‘drawCS.py’ is located. Then type:

abaqus cae noGui=drawCS.py -- _project_name_ _control_file_

where ‘control_file’ is the complete file name including path and extension. Press ‘Enter’. Once done, all those related files can be found in the same place where the control file is.

### 3.5.4 Homogenization

Click ‘Homogenization’ button 

After a certain time, depending on the model, SwiftComp will finish computing the cross-sectional properties and show the results in the notepad. If everything is fine, close the notepad and the process will end.


If error messages pop out, or an empty notepad appears, please refer to the command line window for more information.
