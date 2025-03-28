# oxygen_desorption_plotter.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import warnings

warnings.filterwarnings("ignore")


from gui.screens.calculators.oxygen_desorption_calculator import (
    Oxygen_Desorption_Calculator,
)
from gui.screens.calculators.oxygen_desorption_calculator import Packed_Tower_Calculator
from gui.screens.calculators.oxygen_desorption_calculator import Experiment_Data_Loader


class Packed_Tower_Plotter:
    def __init__(self, calculator):
        self.calculator = calculator
        self._init_plot_style()

    def _init_plot_style(self):
        plt.rcParams["font.family"] = "SimHei"
        plt.rcParams["axes.unicode_minus"] = False

    def plot_comparison(self, save_path=None):
        plt.figure(figsize=(10, 6))

        # 确保有计算结果
        if not self.calculator.results:
            raise ValueError("没有可用的计算结果，请先运行calc_all_files()")

        # 绘制干填料数据
        dry_data = next(
            (r for r in self.calculator.results if "干填料" in r["csv_file"]), None
        )
        if dry_data:
            self._plot_single(dry_data, "干填料", "red")

        # 绘制湿填料数据
        wet_data = next(
            (r for r in self.calculator.results if "湿填料" in r["csv_file"]), None
        )
        if wet_data:
            self._plot_single(wet_data, "湿填料", "blue")

        plt.xlabel("空塔气速 u (m/s)")
        plt.ylabel("单位高度压降 Δp/Z (kPa/m)")
        plt.title("填料塔流体力学性能对比")
        plt.legend()
        plt.grid(True)
        plt.xlim(0, 1.3)
        plt.ylim(0, 40)
        ExperimentUtils.set_spine_width(plt.gca())

        # 处理保存路径
        output_path = save_path if save_path else "./拟合图结果/填料塔性能对比.png"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        # plt.show()

    def _plot_single(self, data, label, color):
        u = data["u"]
        delta_p = data["delta_p"]
        popt = data["popt"]

        plt.scatter(u, delta_p, color=color, label=label)
        x_fit = np.linspace(min(u), max(u), 100)

        if data["fit_type"] == "linear":
            y_fit = self.calculator.linear_fit(x_fit, *popt)
            eq = f"$Δp/Z = {popt[0]:.1f}u + {popt[1]:.1f}$"
        else:
            y_fit = self.calculator.taylor_fit(x_fit, *popt)
            eq = self._format_taylor_eq(popt)

        plt.plot(x_fit, y_fit, "k--", label=eq)

    @staticmethod
    def _format_taylor_eq(coefficients):
        terms = []
        for i, coeff in enumerate(coefficients):
            if abs(coeff) > 1e-6:  # 忽略接近零的系数
                term = f"{coeff:.1f}u^{i}" if i > 0 else f"{coeff:.1f}"
                terms.append(term)
        return "$Δp/Z = " + "+".join(terms) + "$" if terms else ""


class Oxygen_Desorption_Plotter:
    def __init__(self, calculator):
        self.calculator = calculator
        self._init_plot_style()

    def _init_plot_style(self):
        plt.rcParams["font.family"] = "SimHei"
        plt.rcParams["axes.unicode_minus"] = False

    def plot_correlation(self, save_path=None):
        plt.figure(figsize=(8, 8))

        # 确保有计算结果
        if not self.calculator.results:
            raise ValueError("没有可用的计算结果，请先运行calc_all_files()")

        for result in self.calculator.results:
            csv_file = result["csv_file"]
            label = Path(csv_file).stem.replace("_", " ")
            plt.scatter(result["L"], result["Kxa"], label=label)

        plt.xlabel("液相流量 L (mol/s)")
        plt.ylabel("传质系数 Kxa")
        plt.title("氧解吸传质系数关联")
        plt.legend()
        plt.grid(True)
        ExperimentUtils.set_spine_width(plt.gca())

        # 处理保存路径
        output_path = save_path if save_path else "./拟合图结果/氧解吸传质关联.png"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        # plt.show()


class ExperimentUtils:
    @staticmethod
    def set_spine_width(ax, width=2):
        """设置图表边框粗细"""
        for spine in ax.spines.values():
            spine.set_linewidth(width)


# ====================== 主程序 ======================
if __name__ == "__main__":
    try:
        # 使用更清晰的标识符初始化
        data_loader = Experiment_Data_Loader(
            dry_packed=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/干填料.csv",
            wet_packed=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/湿填料.csv",
            water_constant=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/水流量一定_空气流量改变.csv",
            air_constant=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/空气流量一定_水流量改变.csv",
        )

        # 填料塔计算
        tower_calculator = Packed_Tower_Calculator(data_loader)
        tower_calculator.calc_all_files()
        tower_plotter = Packed_Tower_Plotter(tower_calculator)
        tower_plotter.plot_comparison()

        # 氧解吸计算
        oxygen_calculator = Oxygen_Desorption_Calculator(data_loader)
        oxygen_calculator.calc_all_files()
        oxygen_plotter = Oxygen_Desorption_Plotter(oxygen_calculator)
        oxygen_plotter.plot_correlation()

    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
        print("请确保所有必需文件都存在")
    except Exception as e:
        print(f"发生未知错误: {str(e)}")
