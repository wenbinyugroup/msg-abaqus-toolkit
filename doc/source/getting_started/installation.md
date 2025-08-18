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

Open a command line window, navigate to the unzipped folder, and run the command `abaqus cae -custom SwiftCompGUI`.


### 3. Full integration

In this way, user can start the GUI and work on analysis anywhere.
Several steps are needed:
1. Let Abaqus locate the package.
    - For Abaqus 2020 and later:
        - Add the path containing `SwiftCompGUI.py` to the variable `plugin_central_dir` in `abaqus_v6.env`.
        - Abaqus 2024 and later uses Python 3.
        - Abaqus 2023 and earlier uses Python 2.
    - For Abaqus 2019 and earlier:
        - Add the path containing `SwiftCompGUI.py` (Python 2) to the `PYTHONPATH` in `abaqus.aev` of Abaqus. This file is usually located at `:<your_abaqus_home_directory>\SMA\site`. Insert the full path just before `:$PYTHONPATH` at the end. Pay attention to the direction of the slash.

2. Add a custom command to Abaqus.
Open file `abaqus.app` in a text editor, which is usually located at `<your_abaqus_home_directory>\SMA\site`.
Append `swiftcomp cae –custom SwiftCompGUI` at the end of the command list.

3. To start the GUI, type `abaqus swiftcomp` in the command prompt.
