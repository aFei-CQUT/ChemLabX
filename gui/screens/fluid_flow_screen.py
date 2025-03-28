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
import numpy as np
import pandas as pd
import re
from tkinter import messagebox, filedialog

# 导入基类和组件
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.processors.fluid_flow_experiment_processor import (
    Fluid_Flow_Expriment_Processor,
)


class Fluid_Flow_Screen(Base_Screen):
    """流体流动实验界面（继承自Base_Screen基类）"""

    RAW_COLS = ["序号", "Q/(L/h)", "直管阻力压降/kPa", "温度t/℃"]
    RESULT_COLS = ["组号", "Re", "λ", "H/m", "N/kW", "η/%"]

    def __init__(self, window):
        super().__init__(window)
        self.processor = None
        self.csv_file_paths = []
        self.images_paths = []

        # 初始化组件调整
        self._adjust_components()
        self._update_button_states()

    def _adjust_components(self):
        """调整基类组件布局"""
        # 调整表格列宽
        self.raw_table.pack_forget()
        self.result_table.pack_forget()
        self.raw_table = TableWidget(
            self.left_frame, self.RAW_COLS, [60, 120, 120, 120], height=15
        )
        self.result_table = TableWidget(
            self.left_frame, self.RESULT_COLS, [60, 120, 120, 120, 120, 120], height=8
        )
        self.raw_table.pack(fill="both", expand=True, padx=5, pady=5)
        self.result_table.pack(fill="both", expand=True, padx=5, pady=5)

        # 配置分页控件
        self.plot_frame.set_images_paths = lambda paths: setattr(
            self.plot_frame, "images_paths", paths
        )

    def _update_button_states(self):
        """更新按钮状态"""
        data_loaded = bool(self.csv_file_paths)
        btn = self._find_button("data_btn_frame", 1)
        btn["state"] = "normal" if data_loaded else "disabled"

    def _find_button(self, frame_name, column):
        """查找指定按钮"""
        frame = self.left_frame.nametowidget(frame_name)
        return frame.grid_slaves(row=0, column=column)[0]

    # ---------------------------- 核心方法重写 ----------------------------
    def load_data(self):
        """加载双CSV文件数据"""
        file_paths = filedialog.askopenfilenames(
            title="选择流体流动实验文件",
            filetypes=[("CSV文件", "*.csv")],
            initialdir="./",
        )

        if not file_paths:
            return

        try:
            self.csv_file_paths = self._classify_files(file_paths)
            self._validate_files()

            # 加载并显示流体阻力数据
            fluid_df = pd.read_csv(self.csv_file_paths[0], skiprows=2, header=None)
            self.raw_table.clear()
            for idx, row in fluid_df.iterrows():
                self.raw_table.append([idx + 1, *row.values.tolist()[:3]])

            self._update_button_states()

        except Exception as e:
            messagebox.showerror("错误", f"文件加载失败: {str(e)}")
            logging.error(f"文件加载异常: {traceback.format_exc()}")

    def _classify_files(self, paths):
        """智能分类文件"""
        file_dict = {"fluid": None, "pump": None}
        key_patterns = {"fluid": ["流体阻力", "fluid"], "pump": ["离心泵", "pump"]}

        for path in paths:
            fname = os.path.basename(path).lower()
            for key, patterns in key_patterns.items():
                if any(p in fname for p in patterns) and not file_dict[key]:
                    file_dict[key] = path
                    break
        return [file_dict["fluid"], file_dict["pump"]]

    def _validate_files(self):
        """验证文件完整性"""
        if None in self.csv_file_paths:
            raise ValueError(
                "缺少必需文件类型!\n"
                "命名应包含以下关键词:\n"
                "- 流体阻力文件: 流体阻力/fluid\n"
                "- 离心泵文件: 离心泵/pump"
            )

    def process_data(self):
        """执行数据处理流程"""
        if not all(self.csv_file_paths):
            messagebox.showwarning("警告", "请先完整加载数据文件")
            return

        try:
            self.show_processing("数据处理中...")
            self.processor = Fluid_Flow_Expriment_Processor(self.csv_file_paths)
            self.processor.process_fluid_flow()
            self.processor.process_pump_characteristics()
            self._update_result_table()

        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")
            logging.error(f"处理异常: {traceback.format_exc()}")
        finally:
            self.close_processing()

    def _update_result_table(self):
        """更新结果表格数据"""
        if not self.processor:
            return

        self.result_table.clear()
        # 流体阻力结果
        fluid_results = self.processor.get_fluid_flow_results()
        self.result_table.append(
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
        pump_results = self.processor.get_pump_characteristics_results()
        self.result_table.append(
            [
                "离心泵特性",
                "",
                "",
                f"{np.mean(pump_results['head']):.2f}",
                f"{np.mean(pump_results['power']):.2f}",
                f"{np.mean(pump_results['efficiency']):.2f}",
            ]
        )

    def plot_graph(self):
        """显示生成的图表（精确过滤）"""
        if not self.processor or not hasattr(self.processor, "output_dir"):
            messagebox.showwarning("警告", "请先完成数据处理")
            return

        try:
            self.show_processing("生成图表中...")
            self.processor.generate_all_plots()

            # 精确匹配当前实验的图表文件
            expected_patterns = [
                r"雷诺数与阻力系数双对数拟合\(无插值\)\.png",
                r"雷诺数与阻力系数双对数拟合\(有插值\)\.png",
                r"离心泵特性曲线及二次拟合\.png",
            ]

            output_dir = self.processor.output_dir
            self.images_paths = []
            for f in sorted(os.listdir(output_dir)):
                if any(re.match(pattern, f) for pattern in expected_patterns):
                    self.images_paths.append(os.path.join(output_dir, f))

            if not self.images_paths:
                raise FileNotFoundError("未找到实验图表文件")

            # 清空历史图像缓存
            self.plot_frame.images_paths = []
            self.plot_frame.set_images_paths(self.images_paths)
            self.plot_frame.current_page = 0
            self.plot_frame.show_current_image()

        except Exception as e:
            messagebox.showerror("错误", f"图表生成失败: {str(e)}")
            self.logger.error(f"图表异常: {traceback.format_exc()}")
        finally:
            self.close_processing()

    def _safe_close(self):
        """安全关闭资源"""
        try:
            # 先关闭可能的处理窗口
            if hasattr(self, "processing_win"):
                self.close_processing()
        finally:
            # 清理处理器资源
            if hasattr(self, "processor"):
                del self.processor
            # 调用基类关闭方法
            super()._safe_close()
