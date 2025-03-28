# Oxygen_Desorption_Experiment_Processor_processor.py

# 内部库
import sys
import os
from pathlib import Path

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = Path(current_script_path).parents[3]  # parents[3]向上4级到项目根
sys.path.insert(0, str(project_root))

import zipfile
from typing import Optional

from gui.screens.calculators.oxygen_desorption_calculator import (
    Experiment_Data_Loader,
    Packed_Tower_Calculator,
    Oxygen_Desorption_Calculator,
)
from gui.screens.plotters.oxygen_desorption_plotter import (
    Packed_Tower_Plotter,
    Oxygen_Desorption_Plotter,
)


class Result_Compressor:
    @staticmethod
    def compress_results(
        output_dir: str = "./拟合图结果", zip_name: str = "拟合图结果.zip"
    ):
        """压缩结果文件

        Args:
            output_dir (str): 结果文件目录
            zip_name (str): 压缩包名称

        Raises:
            FileNotFoundError: 当输出目录不存在时抛出
        """
        output_path = Path(output_dir)
        if not output_path.exists():
            raise FileNotFoundError(f"目录 {output_dir} 不存在")

        with zipfile.ZipFile(zip_name, "w") as zipf:
            for file_path in output_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_path)
                    zipf.write(file_path, arcname)
        print(f"结果已压缩至 {Path(zip_name).absolute()}")


class Oxygen_Desorption_Experiment_Processor:
    def __init__(
        self,
        dry_packed_path: str,
        wet_packed_path: str,
        water_constant_path: str,
        air_constant_path: str,
        output_dir: Optional[str] = None,
    ):
        """初始化实验处理器

        Args:
            dry_packed_path: 干填料数据文件路径
            wet_packed_path: 湿填料数据文件路径
            water_constant_path: 水流量一定数据文件路径
            air_constant_path: 空气流量一定数据文件路径
            output_dir: 输出目录路径，默认为"./拟合图结果"
        """
        # 初始化数据加载器
        self.data_loader = Experiment_Data_Loader(
            dry_packed=dry_packed_path,
            wet_packed=wet_packed_path,
            water_constant=water_constant_path,
            air_constant=air_constant_path,
        )

        # 设置输出目录
        self.output_dir = Path(output_dir) if output_dir else Path("./拟合图结果")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 添加实例属性占位
        self.tower_calculator = None
        self.oxygen_calculator = None

    def run_all_calculations(self, compress_results: bool = True):
        """执行完整计算流程

        Args:
            compress_results: 是否压缩结果文件，默认为True
        """
        try:
            # 填料塔计算
            self.tower_calculator = Packed_Tower_Calculator(
                self.data_loader
            )  # 保存到self
            self.tower_calculator.calc_all_files()

            tower_plotter = Packed_Tower_Plotter(self.tower_calculator)
            tower_plotter.plot_comparison(
                save_path=str(self.output_dir / "填料塔性能对比.png")
            )

            # 氧解吸计算
            self.oxygen_calculator = Oxygen_Desorption_Calculator(
                self.data_loader
            )  # 保存到self
            self.oxygen_calculator.calc_all_files()

            oxygen_plotter = Oxygen_Desorption_Plotter(self.oxygen_calculator)
            oxygen_plotter.plot_correlation(
                save_path=str(self.output_dir / "氧解吸传质关联.png")
            )

            # 可选结果压缩
            if compress_results:
                Result_Compressor.compress_results(
                    output_dir=str(self.output_dir),
                    zip_name=str(self.output_dir.parent / "拟合图结果.zip"),
                )

        except Exception as e:
            print(f"计算过程中发生错误: {str(e)}")
            raise


if __name__ == "__main__":
    # 使用示例
    try:
        # 替换为实际文件路径（修正参数名称）
        processor = Oxygen_Desorption_Experiment_Processor(
            dry_packed_path=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/干填料.csv",
            wet_packed_path=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/湿填料.csv",
            water_constant_path=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/水流量一定_空气流量改变.csv",
            air_constant_path=Path(project_root)
            / "csv_data/解吸/解吸原始记录表(非)/空气流量一定_水流量改变.csv",
        )

        processor.run_all_calculations()

    except Exception as e:
        print(f"程序运行失败: {str(e)}")
