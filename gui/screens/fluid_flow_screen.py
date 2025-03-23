# fluid_flow_screen.py

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

# 配置日志设置
# 保留自己代码的DEBUG日志，过滤第三方库的
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 设置第三方库的日志级别
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("numpy").setLevel(logging.WARNING)
logging.getLogger("pandas").setLevel(logging.WARNING)

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

# 导入界面配置和小部件
from gui.screens.utils.config import MAIN_FRAME_CONFIG, SCREEN_CONFIG
from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.common_widgets.text_widget import TextWidget

# 实验处理器类
from gui.screens.processors.fluid_flow_experiment_processor import Fluid_Flow_Expriment_Processor


class Fluid_Flow_Screen(ttk.Frame):
    """
    流体流动实验界面类，包含数据处理、显示和导入功能。
    """

    RAW_COLS = ["序号", "Q/(L/h)", "直管阻力压降/kPa", "温度t/℃"]
    RESULT_COLS = ["组号", "Re", "λ", "H/m", "N/kW", "η/%"]

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.csv_file_paths = None  # 改为存储CSV文件路径列表
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
        self.raw_data_table = TableWidget(self.raw_data_display, self.RAW_COLS, widths=[60, 120, 120, 120])
        self.raw_data_table.pack(pady=10, fill="both", expand=True)

        # 结果数据表格
        self.res_data_display = ttk.LabelFrame(self.left_frame, text="计算结果")
        self.res_data_display.pack(pady=10, fill="both", expand=True)
        self.res_data_table = TableWidget(self.res_data_display, self.RESULT_COLS, widths=[60, 120, 120, 120, 120, 120])
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
        """加载CSV文件数据并自动分类"""
        # 选择多个CSV文件
        file_paths = filedialog.askopenfilenames(
            title="选择流体流动实验CSV文件（需包含流体阻力、离心泵数据）",
            filetypes=[("CSV Files", "*.csv")],
            initialdir="./",
        )

        if not file_paths:
            return

        try:
            # 文件分类字典
            file_dict = {"fluid": None, "pump": None}

            # 根据文件名关键词分类文件
            for path in file_paths:
                filename = os.path.basename(path).lower()
                if "流体阻力" in filename:
                    file_dict["fluid"] = path
                elif "离心泵" in filename:
                    file_dict["pump"] = path

            # 检查是否所有必要文件都已找到
            missing_files = [name for name, path in file_dict.items() if path is None]
            if missing_files:
                messagebox.showerror("错误", f"缺少必要的文件类型: {', '.join(missing_files)}")
                return

            # 存储分类后的文件路径
            self.csv_file_paths = list(file_dict.values())

            # 加载流体阻力数据到表格显示
            df = pd.read_csv(file_dict["fluid"], skiprows=2, header=None)
            raw_data = df.iloc[:, :4].values
            self.update_raw_data_table(raw_data)

            messagebox.showinfo(
                "成功", "文件加载完成，已自动分类:\n" + "\n".join([f"{k}: {v}" for k, v in file_dict.items()])
            )

        except Exception as e:
            messagebox.showerror("错误", f"加载CSV数据失败：{str(e)}")
            logging.error(traceback.format_exc())

    def process_data(self):
        """处理数据"""
        if not self.csv_file_paths:
            messagebox.showwarning("警告", "请先导入CSV数据！")
            return

        try:
            self.show_processing_window()

            # 1. 创建处理器实例并处理数据
            self.processor = Fluid_Flow_Expriment_Processor(self.csv_file_paths)
            self.processor.process_fluid_flow()
            self.processor.process_pump_characteristics()

            # 2. 获取处理后的数据
            self.processed_data = {
                "fluid": self.processor.get_fluid_flow_results(),
                "pump": self.processor.get_pump_characteristics_results(),
            }

            # 3. 更新结果表格
            self.update_results_table()

            # 4. 准备图像路径
            self.images_paths = [
                "./拟合图结果/雷诺数与阻力系数双对数拟合(无插值).png",
                "./拟合图结果/雷诺数与阻力系数双对数拟合(有插值).png",
                "./拟合图结果/离心泵特性曲线及二次拟合.png",
            ]

            self.close_processing_window()
            self.enable_page_buttons()
            messagebox.showinfo("成功", "数据处理完成！")
        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("错误", f"数据处理失败：{str(e)}")
            logging.error(traceback.format_exc())

    def plot_graph(self):
        """绘制图形"""
        if not hasattr(self, "processor") or not self.processor:
            messagebox.showwarning("警告", "请先处理数据！")
            return

        try:
            self.show_processing_window()

            # 1. 调用绘图方法
            self.processor.generate_all_plots()

            # 2. 更新图像路径
            self.images_paths = [
                "./拟合图结果/雷诺数与阻力系数双对数拟合(无插值).png",
                "./拟合图结果/雷诺数与阻力系数双对数拟合(有插值).png",
                "./拟合图结果/离心泵特性曲线及二次拟合.png",
            ]

            # 3. 显示第一张图
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

    # 以下是原有的辅助方法，保持不变
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
        self.raw_data_table.table["columns"] = self.RAW_COLS
        for col in self.RAW_COLS:
            self.raw_data_table.table.heading(col, text=col)
        if raw_data is not None:
            for idx, row in enumerate(raw_data):
                self.raw_data_table.append([idx + 1, row[0], row[1], row[2]])

    def update_results_table(self):
        """更新结果表格"""
        self.res_data_table.clear()
        self.res_data_table.table["columns"] = self.RESULT_COLS
        for col in self.RESULT_COLS:
            self.res_data_table.table.heading(col, text=col)

        # 流体阻力结果
        fluid_results = self.processed_data["fluid"]
        self.res_data_table.append(
            [
                "流体阻力",
                f"{np.mean(fluid_results['reynolds']):.2f}",
                f"{np.mean(fluid_results['friction_factor']):.2f}",
                "",
                "",
                "",
            ]
        )

        # 离心泵结果
        pump_results = self.processed_data["pump"]
        self.res_data_table.append(
            [
                "离心泵特性",
                "",
                "",
                f"{np.mean(pump_results['head']):.2f}",
                f"{np.mean(pump_results['power']):.2f}",
                f"{np.mean(pump_results['efficiency']):.2f}",
            ]
        )

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
        self.enable_page_buttons()  # 新增：翻页后更新按钮状态

    def show_next_page(self):
        """显示下一页"""
        if self.current_page < len(self.images_paths) - 1:
            self.current_page += 1
            self.show_current_page()
        self.enable_page_buttons()  # 新增：翻页后更新按钮状态

    def enable_page_buttons(self):
        """启用/禁用翻页按钮"""
        if not self.images_paths or len(self.images_paths) <= 1:
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
        else:
            # 根据当前页码设置按钮状态
            prev_state = "normal" if self.current_page > 0 else "disabled"
            next_state = "normal" if self.current_page < len(self.images_paths) - 1 else "disabled"
            self.prev_btn.config(state=prev_state)
            self.next_btn.config(state=next_state)

    def close_window(self):
        """关闭窗口"""
        self.window.destroy()
