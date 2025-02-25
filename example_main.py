import os, sys

if getattr(sys, "frozen", False):
    import pyi_splash  # type: ignore


from pathlib import Path
from win32gui import FindWindow, SetForegroundWindow
from src import utils, gui
from src.logger import LOGGER

APP_NAME = "ExampleApp"
APP_VERSION = "1.0"
WORK_PATH = os.path.join(os.getcwd(), APP_NAME)
PARENT_PATH = Path(__file__).parent
ASSETS_PATH = PARENT_PATH / Path(r"src/assets")
LOG = LOGGER(APP_NAME, APP_VERSION)


this_window = FindWindow(None, APP_NAME)
if this_window != 0:
    LOG.warning(
        f"{APP_NAME} is aleady running! Only one instance can be launched at once.\n"
    )
    SetForegroundWindow(this_window)
    sys.exit(0)
if not os.path.exists(WORK_PATH):
    os.mkdir(WORK_PATH)
LOG.on_init()


import atexit

from concurrent.futures import ThreadPoolExecutor
from imgui.integrations.glfw import GlfwRenderer
from threading import Thread
from time import sleep


Icons = gui.Icons
ImGui = gui.imgui
threadpool = ThreadPoolExecutor(max_workers=3)
progress_value = 0
should_exit = False
window = None
status_update_thread = None
dummy_progress_thread = None
dummy_exit_thread = None
app_init_thread = None
task_status_col = None
task_status = ""
busy_icon = ""
CONFIG_PATH = os.path.join(WORK_PATH, "settings.json")
debug_console = utils.read_cfg_item(CONFIG_PATH, "debug_console")
ImRed = [1.0, 0.0, 0.0]
ImGreen = [0.0, 1.0, 0.0]
ImBlue = [0.0, 0.0, 1.0]
ImYellow = [1.0, 1.0, 0.0]

default_cfg = {
    "debug_console": False,
}


def res_path(path: str) -> Path:
    return ASSETS_PATH / Path(path)


def set_task_status(msg="", color=None, timeout=2):
    global task_status, task_status_col
    task_status = msg
    task_status_col = color
    sleep(timeout)
    task_status = ""
    task_status_col = None


def dummy_progress():
    global progress_value

    progress_value = 0

    for i in range(101):
        progress_value = i / 100
        sleep(0.01)
    sleep(1)
    progress_value = 0


def dummy_quit_func():
    global task_status, should_exit

    task_status = "Pretending to be doing something important..."
    dummy_progress()
    for i in range(4):
        task_status = f"{APP_NAME} will automatically exit in {i - 3}"
    should_exit = True


def is_any_thread_alive():
    global status_update_thread
    global app_init_thread
    global dummy_progress_thread

    for thread in (
        status_update_thread,
        dummy_progress_thread,
        app_init_thread
        ):
            return utils.is_thread_active(thread)
    return False


def get_status_widget_color():
    global task_status
    global status_update_thread
    global app_init_thread

    if task_status != "":
        if utils.stringFind(task_status, "error") or utils.stringFind(
            task_status, "failed"
        ):
            return ImRed, "Error"
        else:
            if is_any_thread_alive():
                return ImYellow, "Busy"
    return ImGreen, "Ready"


def animate_icon():
    global busy_icon

    while True:
        sleep(0.1)
        if is_any_thread_alive():
            busy_icon = Icons.hourglass_1
            sleep(0.1)
            busy_icon = Icons.hourglass_2
            sleep(0.1)
            busy_icon = Icons.hourglass_3
            sleep(0.1)
            busy_icon = Icons.hourglass_4
            sleep(0.1)
            busy_icon = Icons.hourglass_5

Thread(target=animate_icon, daemon=True).start()


def check_saved_config():
    """
    Fixes missing config entries.
    """

    saved_config: dict = utils.read_cfg(CONFIG_PATH)
    if len(saved_config) != len(default_cfg):
        try:
            if len(saved_config) < len(default_cfg):
                for key in default_cfg:
                    if key not in saved_config:
                        saved_config.update({key: default_cfg[key]})
                        LOG.debug(f'Added missing config key: "{key}".')
            elif len(saved_config) > len(default_cfg):
                for key in saved_config.copy():
                    if key not in default_cfg:
                        del saved_config[key]
                        LOG.debug(f'Removed stale config key: "{key}".')
            utils.save_cfg(CONFIG_PATH, saved_config)
        except Exception as e:
            LOG.error(e)
    dummy_progress()


