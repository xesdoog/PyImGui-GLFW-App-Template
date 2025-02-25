from pathlib import Path
from PIL import Image
from pywintypes import error as pywinErr
from win32gui import GetOpenFileNameW
import glfw
import imgui
import numpy as np
import OpenGL.GL as gl
import os
import win32con

from contextlib import contextmanager
from cv2 import cvtColor, imread, COLOR_BGR2RGBA, IMREAD_UNCHANGED
from win11toast import notify


PARENT_PATH = Path(__file__).parent
ASSETS_PATH = PARENT_PATH / Path(r"assets")


class Icons:
    """
    FontAwesome v4.7 unicode reference: https://fontawesome.com/v4/cheatsheet/
    """

    Checkmark = "\uf00c"
    Close = "\uf00d"
    Down = "\uf01a"
    Up = "\uf01b"
    Download = "\uf019"
    Refresh = "\uf021"
    Plus = "\uf055"
    Minus = "\uf056"
    GitHub = "\uf09b"
    hourglass_1 = "\uf254"
    hourglass_2 = "\uf251"
    hourglass_3 = "\uf252"
    hourglass_4 = "\uf253"
    hourglass_5 = "\uf250"


def res_path(path: str):
    return ASSETS_PATH / Path(path)


def start_file_dialog(extension: str, multiselect: bool) -> list | str:
    """
    Call this function with the extension(s) you want.

    - Only one PDF file example: `start_file_dialog(\"PDF\\0*.pdf;\\0\", False)`

        -> returns a single file path string.

    - Any file type with multiselect example: `start_file_dialog(\"All Files\\0*.*;\\0\", True)`

        -> Returns a list of file paths.
    """

    try:
        fnames = []
        customfilter = "All Files\0*.*\0"
        fname, customfilter, _ = GetOpenFileNameW(
            InitialDir=os.getcwd(),
            Flags=multiselect
            and win32con.OFN_EXPLORER | win32con.OFN_ALLOWMULTISELECT
            or win32con.OFN_EXPLORER,
            DefExt=None,
            Title="Select DLL",
            File="",
            MaxFile=65535,
            Filter=extension,
            CustomFilter=customfilter,
            FilterIndex=0,
        )

        if str(fname).find("\x00"):
            split_n = str(fname).split("\x00")
            fnames.append(split_n)

        if len(fnames[0]) > 1:
            filePath_lst = []
            parent_path = fnames[0][0]
            for i in range(1, len(fnames[0])):
                filePaths = os.path.join(parent_path, fnames[0][i])
                filePath_lst.append(filePaths)

            final_list = filePath_lst

        else:
            final_list = fnames[0][0]

        return final_list

    except pywinErr:
        return None


def draw_image(path: str):
    """
    Returns a texture bound to GLFW that can be drawn in ImGui.
    """
    try:
        img = imread(path, IMREAD_UNCHANGED)
        if img is None:
            print("Error loading image.")
            return 0, 0, 0

        img = cvtColor(img, COLOR_BGR2RGBA)
        h, w = img.shape[:2]

        img_data = np.ascontiguousarray(img, dtype=np.uint8)

        texture = gl.glGenTextures(1)
        if texture == 0:
            return 0, 0, 0

        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            w,
            h,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            img_data,
        )

        error = gl.glGetError()
        if error != gl.GL_NO_ERROR:
            print(f"OpenGL error: {error}")
            return 0, 0, 0

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return texture, w, h
    except Exception as e:
        print(f"Unhandled exception: {e}")
        return 0, 0, 0


def fb_to_window_factor(window):
    """
    Frame buffer to window factor.
    """

    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)

    return max(float(fb_w) / win_w, float(fb_h) / win_h)


