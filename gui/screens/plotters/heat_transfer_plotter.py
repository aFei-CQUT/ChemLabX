# heat_transfer_plotter.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 50
plt.rcParams["savefig.dpi"] = 300

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from gui.screens.calculators.heat_transfer_calculator import Heat_Transfer_Calculator


class Heat_Transfer_Plotter:
    def __init__(self, calculator_results):
        """
        初始化画图类

        参数:
        calculator_results: 从Heat_Transfer_Calculator获取的结果数据
        """
        self.results = calculator_results
        self.setup_plot_style()  # 初始化时设置全局样式

    def fit_func(self, x, a, b):
        """
        拟合函数，用于曲线拟合。

        参数:
        x (numpy.ndarray): 自变量
        a (float): 拟合参数
        b (float): 拟合参数

        返回:
        numpy.ndarray: 拟合结果
        """
        return a + b * x

    def setup_plot_style(self):
        """统一配置绘图样式"""
        plt.rcParams.update(
            {
                "font.family": "Microsoft YaHei",
                "font.size": 12,
                "axes.unicode_minus": False,
                "figure.dpi": 50,
                "savefig.dpi": 300,
                "axes.linewidth": 2,
                "grid.linestyle": "-",
                "grid.linewidth": 1,
                "mathtext.default": "regular",
                "font.sans-serif": [
                    "Microsoft YaHei",
                    "SimHei",
                    "DejaVu Sans",
                ],  # 字体回退列表
                "text.usetex": False,
                "mathtext.fontset": "dejavusans",  # 使用与中文字体兼容的数学字体
            }
        )

    def create_directory(self, filepath):
        """确保文件保存路径存在"""
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def configure_plot(self, title):
        """配置通用绘图参数"""
        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel(r"$\mathrm{Re}$", fontsize=14, fontweight="bold")
        plt.ylabel(r"$\mathrm{Nu/Pr^{0.4}}$", fontsize=14, fontweight="bold")
        plt.title(title, fontsize=10, fontweight="bold")
        plt.grid(True, which="both")
        plt.minorticks_on()
        ax = plt.gca()
        for spine in ax.spines.values():
            spine.set_linewidth(2)

    def plot_fit(self, data_for_fit, filename, title):
        """优化后的拟合绘图方法"""
        if len(data_for_fit) == 0:
            print(f"警告：跳过 {title} 的绘图，数据为空")
            return

        try:
            # 曲线拟合
            ans_params, _ = curve_fit(
                self.fit_func,
                np.log10(data_for_fit[:, 0]),
                np.log10(data_for_fit[:, 1]),
            )
        except Exception as e:
            print(f"曲线拟合失败：{str(e)}")
            return

        # 配置图形
        plt.figure(figsize=(8, 6), dpi=125)
        self.configure_plot(title)

        # 绘制数据点及拟合曲线
        plt.scatter(data_for_fit[:, 0], data_for_fit[:, 1], color="r", label="实验数据")
        plt.plot(
            data_for_fit[:, 0],
            10 ** self.fit_func(np.log10(data_for_fit[:, 0]), *ans_params),
            color="k",
            label="拟合曲线",
        )

        # 添加拟合方程文本
        equation_text = (
            f"拟合方程: y = {10**ans_params[0]:.10f} * x^{ans_params[1]:.2f}"
        )
        plt.text(
            0.05,
            0.95,
            equation_text,
            transform=plt.gca().transAxes,
            fontsize=12,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        # 保存输出
        self.create_directory(filename)
        plt.legend()
        plt.savefig(filename, bbox_inches="tight")
        plt.close()

    def generate_plots(self):
        """生成所有分析图表"""
        # 处理第一组数据（无强化套管）
        if len(self.results) > 0 and self.results[0]["params"] is not None:
            self.plot_fit(
                self.results[0]["data_for_fit"],
                "./拟合图结果/无强化套管拟合.png",
                "无强化套管传热性能分析",
            )

        # 处理第二组数据（有强化套管）
        if len(self.results) > 1 and self.results[1]["params"] is not None:
            self.plot_fit(
                self.results[1]["data_for_fit"],
                "./拟合图结果/有强化套管拟合.png",
                "有强化套管传热性能分析",
            )

        # 生成对比图
        self.generate_comparison_plot()

    def generate_comparison_plot(self):
        """生成对比分析图"""
        has_valid_data = False
        plt.figure(figsize=(10, 8), dpi=125)
        self.configure_plot("传热性能对比分析")

        # 绘制第一组数据（无强化套管）
        if len(self.results) > 0 and self.results[0]["params"] is not None:
            data = self.results[0]["data_for_fit"]
            plt.scatter(
                data[:, 0],
                data[:, 1],
                color="r",
                marker="o",
                s=80,
                label="无强化套管实验数据",
            )
            plt.plot(
                data[:, 0],
                10 ** self.fit_func(np.log10(data[:, 0]), *self.results[0]["params"]),
                color="r",
                linestyle="--",
                linewidth=2,
                label="无强化套管拟合曲线",
            )
            has_valid_data = True

        # 绘制第二组数据（有强化套管）
        if len(self.results) > 1 and self.results[1]["params"] is not None:
            data = self.results[1]["data_for_fit"]
            plt.scatter(
                data[:, 0],
                data[:, 1],
                color="b",
                marker="s",
                s=80,
                label="有强化套管实验数据",
            )
            plt.plot(
                data[:, 0],
                10 ** self.fit_func(np.log10(data[:, 0]), *self.results[1]["params"]),
                color="b",
                linestyle="-.",
                linewidth=2,
                label="有强化套管拟合曲线",
            )
            has_valid_data = True

        if has_valid_data:
            self.create_directory("./拟合图结果/传热性能对比.png")
            plt.legend(fontsize=12, loc="upper left")
            plt.savefig("./拟合图结果/传热性能对比.png", bbox_inches="tight")
            plt.close()
        else:
            print("警告：无有效数据生成对比图")


# 使用示例
if __name__ == "__main__":
    # 定义CSV文件路径列表
    csv_file_paths = [
        "./csv_data/传热/传热原始数据记录表(非)/原始数据_无强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/原始数据_有强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/数据预处理_无强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/数据预处理_有强化套管.csv",
    ]

    # 实例化传热计算器（需要确保Heat_Transfer_Calculator已修改为接受CSV文件）
    heat_transfer_calculator = Heat_Transfer_Calculator(csv_file_paths)

    # 数据处理
    heat_transfer_calculator.process_data()

    # 创建作图器并传递计算结果
    plotter = Heat_Transfer_Plotter(heat_transfer_calculator.results)

    # 生成并保存图表
    plotter.generate_plots()
