# config.py

# 快捷键对应event.state的数值
SHORTCUT_CODE = {"Shift": 0x1, "Control": 0x4, "Command": 0x8, "Alt": 0x20000}

DATA_CONFIG = {
    "app": None,
    "window": None,
    "screen": None,
    "mode": None,
    "csv_len": -1,
    "csv": None,
    "time_lower_limit": 30,
    "time_upper_limit": 40,
    "std_limit": 0.005,
}

SCREEN_CONFIG = {"borderwidth": 5, "relief": "raised"}

MAIN_FRAME_CONFIG = {"borderwidth": 5, "relief": "sunken"}

RAISED_SUBFRAME_CONFIG = {"borderwidth": 1, "relief": "raised"}

FLAT_SUBFRAME_CONFIG = {"borderwidth": 2}

ENTRY_LABEL_CONFIG = {"padding": 2}

PLOT_CONFIG = {
    "MainScatter": {"s": 5, "color": "dimgray"},
    "MainLine": {"linewidth": 1, "color": "#1F77B4"},
}

DEFAULT_DATA_VALUE = {
    # 其他默认值
}
