# PyImGui-GLFW App Template

A template repository for creating Python apps with PyImGui and GLFW3.

>[!NOTE]
> The `.pyi` file is only there for PyLance. If you don't need it, remove it.

## Template Structure

### Folders

- `src/assets/dll`: Contains `glfw3.dll` and `msvcp110.dll`, essential for the GUI to work. PyInstaller tends to fail to find and append them on its own so having them here and explicitly adding them when building saves you the headache.
- `src/assets/fonts`: Contains 2 free fonts: Google's [Rokkitt](https://fonts.google.com/specimen/Rokkitt) Regular and the free version of [FontAwesome v4.7](https://fontawesome.com/v4/).
- `src/assets/img`: Contains example icon and splash images.

### Files

- `src/gui.py`: Contains GUI functions and custom ImGui wrappers.
- `src/logger.py`: Contains a [custom logger class](https://gist.github.com/xesdoog/73dd7aca768d2bf30099bdd3311b0e3d).
- `src/utils.py`: Contains general utilities.
- `example_main.py`: A simple demo app.
