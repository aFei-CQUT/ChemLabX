# base_screen.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import logging
import tkinter as tk
from tkinter import ttk
import serial

# 导入界面配置和小部件
from gui.screens.utils.config import MAIN_FRAME_CONFIG, SCREEN_CONFIG
from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.string_entries_widget import StringEntriesWidget
from gui.screens.common_widgets.table_widget import TableWidget

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)


class Base_Screen(ttk.Frame):
    """实验屏幕基类（集成优化组件版）"""

    # 需要在子类中重写的属性
    RAW_COLS = []  # 原始数据列名
    RESULT_COLS = []  # 结果数据列名
    SERIAL_CONFIG = {  # 串口默认配置
        "baudrate": 9600,
        "bytesize": serial.EIGHTBITS,
        "parity": serial.PARITY_NONE,
        "stopbits": serial.STOPBITS_ONE,
        "timeout": 1,
    }

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.data_files = None
        self.processed_data = None
        self.current_page = 0
        self.images_paths = []
        self.serial_connection = None
        self._debounce_id = None

        # 初始化组件
        self._init_components()
        self.window.protocol("WM_DELETE_WINDOW", self._safe_close)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _init_components(self):
        """初始化界面组件"""
        # 主面板布局
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(expand=True, fill="both")

        # 初始化左右面板
        self._init_left_panel()
        self._init_right_panel()

    def _init_left_panel(self):
        """初始化左侧操作面板"""
        self.left_frame = ttk.Frame(self.main_paned, width=400)
        self.main_paned.add(self.left_frame, weight=1)  # 设置权重，防止左侧区域过大

        # 参数输入区域
        self._init_parameter_input()

        # 实验控制按钮组
        self._init_control_buttons()

        # 数据表格
        self._init_data_tables()

    def _init_parameter_input(self):
        """基础参数输入初始化（提供默认空组件）"""
        self.param_widget = ttk.Frame(self.left_frame)  # 创建空容器防止属性丢失
        self.param_widget.pack_forget()  # 默认隐藏

    # _init_control_buttons方法
    def _init_control_buttons(self):
        """初始化控制按钮组"""
        # 实验控制按钮
        experiment_frame = ttk.Frame(self.left_frame, name="experiment_btn_frame")
        experiment_frame.pack(fill="x", padx=5, pady=(5, 2))

        buttons = [
            ("打开串口", self._toggle_serial),
            ("开始采集", self.start_data_acquisition),
            ("停止采集", self.stop_data_acquisition),
        ]
        for col, (text, cmd) in enumerate(buttons):
            btn = ttk.Button(experiment_frame, text=text, command=cmd)
            btn.grid(row=0, column=col, padx=2, pady=2, sticky="ew")
            experiment_frame.columnconfigure(col, weight=1)

        # 数据处理按钮
        data_frame = ttk.Frame(self.left_frame, name="data_btn_frame")
        data_frame.pack(fill="x", padx=5, pady=(2, 5))

        buttons = [
            ("导入数据", self.load_data),
            ("处理数据", self.process_data),
            ("绘制图形", self.plot_graph),
        ]
        for col, (text, cmd) in enumerate(buttons):
            btn = ttk.Button(data_frame, text=text, command=cmd)
            btn.grid(row=0, column=col, padx=2, pady=2, sticky="ew")
            data_frame.columnconfigure(col, weight=1)

    def _init_data_tables(self):
        """初始化数据表格"""
        # 原始数据表格
        self.raw_table = TableWidget(
            self.left_frame, self.RAW_COLS, [100] * len(self.RAW_COLS)
        )
        self.raw_table.pack(fill="both", expand=True, padx=5, pady=5)

        # 结果数据表格
        self.result_table = TableWidget(
            self.left_frame, self.RESULT_COLS, [100] * len(self.RESULT_COLS)
        )
        self.result_table.pack(fill="both", expand=True, padx=5, pady=5)

    def _init_right_panel(self):
        """初始化右侧绘图面板"""
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=2)

        # PlotWidget：内部已分成 canvas_frame 和 pagination_frame）
        self.plot_frame = PlotWidget(self.right_frame)
        self.plot_frame.pack(fill="both", expand=True)

        # 配置自适应布局
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(0, weight=1)

        # 添加对窗口大小调整的监听，确保右侧面板刷新
        self.right_frame.bind("<Configure>", self._on_right_panel_resize)

    def _on_right_panel_resize(self, event):
        """监听右侧面板大小调整"""
        # 强制更新布局
        self.right_frame.update_idletasks()  # 强制更新右侧面板
        self.right_frame.after(100, self.right_frame.update)  # 延时更新，确保刷新正常

        # 只在需要时刷新图形事件
        self.after(100, self.plot_frame.canvas.flush_events)  # 延迟刷新图形事件
        self.after(100, self.plot_frame.canvas.draw_idle)  # 延迟刷新图形

    @property
    def parameters(self):
        """获取当前参数值"""
        return self.param_widget.get_values()

    @parameters.setter
    def parameters(self, values):
        """设置参数值"""
        self.param_widget.set_values(values)

    def _handle_parameter_change(self):
        """处理参数变更"""
        try:
            if self.param_widget.validate_all():
                self.process_data()
                self.plot_graph()
            else:
                pass
        except Exception as e:
            pass

    # ---------------------------- 串口通信方法 ----------------------------
    def _toggle_serial(self):
        """切换串口连接状态（打开或关闭）。"""
        if self.serial_connection and self.serial_connection.is_open:
            self._close_serial()
        else:
            self._open_serial_dialog()

    def _open_serial_dialog(self):
        """打开串口选择对话框（子类可重写）。"""
        # TODO: 实现串口选择对话框
        self.logger.info("打开串口选择对话框")

    def _open_serial(self, port, baudrate):
        try:
            self.serial_connection = serial.Serial(
                port=port, baudrate=baudrate, **self.SERIAL_CONFIG
            )
        except Exception as e:
            self.logger.error(f"串口打开失败: {str(e)}")

    def _close_serial(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

    # ---------------------------- 通用功能方法 ----------------------------
    def bind_parameter_change(self, widget):
        """绑定参数修改事件到控件。

        Args:
            widget: Tkinter 小部件
        """
        widget.bind("<<ParameterChange>>", self._on_parameter_change)

    def _on_parameter_change(self, event=None):
        """基类参数变更回调空实现"""
        pass

    def _handle_parameter_change(self):
        """基类参数变更处理空实现"""
        pass

    def start_data_acquisition(self):
        """数据采集启动（子类必须重写）。"""
        raise NotImplementedError("子类需实现 start_data_acquisition 方法")

    def stop_data_acquisition(self):
        """停止数据采集（子类必须重写）。"""
        raise NotImplementedError("子类需实现 stop_data_acquisition 方法")

    def show_processing(self, msg="处理中..."):
        """显示处理中对话框。

        Args:
            msg: 对话框显示的消息
        """
        self.processing_win = tk.Toplevel(self.window)
        self.processing_win.title("请稍候")
        self.processing_win.geometry("300x100")

        ttk.Label(self.processing_win, text=msg).pack(pady=10)
        self.progress = ttk.Progressbar(self.processing_win, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=5)
        self.progress.start()

        self.processing_win.grab_set()
        self.processing_win.update()

    def update_table(self, table, data):
        if isinstance(table, TableWidget):
            table.clear()
            table.update_columns(self.RAW_COLS)  # 使用 TableWidget 的列更新方法
            if data is not None:
                for idx, row in enumerate(data):
                    formatted_row = [f"{idx+1}"] + [
                        f"{x:.2f}" if isinstance(x, float) else str(x) for x in row
                    ]
                    table.append(formatted_row)

    def close_processing(self):
        """增强版关闭处理方法"""
        if hasattr(self, "processing_win"):
            try:
                # 先停止进度条再销毁窗口
                if hasattr(self, "progress"):
                    self.progress.stop()
            except Exception as e:
                self.logger.error(f"进度条停止失败: {str(e)}")
            finally:
                # 确保资源释放
                self.processing_win.grab_release()
                self.processing_win.destroy()
                del self.processing_win
                if hasattr(self, "progress"):
                    del self.progress

    def _safe_close(self):
        """安全关闭窗口，确保资源释放。"""
        self._close_serial()
        if hasattr(self, "processing_win"):
            self.close_processing()
        self.window.destroy()

    # ---------------------------- 核心功能接口 ----------------------------
    def load_data(self):
        """加载数据（子类必须重写）。"""
        raise NotImplementedError("子类必须实现 load_data 方法")

    def process_data(self):
        """处理数据（子类必须重写）。"""
        raise NotImplementedError("子类必须实现 process_data 方法")

    def plot_graph(self):
        """绘制图表（子类必须重写）。"""
        raise NotImplementedError("子类必须实现 plot_graph 方法")
