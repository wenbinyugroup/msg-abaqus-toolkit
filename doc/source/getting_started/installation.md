# Installation

To get started to use Abaqus-SwiftComp GUI on your local machine, you just need to simply unzip the distribution package into a folder of your own choice.

## Start the GUI

The key to running the GUI is the following command:
```bash
abaqus cae -custom SwiftCompGUI.py
```

There are three ways to trigger this command:

### 1. Shortcut

In the unzipped folder, double click the short cut `Abaqus-SwiftComp GUI` to launch it.


### 2. Command line

Open a command line window, navigate to the unzipped folder, and run the command `abaqus cae -custom SwiftCompGUI.py`.


### 3. Full integration

In this way, user can start the GUI and work on analysis anywhere.
Several steps are needed:
1. Add the folder's root path (containing the file `SwiftCompGUI.py`) to the `PYTHONPATH` of Abaqus.
This constant is in the file `abaqus.aev`, which is usually located at `abaqus_home_directory\SMA\site`.
Insert the full path just before `.:$PYTHONPATH` at the end.
Pay attention to the direction of the slash. Save;
2. Add a custom command to Abaqus.
Open file `abaqus.app` in a text editor, which is usually located at `abaqus_home_directory\SMA\site`.
Append `swiftcomp cae –custom SwiftCompGUI` at the end of the command list. Save;
3. To start the GUI, type `abaqus swiftcomp` in the command prompt.
