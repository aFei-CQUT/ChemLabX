# oxygen_desorption_screen.py

# 内部库
import sys
import os
import logging
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import (
    Label,
    Toplevel,
    messagebox,
    ttk,
    filedialog,
)
from PIL import Image, ImageTk
import pandas as pd


# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = Path(current_script_path).parents[2]  # 向上3级到项目根
sys.path.insert(0, str(project_root))

# 导入基类和组件
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.string_entries_widget import StringEntriesWidget

# 导入处理器
from gui.screens.processors.oxygen_desorption_experiment_processor import (
    Oxygen_Desorption_Experiment_Processor,
)


# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("pandas").setLevel(logging.WARNING)


class Oxygen_Desorption_Screen(Base_Screen):
    """
    氧解吸实验界面类（继承自Base_Screen）
    """

    RAW_COLS = [
        "序号",
        "水流量(L/h)",
        "空气流量(m³/h)",
        "压差(mmH2O)",
        "入口浓度(mg/L)",
        "出口浓度(mg/L)",
        "温度(℃)",
    ]
    RESULT_COLS = ["实验组别", "液相流量(mol/s)", "气相流量(mol/s)", "传质系数Kxa"]

    def __init__(self, window):
        # 显式声明按钮属性
        self.process_btn = None
        self.plot_btn = None
        super().__init__(window)
        self.window.protocol("WM_DELETE_WINDOW", self._safe_close)  # 绑定关闭协议
        self.file_paths = {}
        self.images_paths = []
        self.experiment_processor = None
        self._init_custom_components()

    def _init_custom_components(self):
        """初始化氧解吸特有组件"""
        # 覆盖原始表格配置
        self.raw_table.update_columns(self.RAW_COLS, [100] * len(self.RAW_COLS))
        self.result_table.update_columns(
            self.RESULT_COLS, [150] * len(self.RESULT_COLS)
        )

        # 配置参数输入
        self._init_parameter_input()

        # 绑定处理按钮和绘图按钮
        self._bind_buttons()

    def _bind_buttons(self):
        """动态绑定基类创建的按钮实例"""
        # 查找基类中"数据处理"按钮所在的Frame
        data_frame = self.left_frame.nametowidget("data_btn_frame")

        # 遍历Frame中的子组件
        for child in data_frame.winfo_children():
            if isinstance(child, ttk.Button):
                text = child["text"]
                if text == "处理数据":
                    self.process_btn = child
                elif text == "绘制图形":
                    self.plot_btn = child

    def _init_parameter_input(self):
        """初始化参数输入组件（已移除水温和大气压）"""
        self.param_widget = ttk.Frame(self.left_frame)
        self.param_widget.pack(fill="x", padx=5, pady=5)

        # 配置参数输入（已无参数）
        param_config = []  # 空配置，不创建任何输入
        self.param_entries = StringEntriesWidget(self.param_widget)
        self.param_entries.update_entries(param_config)
        self.param_entries.pack(fill="x", padx=5, pady=5)
        self.bind_parameter_change(self.param_entries)

    def load_data(self):
        """重写基类方法，执行文件导入逻辑"""
        self._import_all_files()

    def _import_all_files(self):
        """文件导入方法"""
        # 弹出文件选择对话框，允许用户多选CSV文件
        file_paths = filedialog.askopenfilenames(
            title="选择氧解吸实验数据文件(请同时选择干填料、湿填料、水流量一定和空气流量一定文件)",
            filetypes=[("CSV文件", "*.csv")],
        )

        if not file_paths:
            return

        # 根据文件名关键词分类文件路径
        self.file_paths.clear()
        for path in file_paths:
            filename = Path(path).name
            if "干填料" in filename:
                key = "dry_packed"
            elif "湿填料" in filename:
                key = "wet_packed"
            elif "水流量一定" in filename:
                key = "water_constant"
            elif "空气流量一定" in filename:
                key = "air_constant"
            else:
                continue
            self.file_paths[key] = path

        # 验证文件完整性并更新界面状态
        self._check_files_complete()

        # 加载首个文件（干填料）的预览数据
        if "dry_packed" in self.file_paths:
            self._load_data_preview(self.file_paths["dry_packed"])

    def _check_files_complete(self):
        """验证文件完整性"""
        required = ["dry_packed", "wet_packed", "water_constant", "air_constant"]
        if all(k in self.file_paths for k in required):
            if self.process_btn:
                self.process_btn.config(state="normal")
            self.status_var.set("就绪")
        else:
            if self.process_btn:
                self.process_btn.config(state="disabled")
            missing = [k for k in required if k not in self.file_paths]
            messagebox.showwarning("文件缺失", f"缺少必要文件: {', '.join(missing)}")

    def _load_data_preview(self, path):
        """加载预览数据到表格"""
        try:
            df = pd.read_csv(path, header=None)
            preview_data = df.iloc[2:, 1:7].values.tolist()
            self.update_table(self.raw_table, preview_data)
        except Exception as e:
            logging.error(f"数据预览加载失败: {str(e)}")
            messagebox.showerror("错误", f"文件读取失败: {Path(path).name}")

    def process_data(self):
        """处理流程"""
        try:
            self.show_processing("正在计算传质系数...")

            # 初始化实验处理器
            self.experiment_processor = Oxygen_Desorption_Experiment_Processor(
                dry_packed_path=self.file_paths["dry_packed"],
                wet_packed_path=self.file_paths["wet_packed"],
                water_constant_path=self.file_paths["water_constant"],
                air_constant_path=self.file_paths["air_constant"],
                output_dir="./results",
            )

            # 执行完整计算流程
            self.experiment_processor.run_all_calculations(compress_results=False)

            # 更新结果和图表
            self._update_results()
            self.plot_btn.config(state="normal")
            self.status_var.set("计算完成")

        except Exception as e:
            logging.error(traceback.format_exc())
            messagebox.showerror("计算错误", f"数据处理失败: {str(e)}")
        finally:
            self.close_processing()

    def _update_results(self):
        """更新结果表格"""
        self.result_table.clear()

        # 填料塔结果
        tower_data = self.experiment_processor.tower_calculator.results
        for res in tower_data:
            self.result_table.append(
                [Path(res["csv_file"]).stem, "-", "-", f"拟合类型: {res['fit_type']}"]
            )

        # 氧解吸结果
        oxygen_data = self.experiment_processor.oxygen_calculator.results
        for res in oxygen_data:
            for i in range(len(res["L"])):
                self.result_table.append(
                    [
                        f"{Path(res['csv_file']).stem}_{i+1}",
                        f"{res['L'][i]:.4f}",
                        f"{res['G'][i]:.4f}",
                        f"{res['Kxa'][i]:.4f}",
                    ]
                )

    def plot_graph(self):
        """增强版绘图方法"""
        if not self.experiment_processor:
            messagebox.showwarning("警告", "请先处理数据")
            return

        try:
            # 动态获取最新图像路径
            self.images_paths = [
                str(Path(self.experiment_processor.output_dir) / "填料塔性能对比.png"),
                str(Path(self.experiment_processor.output_dir) / "氧解吸传质关联.png"),
            ]
            self.plot_frame.set_images_paths(self.images_paths)
            self.plot_frame.show_current_image()
            self.status_var.set("就绪")
        except Exception as e:
            logging.error(f"图表显示失败: {str(e)}")
            messagebox.showerror("错误", "图表渲染失败，请检查图像文件")

    def _on_parameter_change(self, event=None):
        """参数变更响应"""
        if self.param_entries.validate_all():
            self.status_var.set("参数已更新，正在重新计算...")
            self.process_data()
        else:
            self.status_var.set("参数验证失败")

    def _safe_close(self):
        """关闭前资源释放"""
        super()._safe_close()
