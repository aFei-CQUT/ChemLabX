# extraction_calculator.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import logging
import pandas as pd
import numpy as np
from scipy.integrate import trapezoid
from scipy.interpolate import interp1d

# 配置日志设置
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Extraction_Calculator:
    def __init__(self, main_file, distribution_file):
        self.main_file = main_file  # 主数据CSV文件路径
        self.distribution_file = distribution_file  # 分配曲线数据CSV文件路径
        self.results = {}  # 存储处理结果

    def load_data(self):
        """
        加载主数据CSV文件，并进行初步处理。
        """
        # 读取主数据CSV文件
        df1 = pd.read_csv(self.main_file, header=None)
        self.data1 = df1.iloc[1:, 1:].values.astype(float)  # 提取数据部分并转换为浮点数

        # 提取各列数据
        self.n = self.data1[0]  # 实验编号
        self.Vs_S = self.data1[1]  # 溶剂流量 (L/h)
        self.Vs_B = self.data1[2]  # 萃取剂流量 (L/h)
        self.t = self.data1[3]  # 时间
        self.c_NaOH = 0.01  # NaOH浓度
        self.V_to_be_titrated = self.data1[[4, 6, 8], :]  # 待滴定体积
        self.V_NaOH_used = self.data1[[5, 7, 9], :]  # NaOH使用体积

        # 分子量和密度
        self.M_A, self.M_B, self.M_S = 78, 122, 18  # 分子量 (kg/kmol)
        self.ρ_A, self.ρ_B, self.ρ_S = 876.7, 800, 1000  # 密度 (kg/m^3)

    def preprocess_data(self):
        """
        数据预处理，计算相关参数。
        """
        self.Vs_B_rect = self.Vs_S * np.sqrt(
            self.ρ_S * (7900 - self.ρ_B) / (self.ρ_B * (7900 - self.ρ_S))
        )

        self.ans1 = (self.c_NaOH * self.V_NaOH_used * 1e-6 * self.M_B) / (
            self.ρ_B * self.V_to_be_titrated * 1e-6
        )
        self.X_Rb, self.X_Rt, self.Y_Eb = self.ans1[0], self.ans1[1], self.ans1[2]

        self.B = self.ρ_B * self.Vs_B * 1e-3  # 萃取剂体积 (m^3)
        self.S = self.ρ_S * self.Vs_S * 1e-3  # 溶剂体积 (m^3)
        self.B_rect = self.ρ_B * self.Vs_B_rect * 1e-3  # 校正后的萃取剂体积 (m^3)

        self.ans2 = np.array([self.B, self.S, self.B_rect])
        self.results.update(
            {
                "ans1": self.ans1.tolist(),
                "ans2": self.ans2.tolist(),
                "X_Rb": self.X_Rb.tolist(),
                "X_Rt": self.X_Rt.tolist(),
                "Y_Eb": self.Y_Eb.tolist(),
            }
        )

    def load_distribution_curve_data(self):
        """
        加载分配曲线数据CSV文件。
        """
        df3 = pd.read_csv(self.distribution_file, header=None)
        data3 = df3.iloc[2:, :].values  # 跳过前两行
        self.X3_data = data3[:, 0].astype(float)
        self.Y3_data = data3[:, 1].astype(float)

    def fit_distribution_curve(self):
        """
        拟合分配曲线。
        """
        order = 3  # 多项式阶数
        self.coefficients = np.polyfit(self.X3_data, self.Y3_data, order)
        self.X3_to_fit = np.linspace(min(self.X3_data), max(self.X3_data), 100)
        self.Y_fitted = np.polyval(self.coefficients, self.X3_to_fit)

        self.results.update(
            {
                "X3_data": self.X3_data.tolist(),
                "Y3_data": self.Y3_data.tolist(),
                "coefficients": self.coefficients.tolist(),
                "X3_to_fit": self.X3_to_fit.tolist(),
                "Y_fitted": self.Y_fitted.tolist(),
            }
        )

    def calculate_operating_lines(self):
        """
        计算操作线方程。
        """
        self.k1 = (0 - self.Y_Eb[0]) / (self.X_Rt[0] - self.X_Rb[0])
        self.b1 = self.Y_Eb[0] - self.k1 * self.X_Rb[0]

        self.k2 = (0 - self.Y_Eb[1]) / (self.X_Rt[1] - self.X_Rb[1])
        self.b2 = self.Y_Eb[1] - self.k2 * self.X_Rb[1]

        self.results.update(
            {
                "k1": float(self.k1),
                "b1": float(self.b1),
                "k2": float(self.k2),
                "b2": float(self.b2),
            }
        )

    def perform_graphical_integration(self):
        """
        执行图解积分。
        """
        self.integral_values = []  # 用于存储每个实验组的积分结果
        self.data5_for_graph_integral = []  # 用于存储每组绘图数据

        k = np.array([self.k1, self.k2])
        b = np.array([self.b1, self.b2])

        for i in range(len(self.Y_Eb)):
            Y5_Eb_data = np.linspace(0, self.Y_Eb[i], 20)
            X_Rb_data = (Y5_Eb_data - b[i]) / k[i]
            Y5star_data = np.polyval(self.coefficients, X_Rb_data)
            one_over_Y5star_minus_Y5 = 1 / (Y5star_data - Y5_Eb_data)

            # 将当前实验组的数据存入列表
            self.data5_for_graph_integral.append(
                [Y5_Eb_data, X_Rb_data, Y5star_data, one_over_Y5star_minus_Y5]
            )

            # 插值平滑曲线
            interp_func = interp1d(Y5_Eb_data, one_over_Y5star_minus_Y5, kind="cubic")
            Y5_Eb_data_smooth = np.linspace(Y5_Eb_data.min(), Y5_Eb_data.max(), 40)
            one_over_Y5star_minus_Y5_smooth = interp_func(Y5_Eb_data_smooth)

            # 计算积分并保存
            integral_value = trapezoid(
                one_over_Y5star_minus_Y5_smooth, Y5_Eb_data_smooth
            )
            self.integral_values.append(integral_value)

        # 保存积分结果到ans3
        self.ans3 = np.array(self.integral_values)
        self.results["ans3"] = self.ans3.tolist()

    def print_results(self):
        """
        打印计算结果。
        """
        print("\n========== 萃取计算结果 ==========")
        print(f"\n1. 浓度计算结果 (ans1):")
        print(f"X_Rb (萃余相苯甲酸浓度): {self.X_Rb}")
        print(f"X_Rt (萃余相苯甲酸浓度): {self.X_Rt}")
        print(f"Y_Eb (萃取相苯甲酸浓度): {self.Y_Eb}")

        print(f"\n2. 体积计算结果 (ans2):")
        print(f"萃取剂体积 B (m³): {self.B}")
        print(f"溶剂体积 S (m³): {self.S}")
        print(f"校正后的萃取剂体积 B_rect (m³): {self.B_rect}")

        print(f"\n3. 分配曲线拟合系数:")
        print(f"多项式系数: {self.coefficients}")

        print(f"\n4. 操作线参数:")
        print(f"操作线1 - 斜率 k1: {self.k1:.4f}, 截距 b1: {self.b1:.4f}")
        print(f"操作线2 - 斜率 k2: {self.k2:.4f}, 截距 b2: {self.b2:.4f}")

        print(f"\n5. 图解积分结果 (ans3)已计算完成")
        print("\n=================================")

    def run_calculations(self):
        """
        运行完整计算流程。
        """
        self.load_data()
        self.preprocess_data()
        self.load_distribution_curve_data()
        self.fit_distribution_curve()
        self.calculate_operating_lines()
        self.perform_graphical_integration()
        self.print_results()


if __name__ == "__main__":
    main_csv = "./1_原始数据记录.csv"
    distribution_csv = "./3_分配曲线数据集.csv"

    print("开始萃取计算...")
    calculator = Extraction_Calculator(main_csv, distribution_csv)
    calculator.run_calculations()

    # 获取结果示例
    results = calculator.results
    ans1 = calculator.ans1
    ans2 = calculator.ans2
    ans3 = calculator.ans3
