# base_screen.py

# 内置库
import sys
import os
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import pandas as pd
import serial
from serial.tools import list_ports

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

# 导入界面配置和小部件
from gui.screens.utils.config import MAIN_FRAME_CONFIG, SCREEN_CONFIG
from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.spin_entries_widget import SpinEntriesWidget
from gui.screens.common_widgets.string_entries_widget import StringEntriesWidget
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.common_widgets.text_widget import TextWidget

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)


class Base_Screen(ttk.Frame):
    """实验屏幕基类"""

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
        self._debounce_id = None  # 防抖计时器ID

        # 初始化组件
        self._init_components()
        self.window.protocol("WM_DELETE_WINDOW", self._safe_close)

        # 日志记录器
        self.logger = logging.getLogger(self.__class__.__name__)

    def _init_components(self):
        """初始化通用界面组件"""
        # 主面板布局
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(expand=True, fill="both")

        # 初始化左右面板
        self._init_left_panel()
        self._init_right_panel()

    def _init_left_panel(self):
        """初始化左侧操作面板"""
        self.left_frame = ttk.Frame(self.main_paned, width=400)
        self.main_paned.add(self.left_frame, weight=1)

        # 实验控制按钮组（第一行）
        experiment_frame = ttk.Frame(self.left_frame)
        experiment_frame.pack(fill="x", padx=5, pady=(5, 2))

        self.serial_btn = ttk.Button(experiment_frame, text="打开串口", command=self._toggle_serial)
        self.serial_btn.pack(side="left", padx=2)

        ttk.Button(experiment_frame, text="开始采集", command=self.start_data_acquisition).pack(side="left", padx=2)
        ttk.Button(experiment_frame, text="停止采集", command=self.stop_data_acquisition).pack(side="left", padx=2)

        # 数据处理按钮组（第二行）
        data_frame = ttk.Frame(self.left_frame)
        data_frame.pack(fill="x", padx=5, pady=(2, 5))

        ttk.Button(data_frame, text="导入数据", command=self.load_data).pack(side="left", padx=2)
        ttk.Button(data_frame, text="处理数据", command=self.process_data).pack(side="left", padx=2)
        ttk.Button(data_frame, text="绘制图形", command=self.plot_graph).pack(side="left", padx=2)

        # 状态显示（第二行右侧）
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(data_frame, textvariable=self.status_var).pack(side="right", padx=5)

        # 数据表格
        self._init_data_tables()

        # 信息文本框
        self.info_text = TextWidget(self.left_frame)
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _init_data_tables(self):
        """初始化数据表格"""
        # 原始数据表格
        self.raw_table = TableWidget(self.left_frame, self.RAW_COLS, [100] * len(self.RAW_COLS))
        self.raw_table.pack(fill="both", expand=True, padx=5, pady=5)

        # 结果数据表格
        self.result_table = TableWidget(self.left_frame, self.RESULT_COLS, [100] * len(self.RESULT_COLS))
        self.result_table.pack(fill="both", expand=True, padx=5, pady=5)

    def _init_right_panel(self):
        """初始化右侧绘图面板"""
        self.right_frame = ttk.Frame(self.main_paned, width=600)
        self.main_paned.add(self.right_frame, weight=2)

        # 绘图容器
        self.plot_frame = PlotWidget(self.right_frame)
        self.plot_frame.pack(fill="both", expand=True, padx=0, pady=0)

    # ---------------------------- 串口通信方法 ----------------------------
    def _toggle_serial(self):
        """切换串口连接状态"""
        if self.serial_connection and self.serial_connection.is_open:
            self._close_serial()
        else:
            self._open_serial_dialog()

    def _open_serial_dialog(self):
        """打开串口选择对话框"""
        ports = list_ports.comports()
        if not ports:
            messagebox.showwarning("警告", "没有找到可用的串口设备")
            return

        dialog = tk.Toplevel(self.window)
        dialog.title("选择串口")
        dialog.geometry("300x200")

        ttk.Label(dialog, text="选择串口:").pack(pady=5)
        port_var = tk.StringVar(value=ports[0].device)
        port_menu = ttk.OptionMenu(dialog, port_var, ports[0].device, *[p.device for p in ports])
        port_menu.pack(pady=5)

        ttk.Label(dialog, text="波特率:").pack(pady=5)
        baud_var = tk.StringVar(value=str(self.SERIAL_CONFIG["baudrate"]))
        baud_entry = ttk.Entry(dialog, textvariable=baud_var)
        baud_entry.pack(pady=5)

        def connect():
            try:
                self._open_serial(port=port_var.get(), baudrate=int(baud_var.get()))
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开串口: {str(e)}")

        ttk.Button(dialog, text="连接", command=connect).pack(pady=10)

    def _open_serial(self, port, baudrate):
        """打开串口连接"""
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=self.SERIAL_CONFIG["bytesize"],
                parity=self.SERIAL_CONFIG["parity"],
                stopbits=self.SERIAL_CONFIG["stopbits"],
                timeout=self.SERIAL_CONFIG["timeout"],
            )
            self.serial_btn.config(text="关闭串口")
            self.status_var.set(f"已连接: {port} @ {baudrate}")
            self.logger.info(f"串口已连接: {port} @ {baudrate}")
        except Exception as e:
            self.logger.error(f"串口连接失败: {str(e)}")
            raise

    def _close_serial(self):
        """关闭串口连接"""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                self.serial_btn.config(text="打开串口")
                self.status_var.set("串口已断开")
                self.logger.info("串口已断开")
            except Exception as e:
                self.logger.error(f"关闭串口时出错: {str(e)}")

    # ---------------------------- 通用功能方法 ----------------------------

    def bind_parameter_change(self, widget):
        """绑定参数修改事件到控件"""
        widget.bind("<<ParameterChange>>", self._on_parameter_change)

    def _on_parameter_change(self, event=None):
        """参数修改回调（带防抖）"""
        if hasattr(self, "_debounce_id"):
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(800, self._handle_parameter_change)

    def _handle_parameter_change(self):
        """实际处理参数变更"""
        if hasattr(self, "csv_file_path") and self.csv_file_path:  # 如果已加载数据则重新处理
            try:
                self.status_var.set("参数更新中...")
                self.process_data()
                self.plot_graph()
                self.status_var.set("参数更新完成")
            except Exception as e:
                self.status_var.set("更新失败")
                self.logger.error(f"自动更新失败: {str(e)}")

    def start_data_acquisition(self):
        """数据采集启动（子类可重写）"""
        raise NotImplementedError("子类需实现 start_data_acquisition 方法")

    def stop_data_acquisition(self):
        """停止数据采集（子类可重写）"""
        raise NotImplementedError("子类需实现 stop_data_acquisition 方法")

    def show_processing(self, msg="处理中..."):
        """显示处理中对话框"""
        self.processing_win = tk.Toplevel(self.window)
        self.processing_win.title("请稍候")
        self.processing_win.geometry("300x100")

        ttk.Label(self.processing_win, text=msg).pack(pady=10)
        self.progress = ttk.Progressbar(self.processing_win, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=5)
        self.progress.start()

        self.processing_win.grab_set()
        self.processing_win.update()

    def close_processing(self):
        """关闭处理中对话框"""
        if hasattr(self, "processing_win"):
            self.progress.stop()
            self.processing_win.grab_release()
            self.processing_win.destroy()

    def update_table(self, table, data):
        """更新表格数据"""
        if isinstance(table, TableWidget):
            table.clear()
            table.table["columns"] = self.RAW_COLS
            for col in self.RAW_COLS:
                table.table.heading(col, text=col)
            if data is not None:
                for idx, row in enumerate(data):
                    table.append([idx + 1] + row.tolist())

    def _safe_close(self):
        """安全关闭窗口"""
        self._close_serial()
        if hasattr(self, "processing_win"):
            self.close_processing()
        self.window.destroy()

    # ---------------------------- 核心功能接口 ----------------------------
    def load_data(self):
        raise NotImplementedError("子类必须实现 load_data 方法")

    def process_data(self):
        raise NotImplementedError("子类必须实现 process_data 方法")

    def plot_graph(self):
        raise NotImplementedError("子类必须实现 plot_graph 方法")
