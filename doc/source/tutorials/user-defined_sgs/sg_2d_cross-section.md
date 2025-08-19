# Cross-section with arbitrary shape (2D SG)


## Laminate in the GUI


As shown in the figure, once the direction of layup is decided, the baseline is defined as the starting edge of the layup and the opposite boundary is the ending edge.

## Dialog box



A layup area is the whole segment face before partitioning into different layers and the baseline is shown as in the figure above. These two objects are required for all type of laminates. The next two inputs, the opposite boundary and number of sampling points, are required only when the baseline and opposite boundary are not straight lines. The sampling points are used to replicate those curved edges in Abaqus sketch module. The more sampling points, the more accurate the geometry will be. But large number of points will greatly reduce the speed of building the part. The last two dropdown lists are for users to choose composite layups.



If a layup is assigned mistakenly, user can use this function to delete the wrong assignment. The baseline is the same as the one when assigning the layup. This function will help user to delete section assignments, sets and erase lines in the partition sketch, so that user can re-assign the area without worrying about duplicate or conflicting sets or section assignments.

## Prerequisite

Before using the “Assign Layups” function, user needs to provide the geometry of the cross-section, materials and composite sections.

## Example

### Step 1: Set work directory

Menu > File > Set Work Directory.... Select the directory where you want to put all relative files, .cae, .inp, .sc, etc.

### Step 2: Create materials


### Step 3: Create composite sections

User can create layups using functions described in section 3.3, or using Abaqus’s own functions by hand, which is described below.

Note here that the thickness of each layer should be actual thickness instead of relative thickness.

### Step 4: Draw the general shape

According to the coordinates convention in SwiftComp, the X-axis is along the beam reference line and the cross-section is in the Y-Z plane. Thus we need to first set our workplane to Y-Z plane. In the SwiftComp Toolset, click the icon button , set the ‘New Part Name’ and select ‘2D’ as the ‘SG Dimension’. Click ‘OK’.



In the toolbox of the Part module, click ‘Create Shell: Planar’ 

Click ‘Done’, then the part will be generated.

Next we need to divide this part into four segments. Click ‘Partition Face: Sketch’ 

### Step 5: Assign layups

First we will assign the layup for the segment on the top. Click ‘Assign Layups’ 


Next, assign the layup for the segment on the left. Pick the area 1, baseline 2, opposite boundary 3, give 20 sampling points and select section ‘Layup-1’. Click ‘OK’.



We can do the same for the rest two segments, except that we use ‘Layup-3’ for the right segment.


User may notice that the color for some layers changed after assigning the layup for the right segment. This is because we have some new sections created in ‘Layup-3’ and the order of the section list changed, so that the color map also changed. But no need to worry here, since the section assignment are still right, the only difference is the color.

### Step 6: Delete layups

If users find that some layup is assigned mistakenly, it can be deleted and re-assigned. For instance, we want to re-assign the layup for the left segment. Click ‘Erase Layups’ . In the dialog box pick the same baseline used for assigning the layup. Click ‘OK’.


Once done, user can assign a new layup for the empty segment. Here we assign the ‘Layup-2’.


### Step 7: Assign local coordinates

Module > Property > Assign Material Orientation 


Once done, the local orientations should look like the same as the figure shown below.


### Step 8: Create assembly

Module > Assembly > Create Instance 

### Step 9: Mesh

First choose ‘Part’ as the _Object_. Then click Module > Mesh > Seed Part 

Click ‘Mesh Part’ 

### Step 10: Write Abaqus input file

Module > Job > Create Job 

### Step 11: Homogenization

Click ‘Homogenization’ button 

After a certain time, depending on the model, SwiftComp will finish computing the cross-sectional properties and show the results in the notepad. If everything is fine, close the notepad and the process will end.


If error messages pop out, or an empty notepad file appears, please refer to the command line window for more information.
