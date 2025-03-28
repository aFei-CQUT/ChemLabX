# drying_experiment_processor.py

# 内置库
import sys
import os
import numpy as np
import pandas as pd
import zipfile

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

from gui.screens.calculators.drying_calculator import Drying_Calculator
from gui.screens.plotters.drying_plotter import Drying_Plotter


class Drying_Experiment_Processor(Drying_Calculator):
    def __init__(self, csv_file_paths):
        """
        初始化实验处理器，直接传入CSV文件路径列表
        """
        super().__init__(csv_file_paths)
        self._plotter = None  # 绘图器实例，初始化时为None

    def process_experiment(self, output_dir="./拟合结果"):
        """
        处理整个干燥实验过程
        包括计算、绘图和结果输出
        """
        # 运行完整计算
        self.run_full_calculation()

        # 创建绘图器实例（如果尚未创建）
        if self._plotter is None:
            self._plotter = Drying_Plotter(self)

        # 运行完整绘图
        return self._plotter.run_full_plotting(output_dir)

    def get_results(self):
        """
        获取完整的计算结果
        """
        return self.results

    def get_plots(self, plot_type="combined"):
        """
        获取绘图结果
        可选参数：plot_type ('combined', 'curve', 'rate')
        """
        # 确保绘图器已经创建
        if self._plotter is None:
            self._plotter = Drying_Plotter(self)

        if plot_type == "combined":
            return self._plotter.integrate_images()
        elif plot_type == "curve":
            return self._plotter.plot_drying_curve()
        elif plot_type == "rate":
            return self._plotter.plot_drying_rate_curve()
        else:
            raise ValueError("无效的绘图类型，请选择 'combined', 'curve' 或 'rate'")

    def __str__(self):
        return f"Drying_Experiment_Processor处理了{len(self.csv_file_paths)}个CSV文件"


# 使用示例
if __name__ == "__main__":
    csv_files = [
        "./csv_data/干燥原始数据记录表(非)/原始数据1.csv",
        "./csv_data/干燥原始数据记录表(非)/原始数据2.csv",
    ]

    # 初始化实验处理器
    processor = Drying_Experiment_Processor(csv_files)

    # 处理实验并输出结果
    outputs = processor.process_experiment()

    print("实验处理完成，生成结果如下：")
    print(f"- 组合图表: {outputs['combined_plot']}")
    print(f"- 压缩包: {outputs['zip_archive']}")
    print(f"- 序列化数据: {outputs['serialized_data']}")

    # 获取计算结果
    results = processor.get_results()

    # 打印部分计算结果
    print("\n部分计算结果：")
    print(f"恒定干燥速率 U_c: {processor.U_c}")
    print(f"传热系数 α: {processor.α}")
