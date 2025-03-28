# filteration_screen.py

# 内部库
import sys
import os
import logging
import traceback
import pandas as pd
from tkinter import messagebox, filedialog
from PIL import Image

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

# 导入基类和组件
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.processors.filteration_experiment_processor import (
    Filteration_Experiment_Processor,
)


class Filteration_Screen(Base_Screen):
    """过滤实验界面（继承自Base_Screen基类）"""

    RAW_COLS = ["行号", "索引", "滤面高度 (cm)", "时间θ (s)", "时间差Δθ (s)"]
    RESULT_COLS = ["组号", "斜率", "截距"]

    def __init__(self, window):
        super().__init__(window)
        self.csv_file_path = None
        self.processed_data = None
        self.processor = None
        self.images_paths = []

        # 配置实验专用按钮（保留基类的串口控制按钮）
        self._configure_experiment_buttons()

    def _configure_experiment_buttons(self):
        """配置实验专用按钮状态（保留串口按钮为禁用状态）"""
        # 禁用尚未实现的串口功能按钮
        self._disable_unimplemented_buttons()

    def _disable_unimplemented_buttons(self):
        """禁用未实现功能的按钮"""
        btn_frame = self.left_frame.nametowidget("experiment_btn_frame")
        for child in btn_frame.winfo_children():
            if child.winfo_name() == "打开串口":
                child.configure(state="disabled")  # 禁用但保留可见

    # ---------------------------- 核心功能重写 ----------------------------
    def load_data(self):
        """加载CSV数据并更新原始数据表格"""
        file_path = filedialog.askopenfilename(
            title="选择CSV文件", filetypes=[("CSV文件", "*.csv")]
        )
        if not file_path:
            return

        try:
            # 读取并预处理数据
            data = pd.read_csv(file_path, header=0)
            data = data.apply(pd.to_numeric, errors="coerce").dropna()

            # 更新实例状态
            self.csv_file_path = file_path

            # 更新原始数据表格
            self.raw_table.clear()
            for idx, row in data.iterrows():
                self.raw_table.append([idx + 1, *row.values])

        except Exception as e:
            messagebox.showerror("错误", f"数据加载失败: {str(e)}")
            self.logger.error(f"数据加载异常: {traceback.format_exc()}")

    def process_data(self):
        """处理数据并更新结果表格"""
        if not self.csv_file_path:
            messagebox.showwarning("警告", "请先导入数据文件")
            return

        try:
            self.show_processing("数据处理中...")
            self.processor = Filteration_Experiment_Processor(self.csv_file_path)
            self.processor.calculate()
            self.processor.store()
            self.processed_data = self.processor.processed_data

            # 更新结果表格
            self.result_table.clear()
            for res in self.processed_data:
                self.result_table.append(
                    [res["group"], f"{res['slope']:.4f}", f"{res['intercept']:.2f}"]
                )

        except Exception as e:
            messagebox.showerror("错误", f"数据处理失败: {str(e)}")
            self.logger.error(f"数据处理异常: {traceback.format_exc()}")
        finally:
            self.close_processing()

    def plot_graph(self):
        """生成图表并更新绘图组件"""
        if not hasattr(self, "processor") or not self.processor:
            messagebox.showwarning("警告", "请先完成数据处理")
            return

        try:
            self.show_processing("图表生成中...")
            self.processor.plot()
            self.images_paths = self.processor.plotter.images_paths

            # 更新绘图组件
            self.plot_frame.set_images_paths(self.images_paths)
        except Exception as e:
            messagebox.showerror("错误", f"图表生成失败: {str(e)}")
            self.logger.error(f"绘图异常: {traceback.format_exc()}")
        finally:
            self.close_processing()

    # ---------------------------- 事件处理增强 ----------------------------
    def _safe_close(self):
        """关闭前资源清理"""
        if hasattr(self, "processor"):
            del self.processor
        super()._safe_close()
