# extraction_plotter.py

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
import numpy as np
import logging
import matplotlib.pyplot as plt

# 配置日志设置
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 设置matplotlib日志级别为ERROR，避免显示findfont的DEBUG信息
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

from scipy.integrate import trapezoid
from scipy.interpolate import interp1d

from gui.screens.calculators.extraction_calculator import Extraction_Calculator


class Extraction_Plotter:
    def __init__(self, calculator):
        self.calculator = calculator
        self._setup_plot_style()
        self.output_dir = "./拟合图结果"

    def _setup_plot_style(self):
        """统一设置专业科研绘图样式"""
        plt.rcParams.update(
            {
                "font.family": [
                    "SimHei",
                    "Microsoft YaHei",
                    "Arial Unicode MS",
                ],  # 字体回退链
                "axes.unicode_minus": False,
                "figure.dpi": 300,  # 印刷级分辨率
                "axes.linewidth": 2,  # 坐标轴线宽
                "grid.alpha": 0.3,  # 网格透明度
                "legend.frameon": False,  # 图例无边框
                "legend.fontsize": 10,  # 图例字号
                "xtick.major.width": 2,  # X轴刻度线宽
                "ytick.major.width": 2,  # Y轴刻度线宽
                "xtick.minor.visible": True,  # 显示次要刻度
                "ytick.minor.visible": True,  # 显示次要刻度
                "figure.facecolor": "white",  # 图表背景色
                "savefig.bbox": "tight",  # 保存时自动裁剪
            }
        )  # 在 Extraction_Plotter 类中修改字体设置方法

    def _setup_plot_style(self):
        """智能配置中文字体，支持跨平台"""
        import matplotlib.font_manager as fm

        # 中文字体优先级列表
        chinese_fonts = [
            "Microsoft YaHei",  # Windows 微软雅黑
            "SimHei",  # Windows 中易黑体
            "WenQuanYi Zen Hei",  # Linux 文泉驿
            "PingFang SC",  # macOS 苹方
            "Source Han Sans SC",  # 思源黑体
        ]

        # 扫描系统所有字体
        system_fonts = {f.name for f in fm.fontManager.ttflist}

        # 选择第一个可用的中文字体
        selected_font = None
        for font in chinese_fonts:
            if font in system_fonts:
                selected_font = font
                break

        # 配置字体参数
        plt.rcParams.update(
            {
                "font.family": "sans-serif",
                "font.sans-serif": [selected_font] if selected_font else [],
                "axes.unicode_minus": False,
                "figure.dpi": 300,
                "axes.linewidth": 2,
                "grid.alpha": 0.3,
                "legend.frameon": False,
                "legend.fontsize": 10,
            }
        )

        # 如果未找到中文字体，显示警告
        if not selected_font:
            import warnings

            warnings.warn(
                "\n\n⚠️ 未检测到系统中文字体！请执行以下操作：\n"
                "Windows用户：安装'微软雅黑'字体\n"
                "Mac用户：终端执行 `brew tap homebrew/cask-fonts && brew install font-wqy-microhei`\n"
                "Linux用户：执行 `sudo apt install fonts-wqy-microhei`"
            )

    def create_output_dir(self):
        """创建输出目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def plot_origin_curves(self):
        """绘制主分析曲线图"""
        plt.figure(figsize=(10, 8), facecolor="white")

        # 绘制分配曲线
        self._plot_distribution_curve()

        # 绘制操作线
        self._plot_operating_line(0, "操作线1", "#2ca02c")  # 绿色
        self._plot_operating_line(1, "操作线2", "#ff7f0e")  # 橙色

        # 专业图表装饰
        plt.title("分配曲线与操作线分析图", fontsize=14, pad=15)
        plt.xlabel("萃余相浓度 X (kg/kg)", fontsize=12, labelpad=10)
        plt.ylabel("萃取相浓度 Y (kg/kg)", fontsize=12, labelpad=10)
        plt.legend(loc="upper left", fontsize=10)
        plt.grid(True, which="both", linestyle=":", alpha=0.5)
        plt.xlim(0, max(self.calculator.X3_data) * 1.1)
        plt.ylim(0, max(self.calculator.Y3_data) * 1.1)

        # 边框强化
        for spine in plt.gca().spines.values():
            spine.set_linewidth(2)

        self._save_figure("主分析曲线图")

    def _plot_distribution_curve(self):
        """绘制分配曲线元素"""
        plt.scatter(
            self.calculator.X3_data,
            self.calculator.Y3_data,
            c="#9467bd",  # 紫色
            marker="^",
            s=80,
            edgecolor="k",
            linewidth=1,
            label="实验数据点",
            zorder=3,
        )
        plt.plot(
            self.calculator.X3_to_fit,
            self.calculator.Y_fitted,
            color="#1f77b4",  # 蓝色
            lw=2.5,
            label=f"三次多项式拟合 (R²={self._calculate_r_squared():.3f})",
        )

    def _plot_operating_line(self, idx, label, color):
        """专业操作线绘制"""
        X_points = [self.calculator.X_Rb[idx], self.calculator.X_Rt[idx]]
        Y_points = [self.calculator.Y_Eb[idx], 0]

        # 生成直线数据
        X_line = np.linspace(0, X_points[0], 100)
        Y_line = eval(f"self.calculator.k{idx+1}") * X_line + eval(
            f"self.calculator.b{idx+1}"
        )

        # 绘制元素
        plt.scatter(
            X_points,
            Y_points,
            c=color,
            s=100,
            edgecolors="k",
            linewidth=1,
            zorder=4,
            label=f"{label}端点",
        )
        plt.plot(
            X_line,
            Y_line,
            color=color,
            ls="--",
            lw=2,
            alpha=0.8,
            label=f'{label} ($Y={eval(f"self.calculator.k{idx+1}"):.4f}X+{eval(f"self.calculator.b{idx+1}"):.4f}$)',
        )

    def _calculate_r_squared(self):
        """计算决定系数"""
        y_pred = np.polyval(self.calculator.coefficients, self.calculator.X3_data)
        ss_res = np.sum((self.calculator.Y3_data - y_pred) ** 2)
        ss_tot = np.sum(
            (self.calculator.Y3_data - np.mean(self.calculator.Y3_data)) ** 2
        )
        return 1 - (ss_res / ss_tot)

    def plot_integration_curves(self):
        """绘制专业级积分曲线"""
        # 直接使用已分组的数据
        grouped_data = self.calculator.data5_for_graph_integral

        for idx, group in enumerate(grouped_data):
            plt.figure(figsize=(10, 6), facecolor="white")

            # 构建数据字典
            data_dict = {
                "Y5_Eb": group[0],
                "X_Rb": group[1],
                "Y5star": group[2],
                "integrand": group[3],
            }

            self._plot_single_integration(data_dict, idx)

            # 专业标注
            plt.title(f"图解积分曲线 - 实验组 {idx+1}", fontsize=12, pad=15)
            plt.xlabel("萃取相浓度 $Y_5$", fontsize=10, labelpad=8)
            plt.ylabel("积分项 $\\frac{1}{Y_5^* - Y_5}$", fontsize=10, labelpad=8)
            plt.grid(True, which="both", linestyle=":", alpha=0.3)

            # 边框强化
            for spine in plt.gca().spines.values():
                spine.set_linewidth(2)

            self._save_figure(f"积分曲线_{idx+1}")

    def _plot_single_integration(self, data, idx):
        """绘制单组积分曲线（科研级样式）"""
        # 插值平滑
        interp_func = interp1d(data["Y5_Eb"], data["integrand"], "cubic")
        Y_smooth = np.linspace(data["Y5_Eb"].min(), data["Y5_Eb"].max(), 100)
        integrand_smooth = interp_func(Y_smooth)

        # 计算积分值
        integral = trapezoid(integrand_smooth, Y_smooth)

        # 专业绘图元素
        plt.fill_between(
            Y_smooth,
            integrand_smooth,
            alpha=0.3,
            color="#8c564b",  # 棕色
            label="积分区域",
        )
        plt.plot(
            Y_smooth, integrand_smooth, color="#1f77b4", lw=2, label="拟合曲线"
        )  # 蓝色
        plt.scatter(
            data["Y5_Eb"],
            data["integrand"],
            c="#d62728",  # 红色
            s=50,
            edgecolor="k",
            linewidth=0.8,
            label="离散数据点",
            zorder=3,
        )

        # 科研级标注
        plt.text(
            0.95,
            0.85,
            f"积分面积 = {integral:.5f}",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            bbox=dict(
                facecolor="white",
                edgecolor="#2f2f2f",
                boxstyle="round,pad=0.3",
                alpha=0.9,
            ),
            fontsize=10,
        )
        plt.legend(loc="upper right", fontsize=9)

    def _save_figure(self, name):
        """保存科研级图表"""
        plt.tight_layout()
        plt.savefig(
            f"{self.output_dir}/{name}.png",
            dpi=300,
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.close()

    def package_results(self, zip_file="萃取分析结果.zip"):
        """专业打包方法"""
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(
                        file_path, arcname=os.path.relpath(file_path, self.output_dir)
                    )


if __name__ == "__main__":
    # 文件路径
    origin_csv = "./csv_data/萃取/萃取原始数据记录表(非)/1_原始数据记录.csv"
    distribution_csv = "./csv_data/萃取/萃取原始数据记录表(非)/3_分配曲线数据集.csv"

    # 初始化计算器
    calculator = Extraction_Calculator(origin_csv, distribution_csv)
    calculator.run_calculations()

    # 初始化绘图器
    plotter = Extraction_Plotter(calculator)
    plotter.create_output_dir()

    # 生成图表
    plotter.plot_origin_curves()
    plotter.plot_integration_curves()

    # 打包结果
    plotter.package_results()
    print("处理完成！结果已保存至当前目录")
