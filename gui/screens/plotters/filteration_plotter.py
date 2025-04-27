# filteration_plotter.py

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
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec  # 导入 gridspec 用于布局控制
from gui.screens.calculators.filteration_calculator import Filteration_Calculator

# 设置中文字体
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 50
plt.rcParams["savefig.dpi"] = 300


class Filteration_Plotter:
    """
    负责生成符合指定风格的图表，保持一致的绘图风格设置
    """

    def __init__(self, csv_file_path):
        """
        初始化绘图类，设置图表的默认样式，并调用计算类进行数据处理
        :param csv_file_path: CSV文件路径
        """
        self.csv_file_path = csv_file_path
        self.calculator = Filteration_Calculator(self.csv_file_path)

        # 获取计算器生成的数据
        (
            self.q_to_refit_lists,
            self.delta_theta_over_delta_q_to_refit_lists,
            self.refit_slopes,
            self.refit_intercepts,
        ) = self.calculator.process_all_groups()

        # 存储来自计算器的所有数据和变量
        self.calculator_data = {
            "data": self.calculator.data,  # 存储加载的CSV数据
            "q_to_refit_lists": self.calculator.q_to_refit_lists,
            "delta_theta_over_delta_q_to_refit_lists": self.calculator.delta_theta_over_delta_q_to_refit_lists,
            "refit_slopes": self.calculator.refit_slopes,
            "refit_intercepts": self.calculator.refit_intercepts,
            "selected_data": self.calculator.selected_data,
            "data_array": self.calculator.data_array,
            "deltaV": self.calculator.deltaV,
            "S": self.calculator.S,
            "deltaQ": self.calculator.deltaQ,
            "delta_theta_list": self.calculator.delta_theta_list,
            "delta_q_list": self.calculator.delta_q_list,
            "delta_theta_over_delta_q_list": self.calculator.delta_theta_over_delta_q_list,
            "q_list": self.calculator.q_list,
            "q_to_fit": self.calculator.q_to_fit,
            "delta_theta_over_delta_q_to_fit": self.calculator.delta_theta_over_delta_q_to_fit,
            "fit_model": self.calculator.fit_model,
            "fit_data": self.calculator.fit_data,
            "fit_slope": self.calculator.fit_slope,
            "fit_intercept": self.calculator.fit_intercept,
            "outliers": self.calculator.outliers,
            "refit_model": self.calculator.refit_model,
            "filtered_data": self.calculator.filtered_data,
        }

        # 图像路径存储变量
        self.images_paths = []

        # 设置图表风格
        plt.rcParams["font.family"] = "SimHei"
        plt.rcParams["axes.unicode_minus"] = False
        plt.rcParams["figure.dpi"] = 50
        plt.rcParams["savefig.dpi"] = 300

        # 存储图表的显示范围配置
        self.plot_ranges_initial = [
            {"x_min": 0, "x_max": 0.200, "y_min": 0, "y_max": 140000},
            {"x_min": 0, "x_max": 0.200, "y_min": 0, "y_max": 25000},
            {"x_min": 0, "x_max": 0.200, "y_min": 0, "y_max": 8000},
        ]
        self.plot_ranges_refit = [
            {"x_min": 0, "x_max": 0.200, "y_min": 0, "y_max": 15000},
            {"x_min": 0, "x_max": 0.200, "y_min": 0, "y_max": 5000},
            {"x_min": 0, "x_max": 0.200, "y_min": 0, "y_max": 4000},
        ]

    def set_axes_style(self):
        """
        设置统一的坐标轴样式
        """
        plt.gca().spines["top"].set_linewidth(2)
        plt.gca().spines["bottom"].set_linewidth(2)
        plt.gca().spines["left"].set_linewidth(2)
        plt.gca().spines["right"].set_linewidth(2)
        plt.minorticks_on()

    def save_image(self, filename):
        """
        保存生成的图像并记录路径
        :param filename: 图像保存的文件名
        """
        # 定义保存路径
        directory = "./拟合图结果"

        # 检查路径是否存在，如果不存在则创建
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 图像保存的完整路径
        image_path = os.path.join(directory, f"{filename}.png")

        # 记录图像路径
        self.images_paths.append(image_path)

        # 保存图像，添加 bbox_inches='tight' 以减少空白
        plt.savefig(image_path, bbox_inches="tight")
        plt.close()

    def add_auxiliary_lines(self, q_list, delta_theta_over_delta_q_list):
        """
        在图表中添加辅助线
        :param q_list: q值列表
        :param delta_theta_over_delta_q_list: Δθ/Δq值列表
        """
        for i in range(len(delta_theta_over_delta_q_list) - 1):
            plt.axvline(x=q_list[i], color="black", linestyle="dashed")
            plt.hlines(
                y=delta_theta_over_delta_q_list[i],
                xmin=q_list[i],
                xmax=q_list[i + 1],
                color="black",
            )
            plt.axvline(x=q_list[i + 1], color="black", linestyle="dashed")

        i = len(delta_theta_over_delta_q_list) - 1
        plt.axvline(x=q_list[i], color="black", linestyle="dashed")
        plt.hlines(
            y=delta_theta_over_delta_q_list[i],
            xmin=q_list[i],
            xmax=q_list[i],
            color="black",
        )
        plt.axvline(x=q_list[i], color="black", linestyle="dashed")

    def create_initial_fit_figure(
        self,
        group_index,
        q_to_fit,
        delta_theta_over_delta_q_to_fit,
        fit_slope,
        fit_intercept,
        q_list,
        delta_theta_over_delta_q_list,
        plot_range,
    ):
        """
        创建初拟合图表
        """
        plt.figure(figsize=(8, 6))
        plt.scatter(
            q_to_fit, delta_theta_over_delta_q_to_fit, color="red", label="拟合数据"
        )
        plt.plot(
            q_to_fit, fit_slope * q_to_fit + fit_intercept, color="blue", label="拟合线"
        )

        center_x = np.mean(q_to_fit)
        center_y = np.mean(delta_theta_over_delta_q_to_fit)
        equation_text = f"y = {fit_slope:.2f} * x + {fit_intercept:.2f}"
        plt.text(
            center_x,
            center_y,
            equation_text,
            color="black",
            fontsize=15,
            verticalalignment="top",
            weight="bold",
        )

        self.add_auxiliary_lines(q_list, delta_theta_over_delta_q_list)
        plt.xlim(plot_range["x_min"], plot_range["x_max"])
        plt.ylim(plot_range["y_min"], plot_range["y_max"])

        plt.xlabel("q 值")
        plt.ylabel("Δθ/Δq")
        plt.legend(loc="upper left")
        plt.figtext(
            0.5, 0.01, f"第{group_index+1}组数据初拟合", ha="center", fontsize=15
        )

        # 设置轴样式
        self.set_axes_style()

        # 调用自定义的 save_image 函数
        self.save_image(f"{2 * group_index + 1}")
        # plt.show()

    def create_refit_figure(
        self,
        group_index,
        filtered_data,
        refit_slope,
        refit_intercept,
        q_list,
        delta_theta_over_delta_q_list,
        plot_range,
    ):
        """
        创建重新拟合图表
        """
        plt.figure(figsize=(8, 6))
        plt.scatter(
            filtered_data[:, 0], filtered_data[:, 1], color="red", label="拟合数据"
        )
        plt.plot(
            filtered_data[:, 0],
            refit_slope * filtered_data[:, 0] + refit_intercept,
            color="blue",
            label="拟合线",
        )

        center_x = np.mean(filtered_data[:, 0])
        center_y = np.mean(filtered_data[:, 1])
        equation_text = f"y = {refit_slope:.2f} * x + {refit_intercept:.2f}"
        plt.text(
            center_x,
            center_y,
            equation_text,
            color="black",
            fontsize=15,
            verticalalignment="top",
            weight="bold",
        )

        self.add_auxiliary_lines(q_list, delta_theta_over_delta_q_list)
        plt.xlim(plot_range["x_min"], plot_range["x_max"])
        plt.ylim(plot_range["y_min"], plot_range["y_max"])

        plt.xlabel("q 值")
        plt.ylabel("Δθ/Δq")
        plt.legend(loc="upper left")
        plt.figtext(
            0.5,
            0.01,
            f"第{group_index+1}组数据排除异常值后重新拟合",
            ha="center",
            fontsize=15,
        )

        self.set_axes_style()
        self.save_image(f"{2 * group_index + 2}")
        # plt.show()

    def generate_comparison_figures(self):
        """
        生成对比图
        """
        # 初始拟合对比图
        plt.figure(figsize=(8, 6))
        for group_index in range(3):
            (
                q_to_fit,
                delta_theta_over_delta_q_to_fit,
                delta_theta_over_delta_q_list,
                q_list,
            ) = self.calculator.process_single_group_data(group_index)
            model, _ = self.calculator.perform_linear_fit(
                q_to_fit, delta_theta_over_delta_q_to_fit
            )
            fit_slope = model.coef_[0]
            fit_intercept = model.intercept_

            plt.scatter(
                q_to_fit,
                delta_theta_over_delta_q_to_fit,
                label=f"第{group_index+1}组数据",
            )
            plt.plot(
                q_to_fit,
                fit_slope * q_to_fit + fit_intercept,
                label=f"拟合线{group_index+1}",
            )
            self.add_auxiliary_lines(q_list, delta_theta_over_delta_q_list)

        plt.xlim(0, 0.200)
        plt.xlabel("q 值")
        plt.ylabel("Δθ/Δq")
        plt.legend(loc="upper left")
        plt.figtext(
            0.5, 0.01, "三组数据保留所有数据点初拟合对比", ha="center", fontsize=15
        )

        self.set_axes_style()
        self.save_image("7")
        # plt.show()

        # 重新拟合对比图
        plt.figure(figsize=(8, 6))
        for i in range(3):
            plt.scatter(
                self.q_to_refit_lists[i],
                self.delta_theta_over_delta_q_to_refit_lists[i],
                label=f"第{i+1}组数据",
            )
            plt.plot(
                self.q_to_refit_lists[i],
                self.refit_slopes[i] * self.q_to_refit_lists[i]
                + self.refit_intercepts[i],
                label=f"拟合线{i+1}",
            )
            self.add_auxiliary_lines(
                self.q_to_refit_lists[i],
                self.delta_theta_over_delta_q_to_refit_lists[i],
            )

        plt.xlim(0, 0.200)
        plt.xlabel("q 值")
        plt.ylabel("Δθ/Δq")
        plt.legend(loc="upper left")
        plt.figtext(
            0.5, 0.01, "三组数据排除异常值后再拟合对比", ha="center", fontsize=15
        )

        self.set_axes_style()
        self.save_image("8")
        # plt.show()

    def integrate_figures(self):
        """
        合并所有绘图生成的图片并保存成一张图片
        """
        images = []
        for i in range(1, 9):
            img = mpimg.imread(f"./拟合图结果/{i}.png")
            images.append(img)

        # 使用 gridspec 精确控制子图布局
        fig = plt.figure(figsize=(10, 12))
        gs = gridspec.GridSpec(4, 2, wspace=-0.20, hspace=0)  # 设置水平间距和垂直间距

        for i, img in enumerate(images):
            ax = fig.add_subplot(gs[i])
            ax.imshow(img)
            ax.axis("off")
            ax.margins(0)  # 减小子图内部边距

        plt.savefig(r"./拟合图结果/拟合图整合图.png", bbox_inches="tight")
        # plt.show()

    def generate_all_figures(self):
        """
        生成所有必要的图形。
        """
        # 1. 画三张初拟合图
        for i in range(3):
            # 正确拆解数据
            (
                q_to_fit,
                delta_theta_over_delta_q_to_fit,
                delta_theta_over_delta_q_list,
                q_list,
            ) = self.calculator.process_single_group_data(i)

            # 执行线性拟合
            model, _ = self.calculator.perform_linear_fit(
                q_to_fit, delta_theta_over_delta_q_to_fit
            )
            fit_slope = model.coef_[0]
            fit_intercept = model.intercept_

            # 创建初拟合图
            self.create_initial_fit_figure(
                i,
                q_to_fit,
                delta_theta_over_delta_q_to_fit,
                fit_slope,
                fit_intercept,
                q_list,
                delta_theta_over_delta_q_list,
                self.plot_ranges_initial[i],
            )

        # 2. 画三张再拟合图
        for i in range(3):
            # 处理数据并获得回归线后的数据
            (
                q_to_fit,
                delta_theta_over_delta_q_to_fit,
                delta_theta_over_delta_q_list,
                q_list,
            ) = self.calculator.process_single_group_data(i)

            # 执行线性拟合
            model, fit_data = self.calculator.perform_linear_fit(
                q_to_fit, delta_theta_over_delta_q_to_fit
            )

            # 获取异常值
            outliers = self.calculator.detect_outliers(fit_data)

            # 重新拟合数据并移除异常值
            refit_model, filtered_data = (
                self.calculator.refit_data_after_outlier_removal(fit_data, outliers)
            )

            refit_slope = refit_model.coef_[0]
            refit_intercept = refit_model.intercept_

            # 创建重新拟合图
            self.create_refit_figure(
                i,
                filtered_data,
                refit_slope,
                refit_intercept,
                q_list,
                delta_theta_over_delta_q_list,
                self.plot_ranges_refit[i],
            )

        # 3. 生成对比图
        self.generate_comparison_figures()

        # 4. 生成整合图
        self.integrate_figures()


if __name__ == "__main__":
    plotter = Filteration_Plotter(r"./过滤原始数据记录表(非).csv")
    plotter.generate_all_figures()
