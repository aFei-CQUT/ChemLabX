# distillation_experiment_processor.py

import os
import sys
import zipfile
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = Path(current_script_path).parents[3]
sys.path.insert(0, str(project_root))

from gui.screens.calculators.distillation_calculator import Distillation_Calculator
from gui.screens.plotters.distillation_plotter import Distillation_Plotter


class Distillation_Experiment_Processor:
    """
    精馏实验流程处理器

    功能扩展：
    - 自动化执行完整实验流程
    - 结果文件管理
    - 数据打包输出

    主要方法：
    process_experiment() - 执行完整处理流程
    """

    def __init__(self, file_path, R, αm, F, tS, tF, output_dir="实验结果"):
        """
        初始化实验处理器

        参数：
        output_dir (str): 结果输出目录
        """
        # 回流比
        self.R = R

        # 初始化计算引擎
        self.calculator = Distillation_Calculator(
            file_path=file_path, R=R, αm=αm, F=F, tS=tS, tF=tF
        )

        # 初始化可视化引擎
        self.plotter = Distillation_Plotter(self.calculator)

        # 配置输出路径
        self.file_path = file_path
        self.output_dir = Path(output_dir)
        self.base_name = Path(file_path).stem
        self._prepare_directory()

    def _prepare_directory(self):
        """创建结构化输出目录"""
        (self.output_dir / "原始数据").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "计算结果").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "拟合图结果").mkdir(parents=True, exist_ok=True)

    def process_experiment(self, show_plot=False):
        """
        执行完整实验处理流程

        参数：
        show_plot (bool): 是否显示可视化图表
        """
        try:
            # 保存计算结果
            self._save_text_results()

            # 生成可视化
            self._generate_plots(show=show_plot)

            # 打包结果
            self._create_archive()

            print(f"实验处理完成，结果保存在：{self.output_dir.resolve()}")
            return True
        except Exception as e:
            print(f"处理失败：{str(e)}")
            return False

    def _save_text_results(self):
        """保存文本计算结果"""
        result_path = self.output_dir / "计算结果" / f"{self.base_name}_results.txt"
        self.calculator.save_results(str(result_path))

    def _generate_plots(self, show=True):
        """生成可视化图表"""
        plot_path = self.output_dir / "拟合图结果" / f"{self.base_name}.png"
        self.plotter.plot_mccabe_thiele(save_path=str(plot_path), show=show)

    def _create_archive(self):
        """创建ZIP打包文件"""
        zip_path = self.output_dir / f"{self.base_name}_results.zip"

        with zipfile.ZipFile(zip_path, "w") as zipf:
            # 原始数据
            zipf.write(self.file_path, arcname=f"原始数据/{Path(self.file_path).name}")

            # 计算结果
            text_file = self.output_dir / "计算结果" / f"{self.base_name}_results.txt"
            zipf.write(text_file, arcname=text_file.name)

            # 可视化结果
            plot_file = self.output_dir / "拟合图结果" / f"{self.base_name}.png"
            zipf.write(plot_file, arcname=plot_file.name)

    @property
    def result_paths(self):
        """获取各结果文件路径"""
        return {
            "original_data": self.file_path,
            "text_results": self.output_dir
            / "计算结果"
            / f"{self.base_name}_results.txt",
            "visualization": self.output_dir / "拟合图结果" / f"{self.base_name}.png",
            "archive": self.output_dir / f"{self.base_name}_results.zip",
        }


if __name__ == "__main__":
    # 使用示例
    DATA_FILE = "./csv_data/精馏/精馏原始记录表(非)/Sheet1.csv"

    # 处理常规回流比 (R=4)
    processor_normal = Distillation_Experiment_Processor(
        file_path=DATA_FILE, R=4, αm=2.0, F=80, tS=30, tF=26, output_dir="实验结果/R4"
    )
    processor_normal.process_experiment(show_plot=True)

    # 处理全回流 (R=+∞)
    processor_infinite = Distillation_Experiment_Processor(
        file_path=DATA_FILE,
        R=10000,
        αm=2.0,
        F=80,
        tS=30,
        tF=26,
        output_dir="实验结果/全回流",
    )
    processor_infinite.process_experiment()
