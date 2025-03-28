# distillation_calculator.py

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
import sympy


class Distillation_Calculator:
    """
    精馏塔计算器类，用于计算精馏塔理论板数及相关参数

    主要功能：
    - 读取实验数据文件（CSV格式）
    - 计算进料热状态参数
    - 求解物料平衡方程
    - 计算气液相平衡关系
    - 绘制操作线并计算理论塔板数
    """

    def __init__(self, file_path, R, αm, F, tS, tF):
        """
        初始化精馏计算器

        参数:
        ----------
        file_path : str
            包含实验数据的CSV文件路径
        R : float
            回流比(Reflux Ratio)
        αm : float
            平均相对挥发度
        F : float
            进料流量(mol/h)
        tS : float
            泡点温度(°C)
        tF : float
            进料温度(°C)

        处理流程:
        1. 读取实验数据
        2. 设置物性常数
        3. 计算进料参数
        4. 计算各组分组成
        5. 求解物料平衡
        6. 计算理论塔板数
        """

        # 文件路径
        self.file_path = file_path

        # 从CSV读取实验数据（处理BOM头）
        self.df = pd.read_csv(file_path, header=0, encoding="utf-8-sig")

        # 初始化输入参数
        self.R = R
        self.αm = αm
        self.F = F
        self.tS = tS
        self.tF = tF

        # 初始化结果字典
        self.results = {}  # 添加这一行

        # 执行计算流程
        self.set_constants()
        self.calculate_feed_parameters()
        self.calculate_compositions()
        self.solve_material_balance()
        self.calculate_stages()

        # 将关键结果存储到 results 字典中
        self.results = {
            "回流比": self.R,
            "进料热状态参数": self.q,
            "馏出液组成": self.xD,
            "釜残液组成": self.xW,
            "馏出液流量": self.D,
            "釜残液流量": self.W,
            "理论塔板数": self.NT,
            "各理论板组成": list(zip(self.xn, self.yn)),
            "Q点坐标": (self.xQ, self.yQ),
        }

    def set_constants(self):
        """设置乙醇-水体系的物性常数"""
        # 密度 (g/mL)
        self.ρA, self.ρB = 0.789, 1.0  # 乙醇, 水

        # 比热容 (J/(g·°C))
        self.cA, self.cB = 2.4e3, 4.189e3  # 乙醇, 水

        # 摩尔汽化热 (kJ/kg)
        self.rA, self.rB = 850, 2260  # 乙醇, 水

        # 摩尔质量 (g/mol)
        self.MA, self.MB = 46, 18  # 乙醇, 水

        # 进料摩尔分数 (假设值)
        self.xA, self.xB = 0.1, 0.9  # 乙醇, 水

    def calculate_feed_parameters(self):
        """计算进料热状态参数q"""
        # 计算平均比热容 (J/(mol·°C))
        self.cpm = self.xA * self.cA * self.MA + self.xB * self.cB * self.MB

        # 计算平均汽化热 (J/mol)
        self.rm = self.xA * self.rA * self.MA + self.xB * self.rB * self.MB

        # 计算q值(进料热状态参数)
        if self.tS:  # 如果有泡点温度数据
            self.q = (self.cpm * (self.tS - self.tF) + self.rm) / self.rm
        else:  # 缺省值处理
            self.q = 1.5  # 假设为过热蒸气进料

    def calculate_x_ethanol(self, s):
        """
        将体积分数转换为摩尔分数

        参数:
        s : float
            乙醇体积分数(%)

        返回:
        float
            乙醇摩尔分数
        """
        # 将体积百分比转换为小数
        s /= 100

        # 计算各组分的摩尔数
        moles_A = s * self.ρA / self.MA  # 乙醇摩尔数
        moles_B = (1 - s) * self.ρB / self.MB  # 水摩尔数

        # 计算摩尔分数
        return moles_A / (moles_A + moles_B)

    def calculate_compositions(self):
        """从实验数据计算各关键组分组成"""
        # 全回流条件(R=∞)下的组成
        self.xD_inf = self.calculate_x_ethanol(self.df.loc[0, "20°C酒精度(查表)/°"])
        self.xW_inf = self.calculate_x_ethanol(self.df.loc[1, "20°C酒精度(查表)/°"])

        # 正常回流条件(R=4)下的组成
        self.xD = self.calculate_x_ethanol(self.df.loc[2, "20°C酒精度(查表)/°"])
        self.xW = self.calculate_x_ethanol(self.df.loc[3, "20°C酒精度(查表)/°"])

        # 进料液组成
        self.xF = self.calculate_x_ethanol(self.df.loc[4, "20°C酒精度(查表)/°"])

    def solve_material_balance(self):
        """求解全塔物料平衡方程"""
        if self.R >= 10000:  # 全回流情况处理
            self.D = 0.0  # 馏出液量为0
            self.W = self.F  # 釜残液量等于进料量
            self.L = self.R * self.D  # 实际此时L趋近无穷大
        else:  # 正常情况求解
            # 建立矩阵方程：
            # [1    1  ] [D]   [F]
            # [xD  xW  ] [W] = [F * xF]
            A = sympy.Matrix([[1, 1], [self.xD, self.xW]])
            b = sympy.Matrix([self.F, self.xF * self.F])

            # 解线性方程组
            solution = A.solve(b)
            self.D, self.W = solution[0], solution[1]

            # 计算回流液量
            self.L = self.R * self.D

    def y_e(self, x):
        """
        气液平衡方程(y与x的关系)

        参数:
        x : float
            液相中乙醇的摩尔分数

        返回:
        float
            气相中乙醇的摩尔分数
        """
        return self.αm * x / (1 + (self.αm - 1) * x)

    def x_e(self, y):
        """
        反平衡方程(x与y的关系)

        参数:
        y : float
            气相中乙醇的摩尔分数

        返回:
        float
            液相中乙醇的摩尔分数
        """
        return y / (self.αm - (self.αm - 1) * y)

    def y_np1(self, x):
        """
        精馏段操作线方程

        参数:
        x : float
            第n块板液相组成

        返回:
        float
            第n+1块板气相组成
        """
        return (self.R / (self.R + 1)) * x + self.xD / (self.R + 1)

    def y_mp1(self, x):
        """
        提馏段操作线方程

        参数:
        x : float
            第m块板液相组成

        返回:
        float
            第m+1块板气相组成
        """
        numerator = self.L + self.q * self.F
        denominator = numerator - self.W
        return (numerator / denominator) * x - (self.W * self.xW) / denominator

    def y_q(self, x):
        """
        q线方程(进料方程)

        参数:
        x : float
            液相组成

        返回:
        float
            对应的气相组成
        """
        if self.q == 1:  # 泡点进料
            return x
        else:
            return (self.q / (self.q - 1)) * x - (self.xF / (self.q - 1))

    def calculate_stages(self):
        """通过逐板计算法确定理论塔板数"""
        # 根据回流比选择计算模式
        if self.R >= 10000:  # 全回流模式
            xD = self.xD_inf
            xW = self.xW_inf
        else:  # 正常操作模式
            xD = self.xD
            xW = self.xW

        # 计算两操作线交点Q的坐标
        self.xQ = ((self.R + 1) * self.xF + (self.q - 1) * xD) / (self.R + self.q)
        self.yQ = (self.R * self.xF + self.q * xD) / (self.R + self.q)

        # 初始化迭代变量
        yn = np.array([xD])  # 从塔顶开始计算
        xn = np.array([])  # 存储各板液相组成
        max_iterations = 20  # 防止无限循环
        iteration = 0

        # 逐板计算循环
        while self.x_e(yn[-1]) > xW and iteration < max_iterations:
            iteration += 1

            # 计算当前板的液相组成
            xn = np.append(xn, self.x_e(yn[-1]))

            # 判断使用哪条操作线
            if xn[-1] > self.xQ:  # 在精馏段
                new_y = self.y_np1(xn[-1])
            else:  # 进入提馏段
                new_y = self.y_mp1(xn[-1])

            yn = np.append(yn, new_y)

        # 记录最终液相组成
        xn = np.append(xn, self.x_e(yn[-1]))

        # 计算结果整理
        self.NT = len(xn)  # 总理论板数(包括再沸器)
        self.xn, self.yn = xn, yn  # 保存各板组成

    def save_results(self, filename):
        """将关键结果保存至文本文件"""
        results = []
        results.append("--- Q点坐标 ---")
        results.append(f"xQ: {self.xQ:.4f}")
        results.append(f"yQ: {self.yQ:.4f}")

        results.append("\n--- 各理论板组成 ---")
        for i, (x, y) in enumerate(zip(self.xn, self.yn)):
            results.append(f"第{i}块板: xn = {x:.4f}, yn = {y:.4f}")

        results.append(f"\n总理论板数(包括再沸器): {self.NT}")

        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:  # 直接使用完整路径
            f.write("\n".join(results))


