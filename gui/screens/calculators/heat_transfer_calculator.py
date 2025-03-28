# heat_transfer_calculator.py

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
from scipy.optimize import curve_fit


class Heat_Transfer_Calculator:
    """
    传热计算器类。
    """

    def __init__(self, csv_file_paths):
        """
        初始化函数，加载CSV文件并读取数据集。

        参数:
        csv_file_paths (list): CSV文件路径列表
        """
        self.file_dict = self._categorize_files(csv_file_paths)  # CSV文件路径列表
        self.datasets = self.load_data()  # 加载数据集
        self.results = []  # 存储处理结果

    def _categorize_files(self, paths):
        """根据文件名分类文件"""
        file_dict = {
            "无强化套管": None,
            "有强化套管": None,
            "预处理_无": None,
            "预处理_有": None,
        }

        for path in paths:
            if "无强化套管" in path and "预处理" not in path:
                file_dict["无强化套管"] = path
            elif "有强化套管" in path and "预处理" not in path:
                file_dict["有强化套管"] = path
            elif "数据预处理_无" in path:
                file_dict["预处理_无"] = path
            elif "数据预处理_有" in path:
                file_dict["预处理_有"] = path

        missing = [k for k, v in file_dict.items() if v is None]
        if missing:
            raise ValueError(f"缺少必要文件: {missing}")
        return file_dict

    def load_data(self):
        datasets = []
        # 按类型读取文件
        for file_type in ["无强化套管", "有强化套管"]:
            file_path = self.file_dict[file_type]
            df = pd.read_csv(file_path, header=None)
            data = np.array(df.iloc[1:7, 1:4].values, dtype=float)
            datasets.append(
                {
                    "Δp_kb": data[:, 0],
                    "t_in": data[:, 1],
                    "t_out": data[:, 2],
                }
            )
        return datasets

    def preprocess_data(self, Δp_kb, t_in, t_out):
        """
        传热数据预处理，计算相关参数并生成原始数据和计算结果表格。

        参数:
        Δp_kb (numpy.ndarray): 孔板压差数据
        t_in (numpy.ndarray): 入口温度数据
        t_out (numpy.ndarray): 出口温度数据

        返回:
        ans_original_data (pd.DataFrame): 原始数据表格
        ans_calculated_data (pd.DataFrame): 计算结果表格
        data_for_fit (numpy.ndarray): 用于拟合的数据
        """
        # 计算过程
        t_w = 98.4  # 壁面温度
        d_o = 0.022  # 外径
        d_i = d_o - 2 * 0.001  # 内径
        l = 1.2  # 长度
        n = 1  # 管数
        C_0 = 0.65  # 流量系数
        S_i = np.pi * l * n * d_i  # 内表面积
        S_o = np.pi * l * n * d_o  # 外表面积
        A_i = (np.pi * d_i**2) / 4  # 内截面积
        A_0 = 2.27 * 10**-4  # 孔板面积
        t_avg = 0.5 * (t_in + t_out)  # 平均温度
        Cp = 1005  # 比热容
        ρ = (t_avg**2) / 10**5 - (4.5 * t_avg) / 10**3 + 1.2916  # 密度
        λ = -(2 * t_avg**2) / 10**8 + (8 * t_avg) / 10**5 + 0.0244  # 导热系数
        μ = (-(2 * t_avg**2) / 10**6 + (5 * t_avg) / 10**3 + 1.7169) / 10**5  # 动力粘度
        Pr = (Cp * μ) / λ  # 普朗特数
        PrZeroFour = Pr**0.4  # 普朗特数的0.4次方
        V_t = 3600 * A_0 * C_0 * np.sqrt((2 * 10**3 * Δp_kb) / ρ)  # 体积流量
        V_xiu = ((t_avg + 273.15) * V_t) / (t_in + 273.15)  # 修正体积流量
        u_m = V_xiu / (3600 * A_i)  # 平均流速
        W_c = (ρ * V_xiu) / 3600  # 质量流量
        Q = Cp * W_c * (t_out - t_in)  # 热流量
        α_i = Q / (t_avg * S_i)  # 内表面换热系数
        Nu_i = (d_i * α_i) / λ  # 努塞尔数
        Re_i = (ρ * d_i * u_m) / μ  # 雷诺数
        NuOverPrZeroFour = Nu_i / Pr**0.4  # 努塞尔数与普朗特数的0.4次方之比
        Δt1 = t_w - t_in  # 温差1
        Δt2 = t_w - t_out  # 温差2
        Δt_m = (Δt2 - Δt1) / (np.log(Δt2) - np.log(Δt1))  # 平均温差
        K_o = Q / (Δt_m * S_o)  # 总传热系数

        # 创建原始数据表格
        ans_original_data = pd.DataFrame(
            {
                "序号": np.arange(1, len(Δp_kb) + 1),
                "Δp孔板/kPa": Δp_kb,
                "t入/°C": t_in,
                "t出/°C": t_out,
            }
        )

        # 创建计算结果表格
        ans_calculated_data = pd.DataFrame(
            {
                "序号": np.arange(1, len(Δp_kb) + 1),
                "Δp": Δp_kb,
                "t入": t_in,
                "t出": t_out,
                "t平": t_avg,
                "ρ": ρ,
                "λ": λ,
                "μ": μ,
                "Pr": Pr,
                "Pr^0.4": PrZeroFour,
                "V_t": V_t,
                "V修": V_xiu,
                "u_m": u_m,
                "W_c": W_c,
                "Q": Q,
                "α_i": α_i,
                "Nu_i": Nu_i,
                "Re_i": Re_i,
                "Nu/Pr^0.4": NuOverPrZeroFour,
                "Δt1": Δt1,
                "Δt2": Δt2,
                "Δt_m": Δt_m,
                "K_o": K_o,
            }
        ).T

        # 准备用于拟合的数据
        data_for_fit = np.array([Re_i, NuOverPrZeroFour]).T

        return ans_original_data, ans_calculated_data, data_for_fit

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

    def process_data(self):
        """
        处理数据集，进行数据预处理和曲线拟合。
        """
        for idx, dataset in enumerate(self.datasets):
            Δp_kb = dataset["Δp_kb"]
            t_in = dataset["t_in"]
            t_out = dataset["t_out"]

            ans_original_data, ans_calculated_data, data_for_fit = self.preprocess_data(
                Δp_kb, t_in, t_out
            )

            # 检查并过滤掉非正值
            valid_indices = (data_for_fit[:, 0] > 0) & (data_for_fit[:, 1] > 0)
            valid_data = data_for_fit[valid_indices]

            if len(valid_data) > 0:
                ans_params, _ = curve_fit(
                    self.fit_func,
                    np.log10(valid_data[:, 0]),
                    np.log10(valid_data[:, 1]),
                )
            else:
                print(f"警告：数据集 {idx+1} 没有有效的正值用于拟合。")
                ans_params = None

            self.results.append(
                {
                    "original_data": ans_original_data,
                    "calculated_data": ans_calculated_data,
                    "data_for_fit": valid_data,
                    "params": ans_params,
                }
            )

    def print_results(self):
        """
        打印输出results字典的calculated_data键值。
        """
        # 设置显示选项
        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_rows", None)

        for idx, result in enumerate(self.results):
            print(f"数据集 {idx+1} 的计算结果:")
            print(result["calculated_data"])


# 使用示例
if __name__ == "__main__":
    # 定义CSV文件路径列表
    csv_file_paths = [
        "./csv_data/传热/传热原始数据记录表(非)/原始数据_无强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/原始数据_有强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/数据预处理_无强化套管.csv",
        "./csv_data/传热/传热原始数据记录表(非)/数据预处理_有强化套管.csv",
    ]

    # 实例化传热计算器
    heat_transfer_calculator = Heat_Transfer_Calculator(csv_file_paths)

    # 加载数据
    datasets = heat_transfer_calculator.load_data()

    # 数据处理
    heat_transfer_calculator.process_data()

    # 打印结果
    heat_transfer_calculator.print_results()
