# oxygen_desorption_calculator.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import warnings
from typing import Dict, List, Union
from pathlib import Path

warnings.filterwarnings("ignore")


class Experiment_Data_Loader:
    """数据加载器，负责管理实验数据文件"""

    def __init__(
        self,
        dry_packed: Union[str, Path],
        wet_packed: Union[str, Path],
        water_constant: Union[str, Path],
        air_constant: Union[str, Path],
    ):
        self.file_dict = {
            "干填料实验数据": Path(dry_packed),
            "湿填料实验数据": Path(wet_packed),
            "水流量恒定实验数据": Path(water_constant),
            "空气流量恒定实验数据": Path(air_constant),
        }

        # 验证所有文件是否存在
        self._validate_files()

    def _validate_files(self):
        """验证所有文件是否存在，并显示实际路径"""
        missing_files = []
        for name, path in self.file_dict.items():
            if not path.exists():
                missing_files.append(f"{name} (路径: {str(path)})")
        if missing_files:
            raise FileNotFoundError("以下文件未找到:\n" + "\n".join(missing_files))

    def get_file(self, identifier: str) -> Path:
        """通过标识符获取文件路径"""
        return self.file_dict.get(identifier)


# ====================== 填料塔实验 ======================
class Packed_Tower_Calculator:
    def __init__(self, data_loader: Experiment_Data_Loader):
        self.data_loader = data_loader
        self.required_files = ["干填料实验数据", "湿填料实验数据"]
        self.results = []
        self._init_parameters()
        self._validate_files()

    def _validate_files(self):
        """验证所需文件是否存在"""
        missing_files = [
            f for f in self.required_files if not self.data_loader.get_file(f).exists()
        ]
        if missing_files:
            raise FileNotFoundError(f"缺少填料塔实验必要文件: {missing_files}")

    def _init_parameters(self):
        self.D = 0.1  # 塔径 (m)
        self.Z = 0.75  # 塔高 (m)
        self.ρ_水 = 1000  # 修正为正确的密度 (kg/m³)
        self.g = 9.8  # 重力加速度 (m/s²)

    @staticmethod
    def linear_fit(x, a, b):
        return a * x + b

    @staticmethod
    def taylor_fit(x, *coefficients):
        return sum(coeff * (x**i) for i, coeff in enumerate(coefficients))

    def calc_fluid_dynamics(self, csv_file: str, threshold: float = 0.95) -> dict:
        file_path = self.data_loader.get_file(csv_file)
        df = pd.read_csv(file_path, header=None)
        data = df.iloc[2:, 1:].apply(pd.to_numeric, errors="coerce").values

        V_空 = data[:, 0]  # 空塔气速 (m³/h)
        t_空 = data[:, 1]  # 空塔温度 (°C)
        p_空气压力 = data[:, 2] * 1e3  # 转换为Pa
        Δp_全塔_mmH2O = data[:, 4]

        # 计算修正气速
        A = np.pi * (self.D / 2) ** 2
        V_空_修 = V_空 * np.sqrt(
            (1.013e5 / (p_空气压力 + 1.013e5)) * ((t_空 + 273.15) / 298.15)
        )
        u = V_空_修 / A / 3600  # 转换为m/s

        # 计算单位压降 (kPa/m)
        Δp_over_Z = (self.ρ_水 * self.g * Δp_全塔_mmH2O * 1e-3) / (self.Z * 1000)

        # 数据拟合
        corr, _ = pearsonr(u, Δp_over_Z)
        if abs(corr) >= threshold:
            popt, _ = curve_fit(self.linear_fit, u, Δp_over_Z)
            fit_type = "linear"
        else:
            popt, _ = curve_fit(self.taylor_fit, u, Δp_over_Z, p0=[0] * 5)
            fit_type = "taylor"

        return {
            "u": u,
            "delta_p": Δp_over_Z,
            "corr": corr,
            "popt": popt,
            "fit_type": fit_type,
            "csv_file": csv_file,
        }

    def calc_all_files(self):
        for csv_file in self.required_files:
            try:
                self.results.append(self.calc_fluid_dynamics(csv_file))
            except Exception as e:
                print(f"计算文件 {csv_file} 时出错: {str(e)}")


