# distillation_screen.py

# 内部库
import sys
import os

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

import traceback
from tkinter import messagebox, filedialog, ttk
import pandas as pd
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.common_widgets.string_entries_widget import StringEntriesWidget
from gui.screens.processors.distillation_experiment_processor import (
    Distillation_Experiment_Processor,
)


class Distillation_Screen(Base_Screen):
    """继承自Base_Screen的精馏实验界面，支持动态列生成"""

    RAW_COLS = ["序号"]  # 初始列，实际列将在加载数据后动态生成
    RESULT_COLS = ["组号", "回流比", "理论塔板数", "实际塔板数", "分离效率"]

    def __init__(self, window):
        super().__init__(window)
        self.csv_file_path = None
        self.processors = []
        self.processed_data_list = []
        self.images_paths = []
        self.current_page = 0
        self._adjust_layout()

    def _init_parameter_input(self):
        """完全覆盖基类参数输入配置"""
        # 创建参数容器框架
        param_frame = ttk.Frame(self.left_frame)
        param_frame.pack(fill="x", padx=5, pady=5)

        # 创建全新的参数组件（不调用基类初始化）
        self.param_widget = StringEntriesWidget(param_frame)
        self.param_widget.pack(fill="both", expand=True)

        # 配置精馏实验参数
        self.param_widget.update_entries(
            [
                {"label": "回流比(R)", "default": "4", "validation_pattern": r"^\d+$"},
                {"label": "αm", "default": "2.0", "validation_pattern": r"^\d+\.?\d*$"},
                {"label": "F(mL/min)", "default": "80", "validation_pattern": r"^\d+$"},
                {"label": "tS(℃)", "default": "30", "validation_pattern": r"^\d+$"},
                {"label": "tF(℃)", "default": "26", "validation_pattern": r"^\d+$"},
            ]
        )
        self.param_widget.bind("<<ParameterChange>>", self._on_parameter_change)

    def _init_control_buttons(self):
        """覆盖基类方法：保留串口按钮并添加精馏实验按钮"""
        # 调用基类方法创建串口控制按钮
        super()._init_control_buttons()

        # 获取基类创建的按钮框架
        experiment_frame = self.left_frame.nametowidget("experiment_btn_frame")
        data_frame = self.left_frame.nametowidget("data_btn_frame")

        # 调整按钮文本和布局
        experiment_frame.winfo_children()[0].config(text="打开串口")  # 串口按钮
        experiment_frame.winfo_children()[1].config(
            text="开始采集", state="normal"
        )  # 采集按钮
        experiment_frame.winfo_children()[2].config(
            text="停止采集", state="normal"
        )  # 停止按钮

        # 在数据按钮组中添加精馏特有按钮
        buttons = [
            ("导入CSV", self.load_data),
            ("处理数据", self.process_data),
            ("绘制图形", self.plot_graph),
        ]
        for col, (text, cmd) in enumerate(buttons):
            btn = ttk.Button(data_frame, text=text, command=cmd)
            btn.grid(row=0, column=col, padx=2, pady=2, sticky="ew")

    def _adjust_layout(self):
        """调整布局差异并初始化动态列"""
        # 更新表格列宽配置
        self.raw_table.update_columns(self.RAW_COLS)
        self.result_table.update_columns(
            self.RESULT_COLS, widths=[80, 100, 120, 120, 100]
        )

    # ---------------------------- 实现基类抽象方法 ----------------------------
    def start_data_acquisition(self):
        """实现采集启动功能"""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                messagebox.showwarning("警告", "请先打开串口连接！")
                return
            
            # 这里可以添加精馏实验特有的采集逻辑
            messagebox.showinfo("提示", "开始采集精馏实验数据")

        except Exception as e:
            self.logger.error(f"采集启动失败: {str(e)}")
            messagebox.showerror("错误", f"采集启动失败：{str(e)}")

    def stop_data_acquisition(self):
        """实现停止采集功能"""

        # 这里可以添加精馏实验特有的停止逻辑
        messagebox.showinfo("提示", "已停止数据采集")

    # ---------------------------- 核心方法重写 ----------------------------
    def load_data(self):
        """加载CSV数据（实现基类抽象方法）"""
        file_path = filedialog.askopenfilename(
            title="选择精馏实验CSV文件", filetypes=[("CSV Files", "*.csv")]
        )
        if not file_path:
            return

        try:
            self.csv_file_path = file_path
            df = pd.read_csv(file_path)

            # 动态生成列（序号+CSV列）
            dynamic_cols = ["序号"] + df.columns.tolist()
            self.RAW_COLS = dynamic_cols
            self.raw_table.update_columns(dynamic_cols)

            # 更新表格数据
            self._update_raw_table(df)

        except Exception as e:
            self.logger.error(f"数据加载失败: {str(e)}")
            messagebox.showerror("错误", f"文件加载失败：{str(e)}")

    def process_data(self):
        """处理数据（实现基类抽象方法）"""
        if not self.csv_file_path:
            messagebox.showwarning("警告", "请先导入CSV数据！")
            return

        try:
            self.show_processing("数据处理中...")
            self._create_processors()
            self._process_all_cases()
            self._update_result_table()

        except Exception as e:
            self.logger.error(f"数据处理失败: {traceback.format_exc()}")
            messagebox.showerror("错误", f"处理失败：{str(e)}")
        finally:
            self.close_processing()

    def plot_graph(self):
        """绘制图形（实现基类抽象方法）"""
        if not self.processors:
            messagebox.showwarning("警告", "请先处理数据！")
            return

        try:
            self.show_processing("生成图表中...")
            self._generate_plots()
            self.plot_frame.set_images_paths(self._get_plot_paths())
            self.plot_frame._update_page_controls()  # 启用分页控件

        except Exception as e:
            self.logger.error(f"绘图失败: {traceback.format_exc()}")
            messagebox.showerror("错误", f"绘图失败：{str(e)}")
        finally:
            self.close_processing()

    # ---------------------------- 精馏实验特有逻辑 ----------------------------
    def _create_processors(self):
        """根据界面参数动态创建处理器"""
        param_values = self.parameters
        try:
            R = float(param_values[0])
            αm = float(param_values[1])
            F = float(param_values[2])
            tS = float(param_values[3])
            tF = float(param_values[4])
        except (IndexError, ValueError) as e:
            messagebox.showerror("错误", f"参数错误: {str(e)}")
            return

        self.processors = [
            Distillation_Experiment_Processor(
                file_path=self.csv_file_path,
                R=R,
                αm=αm,
                F=F,
                tS=tS,
                tF=tF,
                output_dir=f"实验结果/R{R}",
            ),
            Distillation_Experiment_Processor(
                file_path=self.csv_file_path,
                R=10000,
                αm=αm,
                F=F,
                tS=tS,
                tF=tF,
                output_dir="实验结果/R_inf",
            ),
        ]

    def _process_all_cases(self):
        """处理所有回流比情况"""
        self.processed_data_list = []
        for processor in self.processors:
            processor.process_experiment(show_plot=False)
            self.processed_data_list.append(processor.calculator.results)

    def _update_raw_table(self, df):
        """更新原始数据表格"""
        self.raw_table.clear()
        for idx, row in df.iterrows():
            self.raw_table.append([idx + 1] + row.tolist())

    def _update_result_table(self):
        """更新结果表格"""
        self.result_table.clear()
        for idx, (processor, data) in enumerate(
            zip(self.processors, self.processed_data_list)
        ):
            self.result_table.append(
                [
                    idx + 1,
                    "4" if processor.R == 4 else "∞",
                    f"{data['理论塔板数']:.2f}",
                    f"{data['理论塔板数'] - 1:.2f}",
                    f"{data.get('分离效率', 'N/A')}",
                ]
            )

    def _generate_plots(self):
        """生成所有图形文件"""
        self.images_paths = []
        for processor in self.processors:
            plot_path = processor.result_paths["visualization"]
            processor.plotter.plot_mccabe_thiele(save_path=plot_path, show=False)
            self.images_paths.append(plot_path)

    def _get_plot_paths(self):
        """获取生成的图形路径"""
        return [p for p in self.images_paths if os.path.exists(p)]