def app_init():
    global task_status
    global task_status_col
    global default_cfg

    task_status = f"Initializing {APP_NAME}, please wait..."
    if not os.path.exists(CONFIG_PATH):
        utils.save_cfg(CONFIG_PATH, default_cfg)

    task_status = f"Verifying config..."
    LOG.info("Verifying config...")
    check_saved_config()
    task_status_col = None
    task_status = ""
    LOG.info("Initialization complete.")


app_init_thread = threadpool.submit(app_init)


def run_dummy_progress():
    global dummy_progress_thread

    if dummy_progress_thread and not dummy_progress_thread.done():
        pass
    else:
        dummy_progress_thread = threadpool.submit(dummy_progress)


def run_task_status_update(msg="", color=None, timeout=2):
    global status_update_thread

    if status_update_thread and not status_update_thread.done():
        pass
    else:
        status_update_thread = threadpool.submit(set_task_status, msg, color, timeout)


def run_dummy_exit_func():
    global dummy_exit_thread

    if dummy_exit_thread and not dummy_exit_thread.done():
        pass
    else:
        dummy_exit_thread = threadpool.submit(dummy_quit_func)


def OnDraw():
    global window
    global task_status
    global debug_console

    ImGui.create_context()
    window = gui.new_window(APP_NAME, 400, 400, False)
    impl = GlfwRenderer(window)
    font_scaling_factor = gui.fb_to_window_factor(window)
    io = ImGui.get_io()
    io.fonts.clear()
    io.font_global_scale = 1.0 / font_scaling_factor
    font_config = ImGui.core.FontConfig(merge_mode=True)
    icons_range = ImGui.core.GlyphRanges(
        [
            0xF00C,
            0xF00D,
            0xF01A,
            0xF01B,
            0xF019,
            0xF021,
            0xF055,
            0xF056,
            0xF09B,
            0xF09C,
            0xF250,
            0xF254,
            0,
        ]
    )

    title_font = io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/Rokkitt-Regular.ttf")),
        25 * font_scaling_factor,
    )

    small_font = io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/Rokkitt-Regular.ttf")),
        16.0 * font_scaling_factor,
    )

    main_font = io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/Rokkitt-Regular.ttf")),
        20 * font_scaling_factor,
    )

    io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/fontawesome-webfont.ttf")),
        16 * font_scaling_factor,
        font_config,
        icons_range,
    )

    impl.refresh_font_texture()

    if debug_console:
        LOG.show_console()

    while (
        not gui.glfw.window_should_close(window)
        and not should_exit
    ):
        gui.glfw.poll_events()
        impl.process_inputs()
        ImGui.new_frame()
        win_w, win_h = gui.glfw.get_window_size(window)
        ImGui.set_next_window_size(win_w, win_h)
        ImGui.set_next_window_position(0, 0)
        ImGui.push_style_color(ImGui.COLOR_FRAME_BACKGROUND, 0.1, 0.1, 0.1)
        ImGui.push_style_color(ImGui.COLOR_FRAME_BACKGROUND_ACTIVE, 0.3, 0.3, 0.3)
        ImGui.push_style_color(ImGui.COLOR_FRAME_BACKGROUND_HOVERED, 0.5, 0.5, 0.5)
        ImGui.push_style_color(ImGui.COLOR_TAB, 0.097, 0.097, 0.097)
        ImGui.push_style_color(ImGui.COLOR_TAB_ACTIVE, 0.075, 0.075, 0.075)
        ImGui.push_style_color(ImGui.COLOR_TAB_HOVERED, 0.085, 0.085, 0.085)
        ImGui.push_style_color(ImGui.COLOR_HEADER, 0.1, 0.1, 0.1)
        ImGui.push_style_color(ImGui.COLOR_HEADER_ACTIVE, 0.3, 0.3, 0.3)
        ImGui.push_style_color(ImGui.COLOR_HEADER_HOVERED, 0.5, 0.5, 0.5)
        ImGui.push_style_color(ImGui.COLOR_BUTTON, 0.075, 0.075, 0.075)
        ImGui.push_style_color(ImGui.COLOR_BUTTON_ACTIVE, 0.085, 0.085, 0.085)
        ImGui.push_style_color(ImGui.COLOR_BUTTON_HOVERED, 0.1, 0.1, 0.1)
        ImGui.push_style_var(ImGui.STYLE_CHILD_ROUNDING, 5)
        ImGui.push_style_var(ImGui.STYLE_FRAME_ROUNDING, 5)
        ImGui.push_style_var(ImGui.STYLE_ITEM_SPACING, (5, 5))
        ImGui.push_style_var(ImGui.STYLE_ITEM_INNER_SPACING, (5, 5))
        ImGui.push_style_var(ImGui.STYLE_FRAME_PADDING, (5, 5))
        ImGui.push_font(main_font)
        ImGui.begin(
            "Main Window",
            flags=ImGui.WINDOW_NO_TITLE_BAR
            | ImGui.WINDOW_NO_RESIZE
            | ImGui.WINDOW_NO_MOVE,
        )
        with ImGui.begin_child("##YLP", 0, 300):
            if app_init_thread and app_init_thread.done():
                ImGui.dummy(1, 10)
                with ImGui.font(title_font):
                    ImGui.text("Example Title Text")
                with ImGui.font(small_font):
                    ImGui.bullet_text("Example small text")

                if ImGui.button("Show Dummy Progress"):
                    run_dummy_progress()

                if ImGui.button("Set Task Status"):
                    run_task_status_update("Pretending to be working...", None, 5)
                
                ImGui.text("Example Busy Button:")
                ImGui.same_line(spacing=10)
                if not is_any_thread_alive():
                    if ImGui.button("Click Me!"):
                        run_dummy_progress()
                        run_task_status_update("Please Wait...", None, 2)
                else:
                    gui.busy_button(busy_icon)

                console_clicked, debug_console = ImGui.checkbox(f"{debug_console and "Disable" or "Enable"} Debug Console", debug_console)
                if console_clicked:
                    utils.save_cfg_item(CONFIG_PATH, "debug_console", debug_console)
                    if debug_console:
                        LOG.show_console()
                    else:
                        LOG.hide_console()
                
                if ImGui.button("Run a dummy task and quit"):
                    run_dummy_exit_func()

        ImGui.spacing()
        with ImGui.begin_child("##feedback", 0, 40):
            status_col, _ = get_status_widget_color()
            ImGui.text_colored(
                f"{status_col == ImGreen and "-" or busy_icon}", status_col[0], status_col[1], status_col[2], 0.8
            )
            ImGui.push_text_wrap_pos(win_w - 15)
            with ImGui.font(small_font):
                ImGui.same_line()
                gui.status_text(task_status, task_status_col)
            ImGui.pop_text_wrap_pos()
            if progress_value > 0:
                ImGui.progress_bar(progress_value, (380, 5))

        gui.clickable_icon(
            Icons.GitHub,
            small_font,
            "Click to visit this template's GitHub repository",
            utils.visit_url,
            "https://github.com/xesdoog",
        )

        ImGui.pop_font()
        ImGui.pop_style_var(5)
        ImGui.pop_style_color(12)
        ImGui.end()

        gui.gl.glClearColor(1.0, 1.0, 1.0, 1)
        gui.gl.glClear(gui.gl.GL_COLOR_BUFFER_BIT)
        ImGui.render()
        impl.render(ImGui.get_draw_data())
        gui.glfw.swap_buffers(window)

    if status_col != ImGreen:
        threadpool.shutdown()
    impl.shutdown()
    gui.glfw.terminate()


@atexit.register
def OnExit():
    LOG.info(f"Closing {APP_NAME}...\n\nFarewell!")


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        pyi_splash.close()
    OnDraw()
