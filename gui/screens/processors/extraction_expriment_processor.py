# extraction_experiment_processor.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

import logging

# 配置日志设置
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

import argparse
from gui.screens.calculators.extraction_calculator import Extraction_Calculator
from gui.screens.plotters.extraction_plotter import Extraction_Plotter


class ExtractionExperimentProcessor:
    def __init__(self, main_file=None, distribution_file=None):
        """
        初始化实验处理器
        :param main_file: 主数据文件路径
        :param distribution_file: 分配曲线数据文件路径
        """
        self.main_file = main_file
        self.distribution_file = distribution_file
        self.calculator = None
        self.plotter = None

        # 结果输出配置
        self.output_dir = "./拟合图结果"
        self.zip_file = "萃取分析结果.zip"

    def validate_files(self):
        """验证输入文件有效性"""
        missing_files = []
        if not os.path.exists(self.main_file):
            missing_files.append(self.main_file)
        if not os.path.exists(self.distribution_file):
            missing_files.append(self.distribution_file)

        if missing_files:
            raise FileNotFoundError(f"以下必要文件缺失：{', '.join(missing_files)}")

    def setup_components(self):
        """初始化各处理组件"""
        self.calculator = Extraction_Calculator(self.main_file, self.distribution_file)
        self.plotter = Extraction_Plotter(self.calculator)
        self.plotter.output_dir = self.output_dir

    def process_data(self):
        """执行完整数据处理流程"""
        # 数据计算阶段
        self.calculator.run_calculations()

        # 可视化阶段
        self.plotter.create_output_dir()
        print("\n正在生成分析图表...")
        self.plotter.plot_main_curves()
        self.plotter.plot_integration_curves()

        # 结果打包
        print("正在打包结果文件...")
        self.plotter.package_results(self.zip_file)

    def print_summary(self):
        """输出处理结果摘要"""
        print(f"\n{'='*40}")
        print("处理完成！结果文件已保存至：")
        print(f"- 图表目录: {os.path.abspath(self.output_dir)}")
        print(f"- 压缩包文件: {os.path.abspath(self.zip_file)}")
        print(f"{'='*40}")

    def run(self):
        """主执行流程"""
        try:
            self.validate_files()
            self.setup_components()
            self.process_data()
            self.print_summary()
        except Exception as e:
            print(f"\n处理过程中发生错误：{str(e)}")
            print("建议检查：")
            print("1. 输入文件格式是否符合要求")
            print("2. 数据列是否完整")
            print("3. 系统字体配置是否正确")
            raise


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="萃取实验数据处理系统")
    parser.add_argument(
        "--main",
        type=str,
        default="./1 原始数据记录.csv",
        help="主数据文件路径",
    )
    parser.add_argument(
        "--distribution",
        type=str,
        default="./3 分配曲线数据集.csv",
        help="分配曲线数据文件路径",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # 命令行参数解析
    args = parse_arguments()

    # 创建处理器实例并运行
    processor = ExtractionExperimentProcessor(main_file=args.main, distribution_file=args.distribution)
    processor.run()
