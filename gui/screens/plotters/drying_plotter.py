# drying_plotter.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import zipfile
import pickle

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from pathlib import Path

from gui.screens.calculators.drying_calculator import Drying_Calculator


class Drying_Plotter:
    def __init__(self, calculator):
        """初始化绘图器，需要传入已计算完成的Drying_Calculator实例"""
        if not isinstance(calculator, Drying_Calculator):
            raise TypeError("必须传入Drying_Calculator实例")

        if not calculator.results:
            raise ValueError("计算器尚未执行计算，请先调用run_full_calculation()")

        self.calculator = calculator
        self.setup_plot_style()

    def setup_plot_style(self):
        """绘图样式配置"""
        # plt.style.use("seaborn-v0_8")
        plt.rcParams.update(
            {
                "font.family": ["Microsoft YaHei", "DejaVu Sans"],  # 主字体+回退字体
                "axes.unicode_minus": False,
                "figure.dpi": 150,
                "axes.titlesize": 12,
                "axes.labelsize": 10,
                "xtick.labelsize": 8,
                "ytick.labelsize": 8,
                "mathtext.fontset": "cm",  # 使用Computer Modern数学字体
                "mathtext.default": "regular",
            }
        )

    def _validate_data(self):
        """验证必要绘图数据是否存在"""
        required_attrs = ["τ_bar", "X_bar", "U"]
        missing = [
            attr for attr in required_attrs if not hasattr(self.calculator, attr)
        ]
        if missing:
            raise AttributeError(f"缺少必要数据: {', '.join(missing)}")

    def plot_drying_curve(self, save_dir="./拟合图结果"):
        """绘制干燥曲线"""
        self._validate_data()
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(
            self.calculator.τ_bar,
            self.calculator.X_bar,
            marker="o",
            color="#FF6B6B",
            edgecolor="w",
            label="实验数据点",
        )
        ax.plot(
            self.calculator.τ_bar,
            self.calculator.X_bar,
            linestyle="--",
            color="#4ECDC4",
            linewidth=2,
            label="拟合曲线",
        )

        ax.set_title("物料干基含水量随时间变化曲线", pad=20)
        ax.set_xlabel(r"干燥时间 $\tau$ (h)", labelpad=10)
        ax.set_ylabel(r"干燥速率 $U\ (\mathrm{kg/m^2 \cdot h})$", labelpad=10)
        ax.grid(True, alpha=0.3)
        ax.legend(frameon=True)

        curve_path = save_path / "drying_curve.png"
        fig.savefig(curve_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return str(curve_path)

    def plot_drying_rate_curve(self, save_dir="./拟合图结果"):
        """绘制干燥速率曲线"""
        self._validate_data()
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(
            self.calculator.X_bar,
            self.calculator.U,
            marker="s",
            color="#45B7D1",
            edgecolor="w",
            label="速率数据点",
        )

        # 添加恒定速率参考线
        if self.calculator.U_c is not None:
            ax.axhline(
                y=self.calculator.U_c,
                color="#FF9F43",
                linestyle="--",
                label=f"恒定速率 {self.calculator.U_c:.3f} kg/m²·h",
            )

        ax.set_title("干燥速率曲线", pad=20)
        ax.set_xlabel(r"干基含水量 $X$ (kg/kg 干基)", labelpad=10)
        ax.set_ylabel(r"干燥速率 $U$ (kg/m²·h)", labelpad=10)
        ax.grid(True, alpha=0.3)
        ax.legend(frameon=True)

        rate_path = save_path / "drying_rate_curve.png"
        fig.savefig(rate_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return str(rate_path)

    def integrate_images(self, save_dir="./拟合图结果"):
        """
        生成组合对比图（横向排列）
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # 生成子图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # 干燥曲线
        ax1.scatter(self.calculator.τ_bar, self.calculator.X_bar, color="#FF6B6B")
        ax1.plot(self.calculator.τ_bar, self.calculator.X_bar, "#4ECDC4")
        ax1.set_title("干燥曲线")

        # 干燥速率曲线
        ax2.scatter(self.calculator.X_bar, self.calculator.U, color="#45B7D1")
        if self.calculator.U_c:
            ax2.axhline(self.calculator.U_c, color="#FF9F43", linestyle="--")
        ax2.set_title("干燥速率曲线")

        # 统一样式
        for ax in (ax1, ax2):
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis="both", which="major", labelsize=8)

        combined_path = save_path / "combined_plots.png"
        plt.tight_layout()
        fig.savefig(combined_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return str(combined_path)

    def compress_results(self, source_dir="./拟合图结果", output_name="拟合结果"):
        """
        生成压缩包
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"目录不存在: {source_dir}")

        # 直接使用指定的输出名称，不加时间戳
        output_path = Path(f"{output_name}.zip")

        with zipfile.ZipFile(output_path, "w") as zipf:
            for file in source_path.glob("*.png"):
                zipf.write(file, arcname=file.name)

        return str(output_path)

    def serialize_results(self, output_path="干燥实验结果.pkl"):
        """
        带版本控制的序列化
        """
        data = {
            "metadata": {
                "version": "1.1",
                "create_time": pd.Timestamp.now().isoformat(),
                "calculator_type": type(self.calculator).__name__,
            },
            "results": self.calculator.results,
        }

        with open(output_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

        return output_path

    def run_full_plotting(self, output_dir="./拟合结果"):
        """完整的绘图流程"""
        results_dir = Path(output_dir)
        results_dir.mkdir(parents=True, exist_ok=True)

        # 生成图表
        self.plot_drying_curve(results_dir)
        self.plot_drying_rate_curve(results_dir)
        combined_path = self.integrate_images(results_dir)

        # 打包结果
        zip_path = self.compress_results(results_dir)
        pkl_path = self.serialize_results(results_dir / "实验数据.pkl")

        return {
            "combined_plot": combined_path,
            "zip_archive": zip_path,
            "serialized_data": pkl_path,
        }


# 使用示例
if __name__ == "__main__":
    csv_files = [
        "./csv_data/干燥原始数据记录表(非)/原始数据1.csv",
        "./csv_data/干燥原始数据记录表(非)/原始数据2.csv",
    ]
    # 执行计算
    calculator = Drying_Calculator(csv_files)
    calculator.run_full_calculation()

    # 初始化绘图器
    plotter = Drying_Plotter(calculator)

    # 运行完整流程
    outputs = plotter.run_full_plotting()

    print("生成结果：")
    print(f"- 组合图表: {outputs['combined_plot']}")
    print(f"- 压缩包: {outputs['zip_archive']}")
    print(f"- 序列化数据: {outputs['serialized_data']}")
