# filteration_screen.py

# 内部库
import sys
import os

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

import logging
import traceback

from tkinter import (
    Label,
    PhotoImage,
    Toplevel,
    messagebox,
    ttk,
    Button,
    filedialog,
    Canvas,
)

# 从 PIL 导入 Image (tkinter也有Image但是功能不如PIL强大) 和 ImageTk
from PIL import Image, ImageTk

# 设置matplotlib日志级别为ERROR，避免显示findfont的DEBUG信息
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# 设置Pillow日志级别为WARNING，避免显示DEBUG信息
logging.getLogger("PIL").setLevel(logging.WARNING)

# 配置日志设置
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# 导入必要的库
import pandas as pd

# 导入界面配置和小部件
from gui.screens.utils.config import MAIN_FRAME_CONFIG, SCREEN_CONFIG
from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.common_widgets.text_widget import TextWidget

# 导入数据处理类
from gui.screens.processors.filteration_experiment_processor import Filteration_Experiment_Processor


class Filteration_Screen(ttk.Frame):
    """
    过滤实验界面类，包含数据处理、显示和导入功能。
    """

    RAW_COLS = ["行号", "索引", "滤面高度 (cm)", "时间θ (s)", "时间差Δθ (s)"]
    RESULT_COLS = ["组号", "斜率", "截距"]

    def __init__(self, window):
        super().__init__(window, **SCREEN_CONFIG)
        self.window = window
        self.csv_file_path = None
        self.processed_data = None
        self.after_id = None  # 用于存储定时调用的ID，方便取消定时调用
        self.current_page = 0  # 当前页，控制显示的图形
        self.images_paths = []  # 存储图像文件路径
        self._init_components()

        # 将窗口关闭事件绑定到close_window方法
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def _init_components(self):
        """初始化界面组件，包括表格、按钮和绘图区域。"""
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(expand=True, fill="both")

        self.left_frame = ttk.Frame(self.main_paned, **MAIN_FRAME_CONFIG)
        self.main_paned.add(self.left_frame, weight=1)

        self.right_frame = ttk.Frame(self.main_paned, **MAIN_FRAME_CONFIG)
        self.main_paned.add(self.right_frame, weight=2)

        self.csv_file_path_table = TableWidget(self.left_frame, self.RAW_COLS, widths=[10, 40, 40, 40])

        self._init_left_panel()
        self._init_right_panel()

    def _init_left_panel(self):
        """初始化左侧面板，包含按钮和表格区域。"""
        self.left_paned = ttk.PanedWindow(self.left_frame, orient="vertical")
        self.left_paned.pack(expand=True, fill="both")

        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(side="top", fill="x", padx=5, pady=5)

        # 定义按钮及其功能
        self.com_port_btn = Button(button_frame, text="通信串口", command=self._open_serial_port)
        self.com_port_btn.pack(side="top", fill="x", padx=5, pady=5)

        self.import_data_btn = Button(button_frame, text="导入数据", command=self.load_csv_data)
        self.import_data_btn.pack(side="top", fill="x", padx=5, pady=5)

        self.process_data_btn = Button(button_frame, text="处理数据", command=self.process_data)
        self.process_data_btn.pack(side="top", fill="x", padx=5, pady=5)

        self.plot_graph_btn = Button(button_frame, text="绘制图形", command=self.plot_graph)
        self.plot_graph_btn.pack(side="top", fill="x", padx=5, pady=5)

        # 显示原始数据表格
        self.raw_data_display = ttk.LabelFrame(self.left_frame)
        self.left_paned.add(self.raw_data_display, weight=1)

        self.raw_data_table = TableWidget(self.raw_data_display, self.RAW_COLS, widths=[10, 10, 15, 15, 15])
        self.raw_data_table.pack(pady=10, fill="both", expand=True)

        # 显示处理结果数据表格
        self.res_data_display = ttk.LabelFrame(self.left_frame)
        self.left_paned.add(self.res_data_display, weight=1)

        self.res_data_table = TableWidget(self.res_data_display, self.RESULT_COLS, widths=[10, 40, 40])
        self.res_data_table.pack(pady=10, fill="both", expand=True)

        self.left_paned.update_idletasks()

    def _init_right_panel(self):
        """初始化右侧面板，包含绘图区域和文本输出区。"""
        self.right_paned = ttk.PanedWindow(self.right_frame, orient="vertical")
        self.right_paned.pack(fill="both", expand=True)

        # 绘图的主面板
        self.image_panel = ttk.Frame(self.right_paned)
        self.right_paned.add(self.image_panel, weight=1)

        # 创建显示图像的Canvas
        self.image_canvas = Canvas(self.image_panel)
        self.image_canvas.pack(fill="both", expand=True)

        # 绑定调整画布大小的事件
        self.image_canvas.bind("<Configure>", self.on_resize)

        # 页码标签
        self.page_label = ttk.Label(self.right_frame, text="Page 1")
        self.page_label.pack(side="top", padx=5, pady=5)

        # 底部按钮
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(side="bottom", fill="x", padx=5, pady=10)

        button_container = ttk.Frame(button_frame)
        button_container.pack(side="top", padx=10, pady=5)  # 按钮之间的间距

        self.prev_btn = Button(button_container, text="上一页", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5, pady=5)

        self.next_btn = Button(button_container, text="下一页", command=self.next_page)
        self.next_btn.pack(side="left", padx=5, pady=5)

    def show_processing_window(self):
        """弹出正在处理窗口"""
        self.processing_window = Toplevel(self.window)
        self.processing_window.title("Processing")
        self.processing_window.geometry("200x100")
        label = Label(self.processing_window, text="正在处理，请稍候...")
        label.pack(expand=True)
        self.processing_window.update()  # 强制更新，显示窗口

    def close_processing_window(self):
        """关闭正在处理窗口"""
        if hasattr(self, "processing_window"):
            self.processing_window.destroy()

    def process_data(self):
        """处理数据，当点击“处理数据”按钮时调用。"""
        if self.csv_file_path is None:
            messagebox.showwarning("Warning", "Please import data first!")
            return

        try:
            # 弹出处理中的窗口
            self.show_processing_window()

            # 创建Filteration_Experiment_Processor实例
            self.processor = Filteration_Experiment_Processor(self.csv_file_path)

            # 执行数据处理
            self.processor.calculate()  # 处理数据（计算、拟合等）
            self.processor.store()  # 存储处理后的数据

            self.processed_data = self.processor.processed_data

            # 更新结果表格
            self.update_results_table(self.processed_data)

            # 更新图像路径
            self.images_paths = self.processor.plotter.images_paths  # 获取生成的图像路径

            # 完成处理后关闭“正在处理”窗口
            self.close_processing_window()

        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("Error", f"Error processing data: {e}")

    def plot_graph(self):
        """绘制图形并在右侧面板显示"""
        if not hasattr(self, "processor") or self.processor is None:
            messagebox.showwarning("Warning", "Please process data first!")
            return

        try:
            # 弹出处理中的窗口
            self.show_processing_window()

            # 直接调用生成图形的方法
            self.processor.plot()

            # 压缩生成的结果图像文件
            self.processor.compress_results()

            # 更新图像路径
            self.images_paths = self.processor.plotter.images_paths

            # 完成处理后关闭“正在处理”窗口
            self.close_processing_window()

            # 自动刷新显示页面
            self.show_page()

        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("Error", f"Error plotting graph: {e}")

    def on_resize(self, event):
        """处理窗口大小调整，动态调整图像大小"""
        if self.images_paths:
            self.show_page()

    def show_page(self):
        """显示当前页的图形"""
        self.image_canvas.delete("all")  # 清空画布

        if self.images_paths:
            img_path = self.images_paths[self.current_page]
            try:
                img = Image.open(img_path)
                canvas_width = self.image_canvas.winfo_width()
                canvas_height = self.image_canvas.winfo_height()

                # 使用resize方法调整图像大小，保持宽高比
                img = img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)

                img_tk = ImageTk.PhotoImage(img)
                self.image_canvas.create_image(0, 0, image=img_tk, anchor="nw")
                self.image_canvas.image = img_tk  # 保持对图像的引用

            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

        # 更新页码
        self.page_label.config(text=f"Page {self.current_page + 1}")

        # 取消之前的定时调用（如果存在）
        if self.after_id is not None:
            self.window.after_cancel(self.after_id)

        # 安排下一个更新
        self.after_id = self.window.after(100, self.show_page)

    def close_window(self):
        """关闭窗口并取消所有待定的任务"""
        if self.after_id is not None:
            self.window.after_cancel(self.after_id)  # 取消待定的任务
        self.window.destroy()  # 关闭窗口

    def prev_page(self):
        """显示上一页的图形"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()

    def next_page(self):
        """显示下一页的图形"""
        if self.current_page < len(self.images_paths) - 1:
            self.current_page += 1
            self.show_page()

    def _open_serial_port(self):
        pass

    def load_csv_data(self):
        """加载CSV文件并预处理数据。"""
        file_path = filedialog.askopenfilename(title="选择CSV文件", filetypes=[("CSV Files", "*.csv")])

        if file_path:
            try:
                data = pd.read_csv(file_path, header=0)
                for col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors="coerce")
                data = data.dropna()

                self.csv_file_path = file_path
                self.update_raw_data_table(data)

            except Exception as e:
                messagebox.showerror("Error", f"Error loading data: {e}")

    def update_raw_data_table(self, raw_data=None):
        """更新原始数据表格。"""
        if isinstance(self.raw_data_table, TableWidget):
            self.raw_data_table.clear()
            self.raw_data_table.table["columns"] = self.RAW_COLS
            for col in self.RAW_COLS:
                self.raw_data_table.table.heading(col, text=col)
            if raw_data is not None:
                df = pd.DataFrame(raw_data)
                for idx, row in df.iterrows():
                    self.raw_data_table.append([idx] + row.tolist())

    def update_results_table(self, processed_data=None):
        """更新处理后的结果表格。"""
        if isinstance(self.res_data_table, TableWidget):
            self.res_data_table.clear()
            self.res_data_table.table["columns"] = self.RESULT_COLS
            for col in self.RESULT_COLS:
                self.res_data_table.table.heading(col, text=col)
            if processed_data is not None:
                for result in processed_data:
                    self.res_data_table.append([result["group"], result["slope"], result["intercept"]])
