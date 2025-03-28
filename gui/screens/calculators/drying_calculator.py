# drying_calculator.py

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


class Drying_Calculator:
    def __init__(self, csv_file_paths):
        """初始化计算器，直接传入CSV文件路径列表"""
        self.csv_file_paths = csv_file_paths
        self.results = {}  # 存储计算结果的字典

        # 核心计算参数（通过load_data()初始化）
        self.m_1 = None  # 毛毡润湿前质量 (kg)
        self.m_2 = None  # 毛毡润湿后质量 (kg)
        self.W2 = None  # 托架质量 (kg)
        self.G_prime = None  # 绝干质量 (kg)
        self.ΔP = None  # 压差 (Pa)
        self.τ = None  # 时间序列（小时）
        self.W1 = None  # 总质量序列 (kg)
        self.t = None  # 干球温度序列 (℃)
        self.tw = None  # 湿球温度序列 (℃)

        # 中间计算结果（通过preprocess_data()生成）
        self.G = None  # 湿物料总质量 (kg)
        self.X = None  # 干基含水量 (kg/kg)
        self.τ_bar = None  # 平均时间点 (小时)
        self.X_bar = None  # 平均干基含水量 (kg/kg)
        self.U = None  # 干燥速率 (kg/m²·h)
        self.U_c = None  # 恒定干燥速率 (kg/m²·h)

        # 高级计算结果（通过further_calculations()生成）
        self.α = None  # 传热系数 (kW/m²·K)
        self.V_t0 = None  # 初始体积流量 (m³/s)
        self.V_t = None  # 温度修正后的体积流量 (m³/s)

        # 常数定义
        self.r_tw = 2490  # 水的汽化潜热 (kJ/kg)
        self.S = 2.64e-2  # 干燥面积 (m²)

    def load_data(self):
        """从文件路径列表加载CSV数据"""
        # 根据文件名识别数据文件
        data1_path, data2_path = None, None
        for path in self.csv_file_paths:
            filename = os.path.basename(path).lower()  # 统一小写比较
            if "原始数据1" in filename:
                data1_path = path
            elif "原始数据2" in filename:
                data2_path = path

        if not all([data1_path, data2_path]):
            raise ValueError("未找到原始数据1和原始数据2文件")

        # 读取原始数据1.csv
        df1 = pd.read_csv(data1_path, header=None, skiprows=0)
        data1 = df1.iloc[:, 1].values.astype(float)

        # 提取静态参数
        self.m_1 = data1[0] * 1e-3  # 转换为kg
        self.m_2 = data1[1] * 1e-3
        self.W2 = data1[2] * 1e-3
        self.G_prime = data1[3] * 1e-3
        self.ΔP = data1[4]

        # 读取原始数据2.csv
        df2 = pd.read_csv(data2_path, header=0, skiprows=[1])

        # 提取时间序列数据
        self.τ = df2["累计时间τ/min"].values.astype(float) / 60  # 转换为小时
        self.W1 = df2["总质量W1/g"].values.astype(float) * 1e-3  # 转换为kg
        self.t = df2["干球温度t_dry/℃"].values.astype(float)
        self.tw = df2["湿球温度t_wet/℃"].values.astype(float)

    def preprocess_data(self):
        """执行核心预处理计算"""
        # 计算中间时间点
        self.τ_bar = (self.τ[:-1] + self.τ[1:]) / 2

        # 计算湿物料总质量和干基含水量
        self.G = self.W1 - self.W2
        self.X = (self.G - self.G_prime) / self.G_prime

        # 计算平均含水量和干燥速率
        self.X_bar = (self.X[:-1] + self.X[1:]) / 2
        self.U = -(self.G_prime / self.S) * (np.diff(self.X) / np.diff(self.τ))
        self.U_c = np.mean(self.U[15:])  # 取后15个点的平均值作为恒定速率

        # 存储中间结果
        self.results.update(
            {
                "ans1": np.array([self.G * 1000, self.X]).T.tolist(),
                "ans2": np.array([self.X_bar, self.U]).T.tolist(),
                "τ_bar": self.τ_bar.tolist(),
                "X_bar": self.X_bar.tolist(),
                "U": self.U.tolist(),
                "U_c": float(self.U_c),
            }
        )

    def further_calculations(self):
        """执行高级计算"""
        # 计算传热系数
        self.α = (self.U_c * self.r_tw) / (self.t - self.tw)

        # 流量计算参数
        C_0 = 0.65  # 流量系数
        A_0 = (np.pi * 0.040**2) / 4  # 流通面积 (m²)
        ρ_air = 1.29  # 空气密度 (kg/m³)
        t0 = 25  # 初始温度 (℃)

        # 体积流量计算
        self.V_t0 = C_0 * A_0 * np.sqrt(2 * self.ΔP / ρ_air)
        self.V_t = self.V_t0 * (273 + self.t) / (273 + t0)

        # 存储高级结果
        self.results.update(
            {"α": self.α.tolist(), "V_t0": float(self.V_t0), "V_t": self.V_t.tolist()}
        )

    def run_full_calculation(self):
        """执行完整计算流程"""
        self.load_data()
        self.preprocess_data()
        self.further_calculations()


# 使用示例
if __name__ == "__main__":
    # 初始化计算器时直接传入文件路径列表
    csv_files = [
        "./csv_data/干燥原始数据记录表(非)/原始数据1.csv",
        "./csv_data/干燥原始数据记录表(非)/原始数据2.csv",
    ]

    calculator = Drying_Calculator(csv_files)
    calculator.run_full_calculation()

    # 尝试访问某些计算结果
    print("恒定干燥速率 U_c:", calculator.U_c)
    print("传热系数 α:", calculator.α)
    print("初始体积流量 V_t0:", calculator.V_t0)

    # 获取完整计算结果字典
    full_results = calculator.results
    # print(full_results)
