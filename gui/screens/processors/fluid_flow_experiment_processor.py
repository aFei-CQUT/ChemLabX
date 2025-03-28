# fluid_flow_experiment_processor.py

# 内置库
import sys
import os

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

from gui.screens.calculators.fluid_flow_calculator import (
    Fluid_Flow_Calculator,
    Centrifugal_Pump_Characteristics_Calculator,
    Auxiliary,
)
from gui.screens.plotters.fluid_flow_plotter import (
    Fluid_Flow_Plotter,
    Centrifugal_Pump_Characteristics_Plotter,
)


class Fluid_Flow_Expriment_Processor:
    def __init__(self, file_paths):
        """初始化实验处理器，设置数据文件路径"""
        self.file_paths = file_paths
        self.output_dir = "./拟合图结果"

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 初始化计算器和绘图器
        self.fluid_calculator = None
        self.pump_calculator = None
        self.fluid_plotter = None
        self.pump_plotter = None

        # 初始化辅助类
        self.auxiliary = Auxiliary(file_paths)

    def process_fluid_flow(self):
        """处理流体阻力实验数据"""
        fluid_file_path = self.auxiliary.identify_file_type(self.file_paths[0])
        if fluid_file_path == "fluid":
            self.fluid_calculator = Fluid_Flow_Calculator(self.file_paths[0])
            ans1, df1 = self.fluid_calculator.process()
            self.fluid_plotter = Fluid_Flow_Plotter(self.fluid_calculator)
            return ans1, df1
        else:
            raise ValueError("第一个文件不是流体阻力数据文件")

    def process_pump_characteristics(self):
        """处理离心泵特性实验数据"""
        pump_file_path = self.auxiliary.identify_file_type(self.file_paths[1])
        if pump_file_path == "pump":
            self.pump_calculator = Centrifugal_Pump_Characteristics_Calculator(
                self.file_paths[1]
            )
            ans2, df2, params_H, params_N, params_η = self.pump_calculator.process()
            self.pump_plotter = Centrifugal_Pump_Characteristics_Plotter(
                self.pump_calculator
            )
            return ans2, df2, params_H, params_N, params_η
        else:
            raise ValueError("第二个文件不是离心泵数据文件")

    def generate_all_plots(self):
        """生成所有分析图表"""
        if not self.fluid_plotter:
            self.process_fluid_flow()
        if not self.pump_plotter:
            self.process_pump_characteristics()

        self.fluid_plotter.plot()
        self.pump_plotter.plot()

    def get_fluid_flow_results(self):
        """获取流体阻力实验结果"""
        if not self.fluid_calculator:
            self.process_fluid_flow()
        return {
            "velocity": self.fluid_calculator.ans1[:, 0],
            "reynolds": self.fluid_calculator.ans1[:, 1],
            "friction_factor": self.fluid_calculator.ans1[:, 2],
            "log_reynolds": self.fluid_calculator.log_Re,
            "log_friction": self.fluid_calculator.log_λ,
            "polynomial": self.fluid_calculator.p,
        }

    def get_pump_characteristics_results(self):
        """获取离心泵特性实验结果"""
        if not self.pump_calculator:
            self.process_pump_characteristics()
        return {
            "head": self.pump_calculator.ans2[:, 0],
            "power": self.pump_calculator.ans2[:, 1],
            "efficiency": self.pump_calculator.ans2[:, 2],
            "head_params": self.pump_calculator.params_H,
            "power_params": self.pump_calculator.params_N,
            "efficiency_params": self.pump_calculator.params_η,
        }


if __name__ == "__main__":
    # 文件路径列表
    file_paths = [
        "./csv_data/流体/流体原始数据记录表(非)/流体阻力原始数据.csv",
        "./csv_data/流体/流体原始数据记录表(非)/离心泵原始数据.csv",
    ]

    # 创建实验处理器实例
    processor = Fluid_Flow_Expriment_Processor(file_paths)

    # 处理流体阻力数据
    fluid_ans, fluid_df = processor.process_fluid_flow()

    # 处理离心泵数据
    pump_ans, pump_df, pump_params_H, pump_params_N, pump_params_η = (
        processor.process_pump_characteristics()
    )

    # 生成所有图表
    processor.generate_all_plots()

    # 获取结果
    fluid_results = processor.get_fluid_flow_results()
    pump_results = processor.get_pump_characteristics_results()

    # 打印结果
    print("流体阻力实验结果:", fluid_results)
    print("离心泵特性实验结果:", pump_results)