def process_and_save(file_path, R, αm, F, tS, tF, filename):
    """处理并保存结果的辅助函数"""
    try:
        # 创建计算器实例
        calculator = Distillation_Calculator(
            file_path=file_path, R=R, αm=αm, F=F, tS=tS, tF=tF
        )

        # 打印关键结果
        print("\n精馏塔计算结果:")
        print(f"回流比 R: {R}")
        print(f"进料热状态参数 q: {calculator.q:.3f}")
        print(f"馏出液组成 xD: {calculator.xD:.4f}")
        print(f"釜残液组成 xW: {calculator.xW:.4f}")
        print(f"馏出液流量 D: {calculator.D:.2f} mol/h")
        print(f"釜残液流量 W: {calculator.W:.2f} mol/h")
        print(f"理论塔板数 NT: {calculator.NT}")

        # 保存详细结果
        results_dir = "./计算结果"
        os.makedirs(results_dir, exist_ok=True)
        results_path = f"{results_dir}/{filename}.txt"
        calculator.save_results(results_path)
        print(f"详细结果已保存至: {results_path}")

        return calculator

    except Exception as e:
        print(f"计算过程中发生错误: {str(e)}")
        return None


if __name__ == "__main__":
    # 设置文件路径 - 相对路径
    file_path = "./csv_data/精馏/精馏原始记录表(非)/Sheet1.csv"

    # 确保输出目录存在
    os.makedirs("./计算结果", exist_ok=True)

    print("=" * 50)
    print("开始精馏塔计算 (两组不同参数)")
    print("=" * 50)

    # 第一组计算: R = 4 时
    print("\n>>> 计算条件: R = 4 <<<")
    calc1 = process_and_save(
        file_path=file_path, R=4, αm=2.0, F=80, tS=30, tF=26, filename="R_4_结果"
    )

    # 第二组计算: R --> ∞时
    print("\n>>> 计算条件: R --> ∞ <<<")
    calc2 = process_and_save(
        file_path=file_path, R=10000, αm=2.0, F=80, tS=30, tF=26, filename="R_+∞_结果"
    )

    print("\n计算完成，两组结果已分别保存至计算结果目录")
