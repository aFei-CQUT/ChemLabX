# fluid_flow_calculator.py

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
import os


class Fluid_Flow_Calculator:
    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.ans1 = None
        self.df = None
        self.p = None
        self.log_Re = None
        self.log_λ = None
        self.valid_idx = None

    def process(self):
        """进行流体流动分析，包括计算雷诺数和摩擦系数，并进行双对数拟合"""
        # 已知参数
        d = 0.008  # 管径(m)
        l = 1.70  # 管长(m)
        ρ = 996.5  # 水的密度(kg/m^3)
        g = 9.81  # 重力加速度(m/s^2)
        μ = 8.55e-4  # 粘性系数(Pa·s)

        # 从CSV读取数据（跳过前两行标题和单位行）
        df = pd.read_csv(self.file_dir, skiprows=2, header=None)

        # 处理非数值数据（将非数值转为NaN后填充0）
        df[1] = pd.to_numeric(df[1], errors="coerce").fillna(0)  # Q列
        df[2] = pd.to_numeric(df[2], errors="coerce").fillna(0)  # 直管阻力压降
        df[3] = pd.to_numeric(df[3], errors="coerce").fillna(0)  # mmH2O列

        # 提取数据
        Q = df.iloc[:, 1].values / 3600 / 1000  # 转换L/h → m³/s

        # 构造压降数组（前9个为kPa数据，后10个为mmH2O数据）
        ΔPf = np.concatenate(
            [
                1000 * df.iloc[:9, 2].values,
                ρ * g * df.iloc[9:, 3].values / 1000,
            ]  # kPa → Pa  # mmH2O → Pa
        )

        # 计算流速(m/s)
        u = Q / (np.pi / 4 * d**2)

        # 计算雷诺数
        Re = (d * u * ρ) / μ

        # 计算摩擦系数（避免除以零）
        valid_u = np.where(u != 0, u, 1e-10)  # 替换零值为极小值
        λ = (2 * d) / (ρ * l) * ΔPf / valid_u**2

        # 双对数拟合（过滤无效值）
        valid_idx = (Re > 0) & (λ > 0)
        log_Re = np.log10(Re[valid_idx])
        log_λ = np.log10(λ[valid_idx])

        degree = 9
        coefficients = np.polyfit(log_Re, log_λ, degree)
        p = np.poly1d(coefficients)

        # 保存结果到实例变量
        self.ans1 = np.column_stack((u, Re, λ))
        self.df = df
        self.p = p
        self.log_Re = log_Re
        self.log_λ = log_λ
        self.valid_idx = valid_idx
        return self.ans1, self.df


class Centrifugal_Pump_Characteristics_Calculator:
    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.ans2 = None
        self.df = None
        self.params_H = None
        self.params_N = None
        self.params_η = None

    @staticmethod
    def quadratic(x, a, b, c):
        return a * x**2 + b * x + c

    def process(self):
        """分析离心泵特性曲线，包括扬程、功率和效率的计算与二次拟合"""
        # 从CSV读取数据（跳过标题行）
        df = pd.read_csv(self.file_dir, skiprows=1, header=None)

        # 处理非数值数据
        for col in [1, 2, 3, 4]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # 提取数据
        Q = df.iloc[:, 1].values  # 流量(m³/h)
        p_in = df.iloc[:, 2].values  # 入口压力(MPa)
        p_out = df.iloc[:, 3].values  # 出口压力(MPa)
        N_elc = df.iloc[:, 4].values  # 电机功率(kW)

        # 已知参数
        ρ = 995.7  # 水的密度(kg/m^3)
        g = 9.81  # 重力加速度(m/s²)
        Δz = 0.23  # 高度差(m)
        η_elc = 0.6  # 电机效率

        # 计算扬程（压力单位MPa → Pa）
        H = Δz + ((p_out - p_in) * 1e6) / (ρ * g)

        # 计算有效功率（kW → W）
        N_elc_e = N_elc * η_elc * 1000

        # 计算流体有效功率（Q单位m³/h → m³/s）
        N_e = H * Q / 3600 * ρ * g

        # 计算效率（避免除以零）
        valid_N = np.where(N_elc_e != 0, N_elc_e, 1e-10)
        η = N_e / valid_N

        # 二次拟合
        params_H, _ = curve_fit(self.quadratic, Q, H)
        params_N, _ = curve_fit(self.quadratic, Q, N_elc_e)
        params_η, _ = curve_fit(self.quadratic, Q, η)

        # 保存结果到实例变量
        self.ans2 = np.column_stack((H, N_elc_e, η))
        self.df = df
        self.params_H = params_H
        self.params_N = params_N
        self.params_η = params_η
        return self.ans2, self.df, self.params_H, self.params_N, self.params_η


class Auxiliary:
    def __init__(self, file_paths):
        self.file_paths = file_paths
        self.results = {}

    def identify_file_type(self, file_path):
        """根据文件名识别文件类型"""
        file_name = os.path.basename(file_path)
        if "流体阻力" in file_name:
            return "fluid"
        elif "离心泵" in file_name:
            return "pump"
        else:
            raise ValueError(f"无法识别文件类型: {file_name}")

    def process_files(self):
        """处理所有文件"""
        for file_path in self.file_paths:
            try:
                file_type = self.identify_file_type(file_path)
                if file_type == "fluid":
                    calculator = Fluid_Flow_Calculator(file_path)
                    ans, df = calculator.process()
                    self.results["fluid"] = {"ans": ans, "df": df}
                elif file_type == "pump":
                    calculator = Centrifugal_Pump_Characteristics_Calculator(file_path)
                    ans, df, params_H, params_N, params_η = calculator.process()
                    self.results["pump"] = {
                        "ans": ans,
                        "df": df,
                        "params_H": params_H,
                        "params_N": params_N,
                        "params_η": params_η,
                    }
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {str(e)}")

    def get_results(self):
        """获取处理结果"""
        return self.results


if __name__ == "__main__":
    # 文件路径列表
    file_paths = [
        "./csv_data/流体/流体原始数据记录表(非)/流体阻力原始数据.csv",
        "./csv_data/流体/流体原始数据记录表(非)/离心泵原始数据.csv",
    ]

    # 确保输出目录存在
    os.makedirs("./拟合图结果", exist_ok=True)

    # 创建Auxiliary实例并处理文件
    processor = Auxiliary(file_paths)
    processor.process_files()

    # 获取结果
    results = processor.get_results()

    # 打印结果字典的键
    print("处理完成，结果字典包含以下键:", results.keys())
