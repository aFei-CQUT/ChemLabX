# distillation_screen.py

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
from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.text_widget import TextWidget
from gui.screens.processors.distillation_experiment_processor import Distillation_Experiment_Processor


class Distillation_Screen(ttk.Frame):
    """
    精馏实验界面类，包含数据处理、显示和导入功能。
    """

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.csv_file_path = None  # 存储CSV文件路径
        self.processed_data = None
        self.current_page = 0
        self.images_paths = []
        self.RAW_COLS = []  # 动态生成列标题
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

        # 导入数据按钮 - 修改为导入CSV文件
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
        self.raw_data_table = TableWidget(self.raw_data_display, [], widths=[])  # 初始时为空
        self.raw_data_table.pack(pady=10, fill="both", expand=True)

        # 结果数据表格
        self.res_data_display = ttk.LabelFrame(self.left_frame, text="计算结果")
        self.res_data_display.pack(pady=10, fill="both", expand=True)
        self.res_data_table = TableWidget(self.res_data_display, [], widths=[])
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
        """加载CSV文件数据"""
        file_path = filedialog.askopenfilename(
            title="选择精馏实验CSV文件",
            filetypes=[("CSV Files", "*.csv")],
            initialdir="./",
        )

        if not file_path:
            return

        try:
            self.csv_file_path = file_path

            # 加载数据到表格显示
            df = pd.read_csv(file_path)
            # 动态生成列标题
            self.RAW_COLS = ["序号"] + df.columns.tolist()
            self.update_raw_data_table(df.values)

            messagebox.showinfo("成功", "文件加载完成！")

        except Exception as e:
            messagebox.showerror("错误", f"加载CSV数据失败：{str(e)}")
            logging.error(traceback.format_exc())

    def process_data(self):
        """处理数据"""
        if not self.csv_file_path:
            messagebox.showwarning("警告", "请先导入CSV数据！")
            return

        try:
            self.show_processing_window()

            # 创建处理器实例并处理数据
            self.processors = []
            self.processed_data_list = []

            # 处理 R=4 的情况
            processor_r4 = Distillation_Experiment_Processor(
                file_path=self.csv_file_path,
                R=4,  # 回流比
                αm=2.0,  # 默认相对挥发度
                F=80,  # 默认进料量
                tS=30,  # 默认塔顶温度
                tF=26,  # 默认塔底温度
                output_dir="实验结果/R4",
            )
            processor_r4.process_experiment(show_plot=False)  # 不显示图形
            self.processors.append(processor_r4)
            self.processed_data_list.append(processor_r4.calculator.results)

            # 处理 R=无穷大 的情况
            processor_r_inf = Distillation_Experiment_Processor(
                file_path=self.csv_file_path,
                R=10000,  # 回流比（近似无穷大）
                αm=2.0,  # 默认相对挥发度
                F=80,  # 默认进料量
                tS=30,  # 默认塔顶温度
                tF=26,  # 默认塔底温度
                output_dir="实验结果/R_inf",
            )
            processor_r_inf.process_experiment(show_plot=False)  # 不显示图形
            self.processors.append(processor_r_inf)
            self.processed_data_list.append(processor_r_inf.calculator.results)

            # 更新结果表格
            self.update_results_table()

            self.close_processing_window()
            messagebox.showinfo("成功", "数据处理完成！")

        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("错误", f"数据处理失败：{str(e)}")
            logging.error(traceback.format_exc())

    def plot_graph(self):
        """绘制图形"""
        if not hasattr(self, "processors") or not self.processors:
            messagebox.showwarning("警告", "请先处理数据！")
            return

        try:
            self.show_processing_window()

            # 清空图像路径
            self.images_paths = []

            # 分别绘制两种回流比的图形
            for processor in self.processors:
                plot_path = processor.result_paths["visualization"]
                processor.plotter.plot_mccabe_thiele(save_path=plot_path, show=False)
                self.images_paths.append(plot_path)

            # 显示第一张图
            if self.images_paths:
                self.current_page = 0
                self.show_current_page()
                self.enable_page_buttons()

            self.close_processing_window()
            messagebox.showinfo("成功", "图形绘制完成！")

        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("错误", f"绘制图形失败：{str(e)}")
            logging.error(traceback.format_exc())

    def update_raw_data_table(self, raw_data=None):
        """更新原始数据表格"""
        self.raw_data_table.clear()
        # 动态设置表格列
        self.raw_data_table.table["columns"] = self.RAW_COLS
        for col in self.RAW_COLS:
            self.raw_data_table.table.heading(col, text=col)
        if raw_data is not None:
            for idx, row in enumerate(raw_data):
                # 确保数据行的长度与列数匹配
                row_data = [idx + 1] + row.tolist()
                self.raw_data_table.append(row_data)

    def update_results_table(self):
        """更新结果表格"""
        self.res_data_table.clear()
        RESULT_COLS = ["组号", "回流比", "理论塔板数", "实际塔板数", "分离效率"]
        self.res_data_table.table["columns"] = RESULT_COLS
        for col in RESULT_COLS:
            self.res_data_table.table.heading(col, text=col)

        for idx, (processor, data) in enumerate(zip(self.processors, self.processed_data_list)):
            # 根据回流比区分情况
            if processor.R == 4:
                reflux_ratio = 4
            else:
                reflux_ratio = "无穷大"

            # 添加结果到表格
            self.res_data_table.append(
                [
                    idx + 1,
                    reflux_ratio,
                    f"{data['理论塔板数']:.2f}",
                    f"{data['理论塔板数'] - 1:.2f}",
                    "N/A",  # 分离效率需要根据具体实验计算
                ]
            )

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
        self.enable_page_buttons()  # 翻页后更新按钮状态

    def show_next_page(self):
        """显示下一页"""
        if self.current_page < len(self.images_paths) - 1:
            self.current_page += 1
            self.show_current_page()
        self.enable_page_buttons()  # 翻页后更新按钮状态

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
