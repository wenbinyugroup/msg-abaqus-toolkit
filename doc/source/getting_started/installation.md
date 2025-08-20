(start-install)=
# Installation

To get started to use Abaqus-SwiftComp GUI on your local machine, you just need to unzip the distribution package into a folder of your own choice.
For convenience, we will refer to this folder as `SC_ABQ_GUI_HOME=<your_path_to>/msg-abaqus-toolkit` in the following.

The starting file `SwiftCompGUI` (both script and shortcut) is located in the `{SC_ABQ_GUI_HOME}/scripts` folder, with two versions for Python 2 and Python 3.
Choose the one compatible with your Abaqus version.
According to Abaqus documentation,
- Abaqus 2024 and later uses Python 3.
  - `{SC_ABQ_GUI_HOME}/scripts/py3`
  - This version is tested based on Abaqus 2025.
- Abaqus 2023 and earlier uses Python 2.
  - `{SC_ABQ_GUI_HOME}/scripts/py2`
  - This version is tested based on Abaqus 2016 (6.16).

## Start the GUI

There are three ways to trigger this command:

### 1. Shortcut

In `{SC_ABQ_GUI_HOME}/scripts/{py2|py3}`, double click the shortcut `Abaqus-SwiftComp GUI` to launch it.


### 2. Command line

Open a command line window, navigate to `{SC_ABQ_GUI_HOME}/scripts/{py2|py3}`, and run the command
```bash
abaqus cae -custom SwiftCompGUI
```

### 3. Full integration

In this way, user can start the GUI and work anywhere.
Several steps are needed:
1. Let Abaqus locate the package.
    - For Abaqus 2020 and later:
        - Add the path `{SC_ABQ_GUI_HOME}/scripts/{py2|py3}` to the variable `plugin_central_dir` in `abaqus_v6.env`, e.g.,
          ```python
          plugin_central_dir = "{SC_ABQ_GUI_HOME}/scripts/{py2|py3};<other_directories>"
          ```
    - For Abaqus 2019 and earlier:
        - Add the path `{SC_ABQ_GUI_HOME}/scripts/py2` to the `PYTHONPATH` in `abaqus.aev` of Abaqus. This file is usually located at `:<your_abaqus_home_directory>\SMA\site`. Insert the full path just before `:$PYTHONPATH` at the end. Pay attention to the direction of the slash.

2. Add a custom command to Abaqus.
Open file `abaqus.app` in a text editor, which is usually located at `<your_abaqus_home_directory>\SMA\site`.
   Append
   ```
   swiftcomp cae –custom SwiftCompGUI
   ```
   at the end of the command list.

3. To start the GUI, type `abaqus swiftcomp` in the command prompt.



Once the GUI is launched, you should see the SwiftComp toolbar in the main window.

```{figure} /_static/images/toolbar.png
:align: center

SwiftComp toolbar.
```


```{note}
If the toolbar does not show up, please go to the menu **View** > **Toolbars** > **SwiftComp** to activate it.
```
