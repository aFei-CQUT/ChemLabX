# filteration_calculator.py

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
from sklearn.linear_model import LinearRegression


class Filteration_Calculator:
    """
    负责过滤实验数据的计算部分，包括数据加载、拟合、异常值检测等
    """

    def __init__(self, csv_file_path):
        """
        初始化类，接收CSV文件路径，并加载数据
        :param csv_file_path: CSV文件路径
        """
        self.csv_file_path = csv_file_path
        self.data = self.load_csv_data(self.csv_file_path)  # 自动加载数据

        # 初始化用于存储处理后的数据的列表
        self.q_to_refit_lists = []
        self.delta_theta_over_delta_q_to_refit_lists = []
        self.refit_slopes = []
        self.refit_intercepts = []

        # 存储额外的中间变量，用于调试/检查
        self.selected_data = None
        self.data_array = None
        self.deltaV = 9.446e-4
        self.S = 0.0475
        self.deltaQ = self.deltaV / self.S
        self.delta_theta_list = None
        self.delta_q_list = None
        self.delta_theta_over_delta_q_list = None
        self.q_list = None
        self.q_to_fit = None
        self.delta_theta_over_delta_q_to_fit = None
        self.fit_model = None
        self.fit_data = None
        self.fit_slope = None
        self.fit_intercept = None
        self.outliers = None
        self.refit_model = None
        self.filtered_data = None

    def load_csv_data(self, csv_file_path):
        """
        加载CSV文件并进行数据预处理
        :param csv_file_path: CSV文件路径
        :return: 处理后的数据
        """
        data = pd.read_csv(csv_file_path, header=0)
        for col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        data = data.dropna()  # 删除任何含有NaN值的行
        return data

    def perform_linear_fit(self, x, y):
        """
        对数据进行线性拟合
        :param x: 自变量
        :param y: 因变量
        :return: 拟合模型和拟合数据
        """
        fit_data = np.column_stack((x, y))
        model = LinearRegression()
        model.fit(fit_data[:, 0].reshape(-1, 1), fit_data[:, 1])
        return model, fit_data

    def detect_outliers(self, fit_data, threshold=2):
        """
        检测异常值
        :param fit_data: 拟合数据
        :param threshold: 异常值阈值
        :return: 异常值索引
        """
        z_scores = np.abs(
            (fit_data[:, 1] - np.mean(fit_data[:, 1])) / np.std(fit_data[:, 1])
        )
        outliers = np.where(z_scores > threshold)[0]
        return outliers

    def refit_data_after_outlier_removal(self, fit_data, outliers):
        """
        移除异常值后重新拟合数据
        :param fit_data: 拟合数据 (should be 2D array)
        :param outliers: 异常值索引
        :return: 新的拟合模型和清洗后的数据
        """
        if len(outliers) > 0:
            # 确保异常值不是空的
            filtered_data = np.delete(fit_data, outliers, axis=0)
        else:
            # 如果没有异常值，直接使用原始数据
            filtered_data = fit_data

        if filtered_data.shape[0] == 0:
            raise ValueError("去除异常值后数据为空")

        x = filtered_data[:, 0].reshape(-1, 1)
        y = filtered_data[:, 1]
        model = LinearRegression()
        model.fit(x, y)
        return model, filtered_data

    def process_single_group_data(self, group_index):
        """
        处理单组数据
        :param group_index: 组索引
        :return: 拟合所需的数据
        """
        self.selected_data = self.data.iloc[
            0:11, 1 + 3 * group_index : 4 + 3 * group_index
        ]
        self.data_array = self.selected_data.values
        self.data_array[:, 0] = self.data_array[:, 0] / 100  # 转换为标准单位

        self.delta_theta_list = np.diff(self.data_array[:, 1])
        self.delta_q_list = np.full(len(self.delta_theta_list), self.deltaQ)
        self.delta_theta_over_delta_q_list = self.delta_theta_list / self.delta_q_list

        self.q_list = np.linspace(
            0, len(self.delta_theta_list) * self.deltaQ, len(self.delta_theta_list) + 1
        )
        self.q_to_fit = (self.q_list[:-1] + self.q_list[1:]) / 2
        self.delta_theta_over_delta_q_to_fit = self.delta_theta_over_delta_q_list

        return (
            self.q_to_fit,
            self.delta_theta_over_delta_q_to_fit,
            self.delta_theta_over_delta_q_list,
            self.q_list,
        )

    def process_all_groups(self):
        """
        处理所有组数据并生成拟合数据
        :return: 返回拟合图的q值和Δθ/Δq值
        """
        # 重置列表以保存数据
        self.q_to_refit_lists = []
        self.delta_theta_over_delta_q_to_refit_lists = []
        self.refit_slopes = []
        self.refit_intercepts = []

        for group_index in range(3):
            (
                self.q_to_fit,
                self.delta_theta_over_delta_q_to_fit,
                self.delta_theta_over_delta_q_list,
                self.q_list,
            ) = self.process_single_group_data(group_index)

            self.fit_model, self.fit_data = self.perform_linear_fit(
                self.q_to_fit, self.delta_theta_over_delta_q_to_fit
            )
            self.fit_slope = self.fit_model.coef_[0]
            self.fit_intercept = self.fit_model.intercept_

            print(f"第{group_index+1}组数据初拟合结果:")
            print("初拟合斜率:", self.fit_slope)
            print("初拟合截距:", self.fit_intercept)

            self.outliers = self.detect_outliers(self.fit_data)
            if len(self.outliers) > 0:
                self.refit_model, self.filtered_data = (
                    self.refit_data_after_outlier_removal(self.fit_data, self.outliers)
                )
                self.refit_slope = self.refit_model.coef_[0]
                self.refit_intercept = self.refit_model.intercept_

                print(f"第{group_index+1}组数据排除异常值后重新拟合结果:")
                print("排除异常值后斜率:", self.refit_slope)
                print("排除异常值后截距:", self.refit_intercept)

                self.q_to_refit_lists.append(self.filtered_data[:, 0])
                self.delta_theta_over_delta_q_to_refit_lists.append(
                    self.filtered_data[:, 1]
                )
                self.refit_slopes.append(self.refit_slope)
                self.refit_intercepts.append(self.refit_intercept)

        return (
            self.q_to_refit_lists,
            self.delta_theta_over_delta_q_to_refit_lists,
            self.refit_slopes,
            self.refit_intercepts,
        )


if __name__ == "__main__":
    # 初始化Filteration_Calculator实例，传入文件路径
    filteration_calculator = Filteration_Calculator(r"./过滤原始数据记录表(非).csv")

    # 处理所有组数据并获取结果
    (
        q_to_refit_lists,
        delta_theta_over_delta_q_to_refit_lists,
        refit_slopes,
        refit_intercepts,
    ) = filteration_calculator.process_all_groups()

    # 输出处理后的数据以供验证
    print("q_to_refit_lists:", q_to_refit_lists)
    print(
        "delta_theta_over_delta_q_to_refit_lists:",
        delta_theta_over_delta_q_to_refit_lists,
    )
    print("refit_slopes:", refit_slopes)
    print("refit_intercepts:", refit_intercepts)