def new_window(
    title: str, width: int, height: int, resizable: bool):
    """
    Draws a window and binds and icon to it using GLFW.

    You can modify it to also create custom cursors and return them as objects callable in `glfw.set_cursor()`
    """

    if not glfw.init():
        raise Exception("Failed to initialize OpenGL context!")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.RESIZABLE, gl.GL_TRUE if resizable else gl.GL_FALSE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    monitor = glfw.get_primary_monitor()
    vidMode = glfw.get_video_mode(monitor)
    pos_x = vidMode.size.width
    pos_y = vidMode.size.height

    # Example pointing hand cursor '👆'
    # hand_cursor: object = glfw.create_standard_cursor(glfw.POINTING_HAND_CURSOR)

    # Example iBeam cursor '|'
    # ibeam_cursor : object = glfw.create_standard_cursor(glfw.IBEAM_CURSOR)

    window = glfw.create_window(int(width), int(height), title, None, None)
    icon = Image.open(res_path("img/icon.ico"))
    icon = icon.convert("RGBA")
    icon_data = np.array(icon, dtype=np.uint8)
    icon_struct = [icon.width, icon.height, icon_data]

    glfw.set_window_pos(window, int(pos_x / 2 - width / 2), int(pos_y / 2 - height / 2))
    glfw.set_window_icon(window, 1, icon_struct)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        raise Exception("Failed to initialize window!")

    return window


def set_window_size(window: object, width: int, height: int):
    return glfw.set_window_size(window, width, height)


def set_cursor(window: object, cursor: object):
    if imgui.is_item_hovered():
        glfw.set_cursor(window, cursor)


def reset_cursor(window: object):
    if not imgui.is_any_item_hovered():
        glfw.set_cursor(window, None)


def colored_button(
    label: str, color: list, hovered_color: list, active_color: list
) -> bool:
    """
    Creates an ImGui colored button
    """
    imgui.push_style_color(imgui.COLOR_BUTTON, color[0], color[1], color[2])
    imgui.push_style_color(
        imgui.COLOR_BUTTON_ACTIVE, hovered_color[0], hovered_color[1], hovered_color[2]
    )
    imgui.push_style_color(
        imgui.COLOR_BUTTON_HOVERED, active_color[0], active_color[1], active_color[2]
    )
    retbool = imgui.button(label)
    imgui.pop_style_color(3)
    return retbool


def busy_button(icon, label=None):
    """
    Creates a busy button that can be used to replace a functional button when its callback is ongoing.

    You can animate this button's icon by creating a thread that changes the icon to a

    *similar-but-slightly* different one. See `hourglass_1` to `hourglass_5` in the `Icons` class above
    
    for a simple example. A dummy thread is also available in `example_main.py`
    """

    button_label = f"{icon}  {label}" if label else f" {icon} "
    colored_button(
        button_label,
        [0.501, 0.501, 0.501],
        [0.501, 0.501, 0.501],
        [0.501, 0.501, 0.501],
    )


@contextmanager
def begin_disabled(cond: bool):
    """
    PyImGui is missing a lot of useful ImGui bindings. This **tries** to mimic

    `ImGui::BeginDisabled() ... ImGui::EndDisabled()` to a certain extent.
    """

    if cond:
        imgui.push_style_var(imgui.STYLE_ALPHA, 0.5)
        imgui.begin_group()
    try:
        yield
    finally:
        if cond:
            imgui.end_group()
            imgui.pop_style_var()


def disabled_widget(cond: bool, callback, *args):
    """
    Wrapper to handle ImGui widgets that return multiple values (checkboxes, sliders, combos, etc...).
    """

    with begin_disabled(cond):
        result = callback(*args)
        if cond:
            if isinstance(result, tuple):
                return (False, result[1])
            return False
        return result


def status_text(text="", color=None):
    if color:
        imgui.text_colored(text, color[0], color[1], color[2], 1)
    else:
        imgui.text(text)


def tooltip(text="", font=None, alpha=0.75):
    """
    Draws a tooltip when the widget called before this function is hovered.

    - Example:
        ```
        imgui.button("I'm A Button")
        tooltip("Wow! Such button!")
        ```
    """
    if imgui.is_item_hovered():
        imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 10)
        imgui.set_next_window_bg_alpha(alpha)
        with imgui.begin_tooltip():
            imgui.push_text_wrap_pos(imgui.get_font_size() * 15)
            if font:
                with imgui.font(font):
                    imgui.text(text)
            else:
                imgui.text(text)
            imgui.pop_text_wrap_pos()
        imgui.pop_style_var()


