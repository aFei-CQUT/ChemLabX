# app.py

# 导入标准库结果
import logging
import traceback
import sys
import os

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_script_path))
sys.path.insert(0, project_root)

# 导入外部库
import ttkbootstrap as ttk
from tkinter import PhotoImage

# 导入屏幕类
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.filteration_screen import Filteration_Screen
from gui.screens.heat_transfer_screen import Heat_Transfer_Screen
from gui.screens.extraction_screen import Extraction_Screen
from gui.screens.drying_screen import Drying_Screen
from gui.screens.oxygen_desorption_screen import Oxygen_Desorption_Screen
from gui.screens.distillation_screen import Distillation_Screen
from gui.screens.fluid_flow_screen import Fluid_Flow_Screen

# 导入配置
from gui.screens.utils.config import *

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

from gui.screens.utils.smooth_resize_window import Smooth_Resize_Window


class App:
    """
    应用主体
    """

    def __init__(
        self,
        dx: float = 0.1,
        time_interval: int = 500,
        plot_max_points: int = 500,
        port_timeout: float = 0.25,
        std_limit: float = 0.005,
        time_lower_limit: int = 30,
        time_upper_limit: int = 40,
        width_height_inches: tuple = (10, 7),
        dpi: int = 600,
        py_path: str = os.path.dirname(os.path.abspath(__file__)),
    ):
        # 数据配置
        DATA_CONFIG["app"] = self
        DATA_CONFIG["dx"] = dx
        DATA_CONFIG["time_interval"] = time_interval
        DATA_CONFIG["plot_max_points"] = plot_max_points
        DATA_CONFIG["port_timeout"] = port_timeout
        DATA_CONFIG["py_path"] = py_path
        DATA_CONFIG["std_limit"] = std_limit
        DATA_CONFIG["time_lower_limit"] = time_lower_limit
        DATA_CONFIG["time_upper_limit"] = time_upper_limit
        DATA_CONFIG["width_height_inches"] = width_height_inches
        DATA_CONFIG["dpi"] = dpi

        # 初始化窗口
        DATA_CONFIG["window"] = ttk.Window(
            themename="sandstone",
            title="ChemLabX1.0",
        )

        try:
            if sys.platform.startswith("darwin"):
                DATA_CONFIG["window"].iconphoto(
                    True,
                    PhotoImage(file="logos/ce.png"),
                )
            else:
                DATA_CONFIG["window"].iconbitmap("logos/ce.ico")
        except:
            pass

        # 设置窗口最小尺寸
        min_height = 960
        min_width = int(min_height * 4 / 3)
        DATA_CONFIG["window"].minsize(min_width, min_height)
        DATA_CONFIG["window"].geometry(f"{min_width}x{min_height}")

        # 获取屏幕尺寸
        screen_height = DATA_CONFIG["window"].winfo_screenheight()
        screen_width = DATA_CONFIG["window"].winfo_screenwidth()

        # 默认窗口尺寸为屏幕高度的75%，比例4:3
        default_height = int(screen_height * 0.75)
        default_width = int(screen_height * 0.75 * 4 / 3)

        # 根据屏幕尺寸调整窗口尺寸
        if (screen_height < min_height) or (screen_width < min_height):
            if (screen_height * 0.75 * 4 / 3) > min_width:
                default_height = int(screen_height * 0.75)
                default_width = int(screen_height * 0.75 * 4 / 3)
                DATA_CONFIG["window"].geometry(f"{default_width}x{default_height}")

        # 窗口左上角显示
        DATA_CONFIG["window"].geometry("+0+0")

        # 创建所有屏幕实例
        self.screens = {
            "base_screen": Base_Screen(DATA_CONFIG["window"]),
            "filteration_screen": Filteration_Screen(DATA_CONFIG["window"]),
            "heat_transfer_screen": Heat_Transfer_Screen(DATA_CONFIG["window"]),
            "extraction_screen": Extraction_Screen(DATA_CONFIG["window"]),
            "drying_screen": Drying_Screen(DATA_CONFIG["window"]),
            "oxygen_desorption_screen": Oxygen_Desorption_Screen(DATA_CONFIG["window"]),
            "distillation_screen": Distillation_Screen(DATA_CONFIG["window"]),
            "fluid_flow_screen": Fluid_Flow_Screen(DATA_CONFIG["window"]),
        }

        # 初始化 current_screen
        self.current_screen = None

        # 创建模式切换菜单
        self._create_mode_menu()

        # 默认显示过滤实验屏幕
        self.show_screen("base_screen")

        # 主事件循环
        DATA_CONFIG["window"].mainloop()

    def _create_mode_menu(self):
        """创建模式切换菜单"""
        menubar = ttk.Menu(DATA_CONFIG["window"])
        DATA_CONFIG["window"].config(menu=menubar)

        mode_menu = ttk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="实验模式", menu=mode_menu)

        # 创建菜单项
        mode_menu.add_command(
            label="基础模式", command=lambda: self.show_screen("base_screen")
        )
        mode_menu.add_command(
            label="过滤实验", command=lambda: self.show_screen("filteration_screen")
        )
        mode_menu.add_command(
            label="传热实验", command=lambda: self.show_screen("heat_transfer_screen")
        )
        mode_menu.add_command(
            label="萃取实验", command=lambda: self.show_screen("extraction_screen")
        )
        mode_menu.add_command(
            label="干燥实验", command=lambda: self.show_screen("drying_screen")
        )
        mode_menu.add_command(
            label="解吸实验",
            command=lambda: self.show_screen("oxygen_desorption_screen"),
        )
        mode_menu.add_command(
            label="精馏实验", command=lambda: self.show_screen("distillation_screen")
        )
        mode_menu.add_command(
            label="流体实验", command=lambda: self.show_screen("fluid_flow_screen")
        )

    def show_screen(self, screen_name):
        """显示指定的屏幕"""
        if self.current_screen:
            self.current_screen.pack_forget()

        if screen_name in self.screens:
            self.current_screen = self.screens[screen_name]
            self.current_screen.pack(fill="both", expand=True)

            # 只有在切换到非基础模式的界面时才触发抖动
            if screen_name != "base_screen":
                # 触发抖动效果
                self.smooth_resize = Smooth_Resize_Window(DATA_CONFIG["window"])
                self.smooth_resize.start()
        else:
            logging.error(f"未知屏幕名称: {screen_name}")

    def change_mode(self, *args):
        """界面模式切换，切换窗口"""
        event = DATA_CONFIG["mode"].get()
        if event == "过滤":
            self.show_screen("filteration_screen")
        elif event == "传热":
            self.show_screen("heat_transfer_screen")
        elif event == "萃取":
            self.show_screen("extraction_screen")
        elif event == "干燥":
            self.show_screen("drying_screen")
        elif event == "解吸":
            self.show_screen("oxygen_desorption_screen")
        elif event == "精馏":
            self.show_screen("distillation_screen")
        elif event == "流体":
            self.show_screen("fluid_flow_screen")
        else:
            logging.error(f"未知模式: {event}")

    def data_changed(self):
        """数据修改响应函数（预留扩展）"""
        pass