# ====================== 氧解吸实验 ======================
class Oxygen_Desorption_Calculator:
    def __init__(self, data_loader: Experiment_Data_Loader):
        self.data_loader = data_loader
        self.required_files = [
            "水流量恒定实验数据",
            "空气流量恒定实验数据",
        ]
        self.results = []
        self._init_parameters()
        self._validate_files()

    def _validate_files(self):
        """验证所需文件是否存在"""
        missing_files = [
            f for f in self.required_files if not self.data_loader.get_file(f).exists()
        ]
        if missing_files:
            raise FileNotFoundError(f"缺少氧解吸实验必要文件: {missing_files}")

    def _init_parameters(self):
        self.ρ_水 = 1000  # kg/m³
        self.M_H2O = 18e-3  # kg/mol
        self.M_O2 = 32e-3  # kg/mol
        self.D = 0.1  # 塔径 (m)
        self.Z = 0.75  # 塔高 (m)

    @staticmethod
    def oxygen_solubility(t):
        return (-8.5694e-5 * t**2 + 0.07714 * t + 2.56) * 1e9

    def analyze_file(self, csv_file: str) -> dict:
        file_path = self.data_loader.get_file(csv_file)
        df = pd.read_csv(file_path, header=None)
        data = df.iloc[2:, 1:].apply(pd.to_numeric, errors="coerce").values

        V_水 = data[:, 1]  # L/h
        V_空 = data[:, 2]  # m³/h
        ΔP = data[:, 3]  # mmH2O
        c_in = data[:, 5]  # mg/L
        c_out = data[:, 6]  # mg/L
        temp = data[:, 7]  # ℃

        # 修正L的计算：考虑升到立方米的转换
        L = (V_水 * 0.001) * self.ρ_水 / (self.M_H2O * 3600)  # mol/s
        G = V_空 * 1.29 / 29e-3 / 3600  # mol/s
        m = self.oxygen_solubility(temp) / (101325 + 0.5 * ΔP * 9.8)

        # 传质系数计算
        x_in = (c_in * 1e-3 / self.M_O2) / (
            self.ρ_水 / self.M_H2O + c_in * 1e-3 / self.M_O2
        )
        x_out = (c_out * 1e-3 / self.M_O2) / (
            self.ρ_水 / self.M_H2O + c_out * 1e-3 / self.M_O2
        )
        Kxa = (
            L
            * (x_in - x_out)
            / (
                np.pi
                * (self.D / 2) ** 2
                * self.Z
                * self._log_mean_delta(x_in, x_out, m)
            )
        )

        return {"L": L, "G": G, "Kxa": Kxa, "csv_file": csv_file}

    def _log_mean_delta(self, x1, x2, m):
        delta1 = x1 - 0.21 / m
        delta2 = x2 - 0.21 / m
        return (delta1 - delta2) / np.log(delta1 / delta2)

    def calc_all_files(self):
        for csv_file in self.required_files:
            try:
                self.results.append(self.analyze_file(csv_file))
            except Exception as e:
                print(f"计算文件 {csv_file} 时出错: {str(e)}")


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

        # 填料塔实验计算
        tower_calc = Packed_Tower_Calculator(data_loader)
        tower_calc.calc_all_files()
        print("填料塔实验计算完成")

        # 氧解吸实验计算
        oxygen_calc = Oxygen_Desorption_Calculator(data_loader)
        oxygen_calc.calc_all_files()
        print("氧解吸实验计算完成")

    except FileNotFoundError as e:
        print(f"文件验证错误: {str(e)}")
        print("请检查文件路径配置")
    except Exception as e:
        print(f"运行时错误: {str(e)}")
