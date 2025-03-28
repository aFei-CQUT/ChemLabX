# heat_transfer_experiment_processor.py

# 内部库
import sys
import os

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import zipfile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from gui.screens.calculators.heat_transfer_calculator import Heat_Transfer_Calculator
from gui.screens.plotters.heat_transfer_plotter import Heat_Transfer_Plotter

# 设置中文字体
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 50
plt.rcParams["savefig.dpi"] = 300


class Heat_Transfer_Experiment_Processor:
    """
    负责处理传热实验数据的类。
    该类处理数据加载、计算、拟合、异常值检测以及生成结果图形。
    修改为处理CSV文件而非Excel文件。
    """

    def __init__(self, csv_file_paths):
        """
        初始化类并加载CSV文件以进行进一步处理。
        :param csv_file_paths: 包含传热实验数据的CSV文件路径列表
        """
        self.csv_file_paths = csv_file_paths  # 存储CSV文件路径列表

        # 初始化计算类处理数据
        self.calculator = Heat_Transfer_Calculator(csv_file_paths)

        # 初始化绘图类生成图形
        self.plotter = Heat_Transfer_Plotter(self.calculator.results)

        # 初始化一个列表来存储处理后的数据
        self.processed_data = []

        # 存储来自计算器处理后的数据
        self.calculator_data = {"results": self.calculator.results}

    def calculate(self):
        """
        使用计算类处理传热实验数据。
        处理各组数据并返回拟合结果和计算信息。
        """
        # 加载数据
        datasets = self.calculator.load_data()

        # 数据预处理（已在初始化中完成）

        # 数据处理
        self.calculator.process_data()

    def store(self):
        """
        将处理后的数据存储到类的processed_data列表中。
        这些数据将用于生成结果和图形。
        """
        for idx, result in enumerate(self.calculator.results):
            group_data = {
                "group": idx + 1,
                "type": "无强化套管" if idx == 0 else "有强化套管",
                "data_for_fit": result["data_for_fit"],
                "params": result["params"],
                "original_data": result["original_data"],
                "calculated_data": result["calculated_data"],
            }
            self.processed_data.append(group_data)

    def plot(self):
        """
        使用绘图类基于处理后的数据生成所有所需的图形。
        """
        # 生成并保存图表
        self.plotter.generate_plots()

    def compress_results(self):
        """
        将生成的图像文件压缩成一个zip文件，便于分发和存储。
        """
        dir_to_zip = r"./拟合图结果"  # 存放结果的目录
        dir_to_save = r"./拟合图结果.zip"  # 目标zip文件路径

        # 检查结果目录是否存在
        if not os.path.exists(dir_to_zip):
            print(f"警告：结果目录 {dir_to_zip} 不存在，无法压缩")
            return

        # 创建zip文件并将结果目录中的所有文件添加进去
        with zipfile.ZipFile(dir_to_save, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dir_to_zip):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dir_to_zip)
                    zipf.write(file_path, arcname)

        # 打印压缩完成的确认信息
        print(f"压缩完成。文件已保存为: {dir_to_save}")

    def fit_data_summary(self):
        """
        生成实验拟合数据
        """
        summary = []
        for data in self.processed_data:
            summary.append(
                {
                    "实验类型": data["type"],
                    "数据点数": len(data["data_for_fit"]),
                    "拟合参数A": (
                        data["params"][0] if data["params"] is not None else "N/A"
                    ),
                    "拟合参数B": (
                        data["params"][1] if data["params"] is not None else "N/A"
                    ),
                }
            )

        summary_df = pd.DataFrame(summary)
        summary_path = "./拟合图结果/拟合数据.csv"
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        summary_df.to_csv(summary_path, index=False, encoding="utf_8_sig")
        print(f"拟合数据已保存至: {summary_path}")


if __name__ == "__main__":
    # 定义CSV文件路径列表
    csv_file_paths = [
        "./csv_data/传热/传热原始数据记录表(非)/原始数据_无强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/原始数据_有强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/数据预处理_无强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/数据预处理_有强化套管.csv",
    ]

    # 初始化处理类
    processor = Heat_Transfer_Experiment_Processor(csv_file_paths)

    # 第一步：处理数据（包括计算、拟合等）
    processor.calculate()

    # 第二步：存储处理后的数据（可选步骤，用于生成结果或摘要）
    processor.store()

    # 第三步：基于处理后的数据生成图形
    processor.plot()

    # 第四步：生成拟合结果报告
    processor.fit_data_summary()

    # 第五步：压缩结果图像文件为zip文件
    processor.compress_results()
