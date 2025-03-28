# heat_transfer_screen.py

# 内部库
import os
import sys

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

import logging
import traceback
import numpy as np
import pandas as pd
from tkinter import filedialog, messagebox
from PIL import Image
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.common_widgets.string_entries_widget import StringEntriesWidget
from gui.screens.processors.heat_transfer_experiment_processor import (
    Heat_Transfer_Experiment_Processor,
)


class Heat_Transfer_Screen(Base_Screen):
    """传热实验界面类（继承优化基类版本）"""

    RAW_COLS = ["序号", "Δp孔板/kPa", "t入/°C", "t出/°C"]
    RESULT_COLS = ["组号", "Re", "Pr", "Nu/Pr^0.4"]
    IMAGE_PATHS = [
        "./拟合图结果/无强化套管拟合.png",
        "./拟合图结果/有强化套管拟合.png",
        "./拟合图结果/传热性能对比.png",
    ]

    def __init__(self, window):
        super().__init__(window)
        self.csv_file_paths = None
        self.processor = None
        self._enhance_init()

    def _enhance_init(self):
        """增强初始化配置"""
        self.param_widget = self._create_parameter_widget()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_parameter_widget(self):
        """创建参数输入组件（示例模板）"""
        widget = StringEntriesWidget(self.left_frame)
        widget.pack(fill="x", padx=5, pady=5)
        return widget

    def load_data(self):
        """重写数据加载方法（CSV文件处理）"""
        file_paths = filedialog.askopenfilenames(
            title="选择传热实验CSV文件（需包含无强化套管、有强化套管、预处理文件）",
            filetypes=[("CSV Files", "*.csv")],
            initialdir="./",
        )

        if not file_paths:
            return

        try:
            file_dict = self._classify_files(file_paths)
            self.csv_file_paths = list(file_dict.values())

            # 加载示例数据到原始表格
            df = pd.read_csv(file_dict["无强化套管"], header=None)

            # 强制将数据转换为数值类型
            numeric_data = df.iloc[1:7, 1:4].apply(pd.to_numeric, errors="coerce")

            self._update_table(self.raw_table, numeric_data.values)

            messagebox.showinfo(
                "成功",
                "文件加载完成:\n"
                + "\n".join(f"{k}: {v}" for k, v in file_dict.items()),
            )
        except Exception as e:
            self._handle_error("CSV加载失败", e)

    def _classify_files(self, paths):
        """文件分类逻辑"""
        file_dict = {
            "无强化套管": None,
            "有强化套管": None,
            "预处理_无": None,
            "预处理_有": None,
        }

        for path in paths:
            filename = os.path.basename(path).lower()
            if "无强化套管" in filename and "预处理" not in filename:
                file_dict["无强化套管"] = path
            elif "有强化套管" in filename and "预处理" not in filename:
                file_dict["有强化套管"] = path
            elif "预处理_无" in filename:
                file_dict["预处理_无"] = path
            elif "预处理_有" in filename:
                file_dict["预处理_有"] = path

        if missing := [k for k, v in file_dict.items() if not v]:
            messagebox.showerror("错误", f"缺少必要文件: {', '.join(missing)}")
            raise ValueError("文件分类不完整")
        return file_dict

    def process_data(self):
        """重写数据处理方法"""
        if not self.csv_file_paths:
            messagebox.showwarning("警告", "请先导入CSV数据！")
            return

        try:
            self.show_processing("数据计算中...")
            self.processor = Heat_Transfer_Experiment_Processor(self.csv_file_paths)
            self.processor.calculate()  # 分步计算
            self.processor.store()  # 分步存储
            self._update_result_table()
            messagebox.showinfo("成功", "数据处理完成！")  # 移除绘图相关操作
        except Exception as e:
            self._handle_error("数据处理失败", e)
        finally:
            self.close_processing()

    def _update_result_table(self):
        """更新结果表格数据"""
        self.result_table.clear()
        for data in self.processor.processed_data:
            re_mean = (
                np.mean(data["data_for_fit"][:, 0])
                if data["data_for_fit"].size > 0
                else 0
            )
            pr_mean = (
                np.mean(data["calculated_data"].loc["Pr"])
                if "Pr" in data["calculated_data"].index
                else 0
            )
            nu_pr_mean = (
                np.mean(data["data_for_fit"][:, 1])
                if data["data_for_fit"].size > 0
                else 0
            )
            self.result_table.append(
                [data["group"], f"{re_mean:.2f}", f"{pr_mean:.2f}", f"{nu_pr_mean:.2f}"]
            )

    def plot_graph(self):
        """重写绘图方法"""
        if not self.processor:
            messagebox.showwarning("警告", "请先处理数据！")
            return

        try:
            self.show_processing("生成图表中...")
            self.processor.plot()  # 生成图表
            self.processor.compress_results()  # 压缩结果
            self.plot_frame.set_images_paths(self.IMAGE_PATHS)  # 更新图像路径
            self.plot_frame.show_current_image()  # 显示图像
            messagebox.showinfo("成功", "图表生成完成！")
        except Exception as e:
            self._handle_error("绘图失败", e)
        finally:
            self.close_processing()

    def _update_table(self, table, data):
        """通用表格更新方法"""
        table.clear()
        for idx, row in enumerate(data):
            formatted_row = []
            for x in row:
                if isinstance(x, (int, float)):  # 检查是否为数值类型
                    formatted_row.append(f"{x:.2f}")
                else:
                    formatted_row.append(str(x))  # 如果不是数值类型，直接转换为字符串
            table.append([idx + 1, *formatted_row])

    def _handle_error(self, title, error):
        """统一错误处理"""
        self.logger.error(f"{title}: {str(error)}\n{traceback.format_exc()}")
        messagebox.showerror(title, str(error))
        self.close_processing()

    # 保留必要的基类方法重写
    def start_data_acquisition(self):
        """空实现采集方法（本实验不需要）"""
        pass

    def stop_data_acquisition(self):
        """空实现停止方法（本实验不需要）"""
        pass
