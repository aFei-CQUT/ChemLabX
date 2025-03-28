# filteration_experiment_processor.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import zipfile
import matplotlib.pyplot as plt
from gui.screens.calculators.filteration_calculator import Filteration_Calculator
from gui.screens.plotters.filteration_plotter import Filteration_Plotter

# 设置中文字体
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 50
plt.rcParams["savefig.dpi"] = 300


class Filteration_Experiment_Processor:
    """
    负责处理过滤实验数据的类。
    该类处理数据加载、拟合、异常值检测以及生成结果图形。
    """

    def __init__(self, csv_file_path):
        """
        初始化类并加载CSV文件以进行进一步处理。
        :param csv_file_path: 包含数据的CSV文件路径
        """
        self.csv_file_path = csv_file_path

        # 初始化计算类处理数据
        self.calculator = Filteration_Calculator(csv_file_path)

        # 初始化绘图类生成图形
        self.plotter = Filteration_Plotter(csv_file_path)

        # 初始化一个列表来存储处理后的数据
        self.processed_data = []

        # 存储来自Filteration_Calculator和Filteration_Plotter的数据
        self.calculator_data = {
            "data": self.calculator.data,
            "q_to_refit_lists": self.calculator.q_to_refit_lists,
            "delta_theta_over_delta_q_to_refit_lists": self.calculator.delta_theta_over_delta_q_to_refit_lists,
            "refit_slopes": self.calculator.refit_slopes,
            "refit_intercepts": self.calculator.refit_intercepts,
            "selected_data": self.calculator.selected_data,
            "data_array": self.calculator.data_array,
            "deltaV": self.calculator.deltaV,
            "S": self.calculator.S,
            "deltaQ": self.calculator.deltaQ,
            "delta_theta_list": self.calculator.delta_theta_list,
            "delta_q_list": self.calculator.delta_q_list,
            "delta_theta_over_delta_q_list": self.calculator.delta_theta_over_delta_q_list,
            "q_list": self.calculator.q_list,
            "q_to_fit": self.calculator.q_to_fit,
            "delta_theta_over_delta_q_to_fit": self.calculator.delta_theta_over_delta_q_to_fit,
            "fit_model": self.calculator.fit_model,
            "fit_data": self.calculator.fit_data,
            "fit_slope": self.calculator.fit_slope,
            "fit_intercept": self.calculator.fit_intercept,
            "outliers": self.calculator.outliers,
            "refit_model": self.calculator.refit_model,
            "filtered_data": self.calculator.filtered_data,
        }

        self.plotter_data = {
            "q_to_refit_lists": self.plotter.q_to_refit_lists,
            "delta_theta_over_delta_q_to_refit_lists": self.plotter.delta_theta_over_delta_q_to_refit_lists,
            "refit_slopes": self.plotter.refit_slopes,
            "refit_intercepts": self.plotter.refit_intercepts,
        }

    def calculate(self):
        """
        使用计算类处理数据。
        处理各组数据并返回进一步分析所需的信息。
        """
        # 处理所有组的数据并存储结果
        (
            self.q_to_refit_lists,
            self.delta_theta_over_delta_q_to_refit_lists,
            self.refit_slopes,
            self.refit_intercepts,
        ) = self.calculator.process_all_groups()

    def store(self):
        """
        将处理后的数据存储到类的processed_data列表中。
        这些数据将用于生成结果和图形。
        """
        for i in range(3):
            # 存储每组处理后的数据（q值、斜率、截距）到字典中
            group_data = {
                "group": i + 1,
                "q_values": self.q_to_refit_lists[i],
                "slope": self.refit_slopes[i],
                "intercept": self.refit_intercepts[i],
            }
            # 将每组的数据添加到processed_data列表中
            self.processed_data.append(group_data)

    def plot(self):
        """
        使用绘图类基于处理后的数据生成所有所需的图形。
        """
        # 使用绘图类生成图形
        self.plotter.generate_all_figures()

    def compress_results(self):
        """
        将生成的图像文件压缩成一个zip文件，便于分发和存储。
        """
        dir_to_zip = r"./拟合图结果"  # 存放结果的目录
        dir_to_save = r"./拟合图结果.zip"  # 目标zip文件路径

        # 创建zip文件并将结果目录中的所有文件添加进去
        with zipfile.ZipFile(dir_to_save, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dir_to_zip):
                for file in files:
                    file_dir = os.path.join(root, file)
                    arc_name = os.path.relpath(file_dir, dir_to_zip)
                    zipf.write(file_dir, arc_name)

        # 打印压缩完成的确认信息
        print(f"压缩完成。文件已保存为: {dir_to_save}")


if __name__ == "__main__":
    # 定义CSV文件的路径进行处理
    csv_file_path = r"./过滤原始数据记录表(非).csv"

    # 初始化处理类
    processor = Filteration_Experiment_Processor(csv_file_path)

    # 第一步：处理数据（包括拟合、异常值检测等）
    processor.calculate()  # 处理数据（计算、拟合等）

    # 第二步：存储处理后的数据（可选步骤，用于生成结果或摘要）
    processor.store()  # 存储处理后的数据

    # 第三步：基于处理后的数据生成图形
    processor.plot()  # 生成图形（初拟合、再拟合等）

    # 第四步：压缩结果图像文件为zip文件
    processor.compress_results()  # 将生成的结果文件压缩成zip文件
