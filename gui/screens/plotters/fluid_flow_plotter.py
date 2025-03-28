# fluid_flow_plotter.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from gui.screens.calculators.fluid_flow_calculator import Fluid_Flow_Calculator
from gui.screens.calculators.fluid_flow_calculator import (
    Centrifugal_Pump_Characteristics_Calculator,
)
from gui.screens.calculators.fluid_flow_calculator import Auxiliary


class Fluid_Flow_Plotter:
    def __init__(self, calculator):
        self.calculator = calculator
        self.ans1 = calculator.ans1
        self.df = calculator.df
        self.p = calculator.p
        self.log_Re = calculator.log_Re
        self.log_λ = calculator.log_λ
        self.valid_idx = calculator.valid_idx
        self.Re = self.ans1[:, 1]
        self.λ = self.ans1[:, 2]

    def plot(self):
        """绘制流体阻力分析结果"""
        # 设置字体
        plt.rcParams["font.sans-serif"] = ["SimHei"]
        plt.rcParams["axes.unicode_minus"] = False

        # 有效数据
        Re_valid = self.Re[self.valid_idx]
        λ_valid = self.λ[self.valid_idx]
        log_Re = np.log10(Re_valid)
        log_λ = np.log10(λ_valid)

        # 生成插值点
        log_Re_interp = np.linspace(log_Re.min(), log_Re.max(), 100)
        log_lambda_interp = self.p(log_Re_interp)

        # 绘制无插值图
        plt.figure(figsize=(8, 6), dpi=125)
        plt.scatter(log_Re, log_λ, color="b", label="数据点")
        plt.plot(log_Re, self.p(log_Re), color="red", label="拟合曲线")
        plt.xlabel("lg(Re)")
        plt.ylabel("lg(λ)")
        plt.title("雷诺数与阻力系数双对数拟合(无插值)")
        plt.grid(True)
        plt.legend()
        plt.savefig("./拟合图结果/雷诺数与阻力系数双对数拟合(无插值).png", dpi=300)
        plt.close()

        # plt.show()

        # 绘制有插值图
        plt.figure(figsize=(8, 6), dpi=125)
        plt.scatter(log_Re, log_λ, color="b", label="数据点")
        plt.plot(log_Re_interp, log_lambda_interp, color="r", label="插值曲线")
        plt.xlabel("lg(Re)")
        plt.ylabel("lg(λ)")
        plt.title("雷诺数与阻力系数双对数拟合(有插值)")
        plt.grid(True)
        plt.legend()
        plt.savefig("./拟合图结果/雷诺数与阻力系数双对数拟合(有插值).png", dpi=300)
        plt.close()

        # plt.show()


class Centrifugal_Pump_Characteristics_Plotter:
    def __init__(self, calculator):
        self.calculator = calculator
        self.ans2 = calculator.ans2
        self.df = calculator.df
        self.params_H = calculator.params_H
        self.params_N = calculator.params_N
        self.params_η = calculator.params_η

    @staticmethod
    def quadratic(x, a, b, c):
        return a * x**2 + b * x + c

    def plot(self):
        """绘制离心泵特性曲线"""
        # 设置字体
        plt.rcParams["font.sans-serif"] = ["SimHei"]
        plt.rcParams["axes.unicode_minus"] = False

        # 获取数据
        Q = self.df.iloc[:, 1].values  # 流量(m³/h)
        H = self.ans2[:, 0]  # 扬程(m)
        N_elc_e = self.ans2[:, 1]  # 有效功率(W)
        η = self.ans2[:, 2]  # 效率

        # 单位转换
        N_elc_e_kW = N_elc_e / 1000  # W → kW
        η_percent = η * 100  # 小数 → 百分比

        # 生成拟合数据
        Q_fit = np.linspace(Q.min(), Q.max(), 100)
        H_fit = self.quadratic(Q_fit, *self.params_H)
        N_fit = self.quadratic(Q_fit, *self.params_N) / 1000  # kW
        η_fit = self.quadratic(Q_fit, *self.params_η) * 100  # %

        # 创建图形
        fig, ax1 = plt.subplots(figsize=(7.85, 6), dpi=125)
        ax1.scatter(Q, H, color="blue", label="扬程数据")
        ax1.plot(Q_fit, H_fit, "b-", label="扬程拟合")
        ax1.set_xlabel("$Q/(m^3/h)$")
        ax1.set_ylabel("$H/m$", color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")

        ax2 = ax1.twinx()
        ax2.scatter(Q, N_elc_e_kW, color="red", label="功率数据")
        ax2.plot(Q_fit, N_fit, "r--", label="功率拟合")
        ax2.set_ylabel("$N/kW$", color="red")
        ax2.tick_params(axis="y", labelcolor="red")

        ax3 = ax1.twinx()
        ax3.spines["right"].set_position(("outward", 60))
        ax3.scatter(Q, η_percent, color="green", label="效率数据")
        ax3.plot(Q_fit, η_fit, "g-.", label="效率拟合")
        ax3.set_ylabel("$\eta/\%$", color="green")
        ax3.tick_params(axis="y", labelcolor="green")

        fig.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=3)
        plt.title("离心泵特性曲线及二次拟合")
        plt.tight_layout(rect=[0.05, 0.03, 0.95, 0.93])
        plt.savefig("./拟合图结果/离心泵特性曲线及二次拟合.png", dpi=300)
        # plt.show()


class PlotManager:
    def __init__(self, auxiliary):
        self.auxiliary = auxiliary
        self.results = auxiliary.get_results()

    def plot_all(self):
        """绘制所有结果"""
        if "fluid" in self.results:
            fluid_calculator = Fluid_Flow_Calculator(self.auxiliary.file_paths[0])
            fluid_calculator.process()
            fluid_plotter = Fluid_Flow_Plotter(fluid_calculator)
            fluid_plotter.plot()

        if "pump" in self.results:
            pump_calculator = Centrifugal_Pump_Characteristics_Calculator(
                self.auxiliary.file_paths[1]
            )
            pump_calculator.process()
            pump_plotter = Centrifugal_Pump_Characteristics_Plotter(pump_calculator)
            pump_plotter.plot()


if __name__ == "__main__":
    os.makedirs("./拟合图结果", exist_ok=True)

    # 文件路径列表
    file_paths = [
        "./csv_data/流体/流体原始数据记录表(非)/流体阻力原始数据.csv",
        "./csv_data/流体/流体原始数据记录表(非)/离心泵原始数据.csv",
    ]

    # 创建Auxiliary实例并处理文件
    auxiliary = Auxiliary(file_paths)
    auxiliary.process_files()

    # 创建PlotManager实例并绘制所有结果
    plot_manager = PlotManager(auxiliary)
    plot_manager.plot_all()
