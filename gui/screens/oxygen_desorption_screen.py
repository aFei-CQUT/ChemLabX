# oxygen_desorption_screen.py

# 内部库
import sys
import os
import logging
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import Label, PhotoImage, Toplevel, messagebox, ttk, Button, filedialog, Canvas
from PIL import Image, ImageTk
import pandas as pd

# 配置日志设置
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# 设置第三方库的日志级别
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("pandas").setLevel(logging.WARNING)

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = Path(current_script_path).parents[2]  # 向上3级到项目根
sys.path.insert(0, str(project_root))

# 导入界面配置和小部件
from gui.screens.utils.config import MAIN_FRAME_CONFIG, SCREEN_CONFIG

from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.table_widget import TableWidget

# 导入计算器
from gui.screens.calculators.oxygen_desorption_calculator import Oxygen_Desorption_Calculator, Packed_Tower_Calculator

# 导入处理器
from gui.screens.processors.oxygen_desorption_experiment_processor import Oxygen_Desorption_Experiment_Processor


class Oxygen_Desorption_Screen(ttk.Frame):
    """
    氧解吸实验界面类，包含数据处理、显示和可视化功能
    """

    RAW_COLS = ["序号", "水流量(L/h)", "空气流量(m³/h)", "压差(mmH2O)", "入口浓度(mg/L)", "出口浓度(mg/L)", "温度(℃)"]
    RESULT_COLS = ["实验组别", "液相流量(mol/s)", "气相流量(mol/s)", "传质系数Kxa"]

    def __init__(self, window):
        super().__init__(window, **SCREEN_CONFIG)
        self.window = window
        self.file_paths = {}  # 存储四个文件的路径
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
        self.left_frame = ttk.Frame(self.main_paned, **MAIN_FRAME_CONFIG)
        self.main_paned.add(self.left_frame, weight=1)

        # 右侧面板
        self.right_frame = ttk.Frame(self.main_paned, **MAIN_FRAME_CONFIG)
        self.main_paned.add(self.right_frame, weight=2)

        self._init_left_panel()
        self._init_right_panel()

    def _init_left_panel(self):
        """初始化左侧操作面板"""
        # 文件选择区域
        file_select_frame = ttk.LabelFrame(self.left_frame, text="数据文件选择")
        file_select_frame.pack(fill="x", padx=5, pady=5)

        # 添加"导入所有文件"按钮
        ttk.Button(file_select_frame, text="导入所有文件", command=self._import_all_files).grid(
            row=0, column=0, columnspan=3, pady=5, sticky="ew"
        )

        # 文件显示区域
        ttk.Label(file_select_frame, text="已选择文件:").grid(row=1, column=0, sticky="w")
        self.file_listbox = tk.Listbox(file_select_frame, height=4, width=40)
        self.file_listbox.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # 操作按钮区域
        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        self.process_btn = ttk.Button(button_frame, text="处理数据", command=self.process_data, state="disabled")
        self.process_btn.pack(side="left", padx=5)

        self.plot_btn = ttk.Button(button_frame, text="生成图表", command=self.plot_graph, state="disabled")
        self.plot_btn.pack(side="left", padx=5)

        # 原始数据表格
        self.raw_data_display = ttk.LabelFrame(self.left_frame, text="原始数据预览")
        self.raw_data_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.raw_data_table = TableWidget(self.raw_data_display, self.RAW_COLS, widths=[10] * len(self.RAW_COLS))
        self.raw_data_table.pack(fill="both", expand=True)

        # 结果数据表格
        self.res_data_display = ttk.LabelFrame(self.left_frame, text="处理结果")
        self.res_data_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.res_data_table = TableWidget(self.res_data_display, self.RESULT_COLS, widths=[15] * len(self.RESULT_COLS))
        self.res_data_table.pack(fill="both", expand=True)

    def _init_right_panel(self):
        """初始化右侧可视化面板"""
        self.right_paned = ttk.PanedWindow(self.right_frame, orient="vertical")
        self.right_paned.pack(fill="both", expand=True)

        # 图像显示区域
        self.image_panel = ttk.Frame(self.right_paned)
        self.right_paned.add(self.image_panel, weight=1)
        self.image_canvas = Canvas(self.image_panel)
        self.image_canvas.pack(fill="both", expand=True)
        self.image_canvas.bind("<Configure>", self.on_resize)

        # 分页控制
        self.page_label = ttk.Label(self.right_frame, text="Page 1/1")
        self.page_label.pack(side="top", padx=5, pady=5)

        # 导航按钮
        nav_frame = ttk.Frame(self.right_frame)
        nav_frame.pack(side="bottom", fill="x", padx=5, pady=10)
        self.prev_btn = ttk.Button(nav_frame, text="上一页", command=self.prev_page, state="disabled")
        self.prev_btn.pack(side="left", padx=5)
        self.next_btn = ttk.Button(nav_frame, text="下一页", command=self.next_page, state="disabled")
        self.next_btn.pack(side="left", padx=5)

    def _import_all_files(self):
        """一次性导入所有需要的文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择氧解吸实验数据文件(请同时选择干填料、湿填料、水流量一定和空气流量一定文件)",
            filetypes=[("CSV文件", "*.csv")],
        )

        if not file_paths:
            return

        # 清空现有文件路径
        self.file_paths = {}
        self.file_listbox.delete(0, tk.END)

        # 根据文件名自动分类文件
        for file_path in file_paths:
            filename = os.path.basename(file_path).lower()

            if "干填料" in filename:
                self.file_paths["dry_packed"] = file_path
                self.file_listbox.insert(tk.END, f"干填料: {file_path}")
            elif "湿填料" in filename:
                self.file_paths["wet_packed"] = file_path
                self.file_listbox.insert(tk.END, f"湿填料: {file_path}")
            elif "水流量一定" in filename:
                self.file_paths["water_constant"] = file_path
                self.file_listbox.insert(tk.END, f"水流量一定: {file_path}")
            elif "空气流量一定" in filename:
                self.file_paths["air_constant"] = file_path
                self.file_listbox.insert(tk.END, f"空气流量一定: {file_path}")

        # 检查是否所有文件都已选择并加载预览
        self._check_files_complete()
        if "dry_packed" in self.file_paths:
            self._load_data_preview(self.file_paths["dry_packed"])

    def _check_files_complete(self):
        """检查是否所有必需文件都已选择"""
        required_files = ["dry_packed", "wet_packed", "water_constant", "air_constant"]
        if all(f in self.file_paths for f in required_files):
            self.process_btn.config(state="normal")
        else:
            self.process_btn.config(state="disabled")
            missing_files = [f for f in required_files if f not in self.file_paths]
            messagebox.showwarning("警告", f"缺少以下文件: {', '.join(missing_files)}\n请确保选择了所有必需文件")

    def _load_data_preview(self, file_path):
        """加载数据预览到表格"""
        try:
            df = pd.read_csv(file_path, header=None)
            # 数据从第3行开始，前两行是标题
            data = df.iloc[2:, 1:7].values  # 取第2列到第7列的数据
            self.update_raw_data_table(data)
        except Exception as e:
            messagebox.showerror("错误", f"数据预览加载失败: {str(e)}")
            logging.error(traceback.format_exc())

    def process_data(self):
        """执行数据处理流程"""
        try:
            self.show_processing_window()

            # 创建实验处理器实例
            self.experiment = Oxygen_Desorption_Experiment_Processor(
                dry_packed_path=self.file_paths["dry_packed"],
                wet_packed_path=self.file_paths["wet_packed"],
                water_constant_path=self.file_paths["water_constant"],
                air_constant_path=self.file_paths["air_constant"],
            )

            # 执行完整分析
            self.experiment.run_full_analysis(compress_results=False)

            # 更新结果表格
            self._update_results()

            # 设置图像路径
            self.images_paths = [
                str(Path(self.experiment.output_dir) / "填料塔性能对比.png"),
                str(Path(self.experiment.output_dir) / "氧解吸传质关联.png"),
            ]

            self.plot_btn.config(state="normal")
            self.close_processing_window()
            messagebox.showinfo("成功", "数据处理完成！")
        except Exception as e:
            self.close_processing_window()
            messagebox.showerror("错误", f"数据处理失败: {str(e)}")
            logging.error(traceback.format_exc())

    def _update_results(self):
        """更新结果表格"""
        self.res_data_table.clear()

        # 填料塔结果（通过Packed_Tower_Calculator获取）
        tower_calculator = Packed_Tower_Calculator(self.experiment.data_loader)
        tower_calculator.analyze_all_files()
        for result in tower_calculator.results:
            self.res_data_table.append([Path(result["csv_file"]).stem, "-", "-", f"拟合类型: {result['fit_type']}"])

        # 氧解吸结果（通过Oxygen_Desorption_Calculator获取）
        oxygen_calculator = Oxygen_Desorption_Calculator(self.experiment.data_loader)
        oxygen_calculator.analyze_all_files()
        for result in oxygen_calculator.results:
            for i in range(len(result["L"])):
                self.res_data_table.append(
                    [
                        f"{Path(result['csv_file']).stem}_{i+1}",
                        f"{result['L'][i]:.4f}",
                        f"{result['G'][i]:.4f}",
                        f"{result['Kxa'][i]:.4f}",
                    ]
                )

    def plot_graph(self):
        """生成并显示图表"""
        if not self.images_paths:
            messagebox.showwarning("警告", "没有可用的图表数据！")
            return

        try:
            self.current_page = 0
            self.show_page()
            self._update_page_controls()
            messagebox.showinfo("成功", "图表生成完成！")
        except Exception as e:
            messagebox.showerror("错误", f"图表显示失败: {str(e)}")
            logging.error(traceback.format_exc())

    def show_processing_window(self):
        """显示处理中提示窗口"""
        self.processing_window = Toplevel(self.window)
        self.processing_window.title("处理中")
        self.processing_window.geometry("300x100")
        Label(self.processing_window, text="数据处理中，请稍候...").pack(expand=True)
        self.processing_window.grab_set()
        self.processing_window.update()

    def close_processing_window(self):
        """关闭处理提示窗口"""
        if hasattr(self, "processing_window"):
            self.processing_window.grab_release()
            self.processing_window.destroy()

    def update_raw_data_table(self, data):
        """更新原始数据表格"""
        self.raw_data_table.clear()
        for idx, row in enumerate(data):
            self.raw_data_table.append([idx + 1] + list(row[:6]))  # 只显示前6列数据

    def on_resize(self, event):
        """调整图像尺寸"""
        if self.images_paths:
            self.show_page()

    def show_page(self):
        """显示当前页图像"""
        self.image_canvas.delete("all")
        if self.current_page < len(self.images_paths):
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

                self.image_canvas.create_image(x_pos, y_pos, anchor="nw", image=img_tk)
                self.image_canvas.image = img_tk
                self.page_label.config(text=f"Page {self.current_page + 1}/{len(self.images_paths)}")
            except Exception as e:
                logging.error(f"图像加载失败: {str(e)}")

    def prev_page(self):
        """显示上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()
            self._update_page_controls()

    def next_page(self):
        """显示下一页"""
        if self.current_page < len(self.images_paths) - 1:
            self.current_page += 1
            self.show_page()
            self._update_page_controls()

    def _update_page_controls(self):
        """更新分页控制按钮状态"""
        if len(self.images_paths) <= 1:
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
        else:
            self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
            self.next_btn.config(state="normal" if self.current_page < len(self.images_paths) - 1 else "disabled")

    def close_window(self):
        """安全关闭窗口"""
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("氧解吸实验数据处理")
    root.geometry("1200x800")
    screen = Oxygen_Desorption_Screen(root)
    screen.pack(expand=True, fill="both")
    root.mainloop()