def help_marker(text="", font=None, padding=10, alpha=0.75):
    """
    Draws a helpmarker symbol '(?)' in front of the widget called before this function

    then draws a tooltip when the helpmarker symbol is hovered.
    """

    imgui.same_line(spacing=padding)
    imgui.text_disabled("(?)")
    tooltip(text, font, alpha)


def toast(message="", callback=None):
    """
    Triggers a Windows 10/11-style toast notification.
    """

    return notify(
        "ExampleApp",
        message,
        icon=str(res_path("img/icon.ico")),
        on_click=callback,
    )


def message_box(title, text="", font=None, context=0, on_true=None, *args):
    """
    Draws a message box.

    Param context: int
        - 0: Normal message box with "OK" button.
        - 1: Confirm/Cancel message box with "Yes"/"No" buttons. The "Yes" button can trigger a callback if one is given.
    """

    # Adjust window sizes as you see fit.
    imgui.set_next_window_size(240, 0)
    with imgui.begin_popup_modal(
        title=title,
        flags=imgui.WINDOW_NO_TITLE_BAR
        | imgui.WINDOW_NO_COLLAPSE
        | imgui.WINDOW_ALWAYS_AUTO_RESIZE
        | imgui.WINDOW_NO_MOVE,
    ) as msgbox:
        if msgbox.opened:
            imgui.dummy(1, 5)
            imgui.push_text_wrap_pos(235)
            if font:
                with imgui.font(font):
                    imgui.text(text)
            else:
                imgui.text(text)
            imgui.pop_text_wrap_pos()
            imgui.dummy(1, 10)
            if context == 0:
                imgui.dummy(75, 1)
                imgui.same_line()
                if imgui.button("OK", 60, 30):
                    imgui.close_current_popup()
            elif context == 1:
                if imgui.button("Yes", 60, 30):
                    on_true(*args)
                    imgui.close_current_popup()
                imgui.same_line(spacing=105)
                if imgui.button("No", 60, 30):
                    imgui.close_current_popup()


def separator_text(text, padding=10):
    """
    PyImGui is missing a lot of useful ImGui bindings. This tries to mimic `ImGui::SeparatorText()`
    """

    cursor_x, cursor_y = imgui.get_cursor_screen_pos()
    text_width, _ = imgui.calc_text_size(text)
    region_width = imgui.get_content_region_available()[0]
    line_width = (region_width - text_width) / 2 - padding

    draw_list = imgui.get_window_draw_list()
    color = 0xFFFFFFEE

    if line_width > 0:
        draw_list.add_line(
            cursor_x,
            (cursor_y + imgui.get_text_line_height() / 2),
            (cursor_x + padding),
            (cursor_y + imgui.get_text_line_height() / 2),
            color,
            1.6,
        )
        draw_list.add_line(
            (cursor_x + text_width + padding * 2.5),
            (cursor_y + imgui.get_text_line_height() / 2),
            (cursor_x + region_width),
            (cursor_y + imgui.get_text_line_height() / 2),
            color,
            1.6,
        )

    imgui.set_cursor_pos_x(cursor_x + padding)
    imgui.text(text)
    imgui.set_cursor_pos_y(cursor_y - (imgui.get_text_line_height() / 3))


def image_rounded(texture_id, diameter, uv_a=(0, 0), uv_b=(1, 1)):
    """
    Similar to ImGui::Image() but this draws a rounded image.
    """

    draw_list = imgui.get_window_draw_list()
    p_min = imgui.get_cursor_screen_pos()
    p_max = (p_min.x + diameter, p_min.y + diameter)
    draw_list.add_image_rounded(
        texture_id, (p_min.x, p_min.y), p_max, uv_a, uv_b, 0xFFFFFFFF, diameter * 0.5
    )
    imgui.dummy(diameter, diameter)


def clickable_icon(icon, font, tooltip_text, callback, *args):
    """
    Draws a clickable widget.
    """

    imgui.text(icon)
    tooltip(tooltip_text, font)
    if imgui.is_item_hovered() and imgui.is_item_clicked(0):
        callback(*args)
