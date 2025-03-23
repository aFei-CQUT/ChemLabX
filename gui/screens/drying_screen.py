# drying_screen.py

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
    Toplevel,
    messagebox,
    ttk,
    Button,
    filedialog,
    Canvas,
    StringVar,
)
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import numpy as np
import pandas as pd
import tkinter as tk

# 配置 logging 信息
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# 导入界面配置和小部件
from gui.screens.utils.config import MAIN_FRAME_CONFIG, SCREEN_CONFIG
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.processors.drying_experiment_processor import Drying_Experiment_Processor


class Drying_Screen(ttk.Frame):
    """
    干燥实验界面类，包含数据处理、显示和导入功能
    """

    RAW_COLS = ["时间τ/min", "总质量W1/g", "干球温度t_dry/℃", "湿球温度t_wet/℃"]
    RESULT_COLS = ["参数", "值"]

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.csv_file_paths = None
        self.processed_data = None
        self.current_page = 0
        self.images_paths = []
        self._init_components()
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def _init_components(self):
        """初始化界面组件"""
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(expand=True, fill="both")

        # 左侧面板
        self.left_frame = ttk.Frame(self.main_paned, width=600)
        self.main_paned.add(self.left_frame, weight=1)
        self._init_left_panel()

        # 右侧面板
        self.right_frame = ttk.Frame(self.main_paned, width=800)
        self.main_paned.add(self.right_frame, weight=2)
        self._init_right_panel()

    def _init_left_panel(self):
        """初始化左侧面板"""
        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(side="top", fill="x", padx=5, pady=5)

        # 导入数据按钮
        self.import_data_btn = Button(button_frame, text="导入CSV数据", command=self.load_csv_data)
        self.import_data_btn.pack(side="left", padx=5, pady=5)

        # 处理数据按钮
        self.process_data_btn = Button(button_frame, text="处理数据", command=self.process_data)
        self.process_data_btn.pack(side="left", padx=5, pady=5)

        # 绘制图形按钮
        self.plot_graph_btn = Button(button_frame, text="绘制图形", command=self.plot_graph)
        self.plot_graph_btn.pack(side="left", padx=5, pady=5)

        # 原始数据表格
        self.raw_data_display = ttk.LabelFrame(self.left_frame, text="原始数据")
        self.raw_data_display.pack(pady=10, fill="both", expand=True)
        self.raw_data_table = TableWidget(self.raw_data_display, self.RAW_COLS, widths=[100, 120, 120, 120])
        self.raw_data_table.pack(pady=10, fill="both", expand=True)

        # 结果数据表格
        self.res_data_display = ttk.LabelFrame(self.left_frame, text="计算结果")
        self.res_data_display.pack(pady=10, fill="both", expand=True)
        self.res_data_table = TableWidget(self.res_data_display, self.RESULT_COLS, widths=[100, 150])
        self.res_data_table.pack(pady=10, fill="both", expand=True)

    def _init_right_panel(self):
        """初始化右侧面板"""
        self.right_paned = ttk.PanedWindow(self.right_frame, orient="vertical")
        self.right_paned.pack(fill="both", expand=True)

        # 绘图区域
        self.plot_frame = ttk.Frame(self.right_paned)
        self.right_paned.add(self.plot_frame, weight=1)

        # 图像显示Canvas
        self.image_canvas = Canvas(self.plot_frame)
        self.image_canvas.pack(fill="both", expand=True)
        self.image_canvas.bind("<Configure>", self.on_resize)

        # 页码标签
        self.page_label = ttk.Label(self.right_frame, text="Page 1/1")
        self.page_label.pack(side="top", padx=5, pady=5)

        # 翻页按钮
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(side="bottom", fill="x", padx=5, pady=10)

        self.prev_btn = ttk.Button(button_frame, text="上一页", command=self.show_prev_page, state="disabled")
        self.prev_btn.pack(side="left", padx=5, pady=5)

        self.next_btn = ttk.Button(button_frame, text="下一页", command=self.show_next_page, state="disabled")
        self.next_btn.pack(side="left", padx=5, pady=5)

    def load_csv_data(self):
        """加载干燥实验CSV文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择干燥实验CSV文件（需包含原始数据1和原始数据2）",
            filetypes=[("CSV Files", "*.csv")],
            initialdir="./",
        )

        if not file_paths:
            return

        try:
            # 验证文件命名规范
            data1_path, data2_path = None, None
            for path in file_paths:
                filename = os.path.basename(path).lower()
                if "原始数据1" in filename:
                    data1_path = path
                elif "原始数据2" in filename:
                    data2_path = path

            if not all([data1_path, data2_path]):
                raise ValueError("必须包含原始数据1和原始数据2文件")

            # 加载原始数据2到表格显示
            df = pd.read_csv(data2_path, header=0, skiprows=[1])
            raw_data = df[["累计时间τ/min", "总质量W1/g", "干球温度t_dry/℃", "湿球温度t_wet/℃"]].values

            self.csv_file_paths = [data1_path, data2_path]
            self.update_raw_data_table(raw_data)

            messagebox.showinfo("成功", "文件加载完成！")

        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败：{str(e)}")
            logging.error(traceback.format_exc())

    def process_data(self):
        """处理干燥实验数据"""
        if not self.csv_file_paths:
            messagebox.showwarning("警告", "请先导入CSV数据！")
            return

        try:
            self.show_processing_window()

            # 创建处理器实例
            self.processor = Drying_Experiment_Processor(self.csv_file_paths)
            outputs = self.processor.process_experiment()

            # 获取计算结果
            self.results = self.processor.get_results()
            self.images_paths = [
                outputs["combined_plot"],
                outputs["combined_plot"].replace("combined_plots", "drying_curve"),
                outputs["combined_plot"].replace("combined_plots", "drying_rate_curve"),
            ]

            # 更新结果表格
            self.update_results_table()

            self.close_processing_window()
            self.enable_page_buttons()
            messagebox.showinfo("成功", "数据处理完成！")
        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("错误", f"数据处理失败：{str(e)}")
            logging.error(traceback.format_exc())

    def plot_graph(self):
        """生成并显示图表"""
        if not hasattr(self, "processor"):
            messagebox.showwarning("警告", "请先处理数据！")
            return

        try:
            self.show_processing_window()

            # 显示第一张图
            if self.images_paths:
                self.current_page = 0
                self.show_current_page()
                self.enable_page_buttons()

            self.close_processing_window()
            messagebox.showinfo("成功", "图表生成完成！")
        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("错误", f"图表生成失败：{str(e)}")
            logging.error(traceback.format_exc())

    # 以下是通用方法，与传热界面保持一致
    def show_processing_window(self):
        """显示处理中的窗口"""
        self.processing_window = Toplevel(self.window)
        self.processing_window.title("处理中")
        self.processing_window.geometry("200x100")
        label = ttk.Label(self.processing_window, text="正在处理，请稍候...")
        label.pack(expand=True)
        self.processing_window.grab_set()
        self.processing_window.update()

    def close_processing_window(self):
        """关闭处理中的窗口"""
        if hasattr(self, "processing_window"):
            self.processing_window.grab_release()
            self.processing_window.destroy()

    def update_raw_data_table(self, raw_data=None):
        """更新原始数据表格"""
        self.raw_data_table.clear()
        if raw_data is not None:
            for row in raw_data:
                self.raw_data_table.append([row[0], row[1], row[2], row[3]])

    def update_results_table(self):
        """更新计算结果表格"""
        self.res_data_table.clear()
        if hasattr(self.processor, "U_c") and hasattr(self.processor, "α"):
            results = [
                ("恒定干燥速率 U_c (kg/m²·h)", f"{self.processor.U_c:.4f}"),
                ("传热系数 α (kW/m²·K)", f"{self.processor.α.mean():.4f}"),
                ("初始体积流量 V_t0 (m³/s)", f"{self.processor.V_t0:.6f}"),
            ]
            for param, value in results:
                self.res_data_table.append([param, value])

    def show_current_page(self):
        """显示当前页的图形"""
        self.image_canvas.delete("all")
        if not self.images_paths or self.current_page >= len(self.images_paths):
            return

        try:
            img = Image.open(self.images_paths[self.current_page])
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()

            # 保持宽高比缩放
            img_ratio = img.width / img.height
            canvas_ratio = canvas_width / canvas_height

            if canvas_ratio > img_ratio:
                new_height = canvas_height
                new_width = int(new_height * img_ratio)
            else:
                new_width = canvas_width
                new_height = int(new_width / img_ratio)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)

            # 居中显示
            x_pos = (canvas_width - new_width) // 2
            y_pos = (canvas_height - new_height) // 2

            self.image_canvas.create_image(x_pos, y_pos, image=img_tk, anchor="nw")
            self.image_canvas.image = img_tk

            # 更新页码
            self.page_label.config(text=f"Page {self.current_page + 1}/{len(self.images_paths)}")
        except Exception as e:
            logging.error(f"加载图像失败: {str(e)}")

    def on_resize(self, event):
        """处理画布大小变化"""
        if self.images_paths:
            self.show_current_page()

    def show_prev_page(self):
        """显示上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_page()
        self.enable_page_buttons()

    def show_next_page(self):
        """显示下一页"""
        if self.current_page < len(self.images_paths) - 1:
            self.current_page += 1
            self.show_current_page()
        self.enable_page_buttons()

    def enable_page_buttons(self):
        """启用/禁用翻页按钮"""
        if not self.images_paths or len(self.images_paths) <= 1:
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
        else:
            prev_state = "normal" if self.current_page > 0 else "disabled"
            next_state = "normal" if self.current_page < len(self.images_paths) - 1 else "disabled"
            self.prev_btn.config(state=prev_state)
            self.next_btn.config(state=next_state)

    def close_window(self):
        """关闭窗口"""
        self.window.destroy()
