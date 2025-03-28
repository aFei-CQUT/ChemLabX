# distillation_plotter.py

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

# from gui.screens.calculators.distillation_calculator import Distillation_Calculator
from gui.screens.calculators.distillation_calculator import process_and_save


class Distillation_Plotter:
    """
    精馏塔可视化绘图类

    功能：
    - 生成McCabe-Thiele图
    - 可视化理论塔板计算结果
    - 保存可视化结果

    使用方式：
    传入已计算的Distillation_Calculator实例
    """

    def __init__(self, calculator):
        """
        初始化绘图器

        参数:
        calculator : Distillation_Calculator
            已完成计算的精馏计算器实例
        """
        self.calc = calculator

        # 绘图参数配置
        self.figure_size = (10, 8)
        self.dpi = 150
        self.line_styles = {
            "equilibrium": {"linestyle": "--", "color": "blue", "linewidth": 2},
            "operating": {"linestyle": "-", "color": "green", "linewidth": 2},
            "stages": {"linestyle": ":", "color": "purple", "linewidth": 2},
            "q_line": {"linestyle": "-.", "color": "brown", "linewidth": 1.5},
        }

        # 字体配置
        plt.rcParams.update(
            {
                "font.sans-serif": ["SimHei"],  # 设置中文字体
                "axes.unicode_minus": False,  # 正常显示负号
                "font.size": 12,
            }
        )

    def _generate_plot_data(self):
        """生成绘图所需数据"""
        x = np.linspace(0, 1, 100)

        # 各曲线数据
        data = {
            "x": x,
            "y_eq": self.calc.y_e(x),  # 平衡线
            "y_rect": self.calc.y_np1(x),  # 精馏段操作线
            "y_strip": self.calc.y_mp1(x),  # 提馏段操作线
            "y_q": self.calc.y_q(x),  # q线
        }

        # 阶梯图数据
        x_stages = np.array([self.calc.xD])
        y_stages = np.array([self.calc.xD])

        for n, xi in enumerate(self.calc.xn):
            # 垂直线段
            x_stages = np.append(x_stages, xi)
            y_stages = np.append(y_stages, self.calc.yn[n])

            # 水平线段
            x_stages = np.append(x_stages, xi)
            if xi >= self.calc.xQ:
                y_next = self.calc.y_np1(xi)
            else:
                y_next = self.calc.y_mp1(xi)
            y_stages = np.append(y_stages, y_next)

        data.update({"x_stages": x_stages, "y_stages": y_stages})

        return data

    def plot_mccabe_thiele(self, save_path=None, show=True):
        """
        绘制McCabe-Thiele图

        参数:
        save_path : str, optional
            图片保存路径，如果不提供则不保存
        show : bool, optional
            是否显示图表 (默认为True)
        """
        # 准备数据
        data = self._generate_plot_data()

        # 创建图形
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        # 绘制主要曲线
        ax.plot(
            data["x"], data["x"], linestyle="-", color="gray", alpha=0.5, label="对角线"
        )
        ax.plot(
            data["x"], data["y_eq"], **self.line_styles["equilibrium"], label="平衡线"
        )
        ax.plot(
            data["x"],
            data["y_rect"],
            **self.line_styles["operating"],
            label="精馏段操作线",
        )
        ax.plot(
            data["x"],
            data["y_strip"],
            **self.line_styles["operating"],
            label="提馏段操作线",
        )
        ax.plot(data["x"], data["y_q"], **self.line_styles["q_line"], label="q线")

        # 绘制阶梯图
        ax.plot(
            self.calc.xn,
            self.calc.yn,
            marker="+",
            markersize=10,
            linestyle="",
            color="red",
            label="理论塔板点",
        )
        ax.plot(
            data["x_stages"],
            data["y_stages"],
            **self.line_styles["stages"],
            label=f"理论塔板 ({self.calc.NT}块)",
        )

        # 标记关键点
        key_points = [
            (self.calc.xD, self.calc.xD, "D (馏出液)", (0.02, -0.05)),
            (self.calc.xW, self.calc.xW, "W (釜残液)", (0.02, 0.02)),
            (self.calc.xQ, self.calc.yQ, "Q (进料点)", (-0.05, 0.02)),
        ]

        for x, y, label, offset in key_points:
            ax.plot(x, y, "ko", markersize=6)
            ax.annotate(
                label,
                xy=(x, y),
                xytext=(x + offset[0], y + offset[1]),
                arrowprops=dict(arrowstyle="->", color="black", linewidth=1),
                bbox=dict(boxstyle="round", alpha=0.2, facecolor="white"),
            )

        # 设置图形属性
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("液相摩尔分数 (x)", fontsize=12)
        ax.set_ylabel("气相摩尔分数 (y)", fontsize=12)
        ax.set_title(
            f"McCabe-Thiele法图解理论板数\n(回流比 R={self.calc.R}, q={self.calc.q:.2f})",
            fontsize=14,
            pad=20,
        )

        # 添加网格和刻度
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())

        # 添加理论板数标注
        ax.text(
            0.65,
            0.25,
            f"理论板数: {self.calc.NT}\n"
            f"实际板数: {self.calc.NT - 1}\n"
            f"进料位置: 第{len(self.calc.xn[self.calc.xn > self.calc.xQ])}块",
            bbox=dict(boxstyle="round", alpha=0.2, facecolor="white"),
        )

        # 图例
        ax.legend(loc="upper left", framealpha=0.8)

        # 调整布局
        fig.tight_layout()

        # 保存或显示
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"图表已保存至: {save_path}")

        if show:
            plt.show()
        else:
            plt.close(fig)


# 使用示例
if __name__ == "__main__":

    # 1. R -> 4
    calculator = process_and_save(
        file_path="./csv_data/精馏/精馏原始记录表(非)/Sheet1.csv",
        R=4,
        αm=2.0,
        F=80,
        tS=30,
        tF=26,
        filename="R_4_结果",
    )

    if calculator:  # 如果计算成功
        # 创建绘图器并绘图
        plotter = Distillation_Plotter(calculator)
        plotter.plot_mccabe_thiele(save_path="./拟合图结果/R_4_plot.png", show=False)

    # 2. R -> +∞
    calculator = process_and_save(
        file_path="./csv_data/精馏/精馏原始记录表(非)/Sheet1.csv",
        R=10000,
        αm=2.0,
        F=80,
        tS=30,
        tF=26,
        filename="R_+∞_结果",
    )

    if calculator:  # 如果计算成功
        # 创建绘图器并绘图
        plotter = Distillation_Plotter(calculator)
        plotter.plot_mccabe_thiele(save_path="./拟合图结果/R_+∞_plot.png", show=False)
