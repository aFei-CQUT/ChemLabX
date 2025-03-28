# drying_screen.py

# 内部库
import os
import sys
import logging
import traceback
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import pandas as pd

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

# 导入基类和组件
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.processors.drying_experiment_processor import (
    Drying_Experiment_Processor,
)


class Drying_Screen(Base_Screen):
    """干燥实验界面（完整保留基类按钮功能）"""

    RAW_COLS = ["时间τ/min", "总质量W1/g", "干球温度t_dry/℃", "湿球温度t_wet/℃"]
    RESULT_COLS = ["参数", "值"]

    def __init__(self, window):
        super().__init__(window)
        self.csv_file_paths = None
        self.processor = None
        self.results = None
        self.images_paths = []

        # 初始化组件
        self._adjust_base_components()
        self._update_button_states()  # 初始按钮状态

    def _adjust_base_components(self):
        """调整基类组件"""
        # 隐藏不需要的参数输入组件
        self.param_widget.pack_forget()

        # 初始化专用表格
        self._init_drying_tables()

    def _init_drying_tables(self):
        """初始化专用表格布局"""
        # 隐藏基类默认表格
        self.raw_table.pack_forget()
        self.result_table.pack_forget()

        # 创建优化后的原始数据表
        self.raw_table = TableWidget(
            self.left_frame, self.RAW_COLS, [120, 120, 140, 140], height=15
        )  # 调整列宽
        self.raw_table.pack(fill="both", expand=True, padx=5, pady=5)

        # 创建结果展示表
        self.result_table = TableWidget(
            self.left_frame, self.RESULT_COLS, [180, 220], height=8
        )  # 加宽结果列
        self.result_table.pack(fill="both", expand=True, padx=5, pady=5)

    def _update_button_states(self):
        """根据串口状态更新按钮可用性"""
        serial_connected = self.serial_connection and self.serial_connection.is_open

        # 获取按钮框架
        exp_frame = self._find_named_frame("experiment_btn_frame")
        data_frame = self._find_named_frame("data_btn_frame")

        # 实验控制按钮状态
        start_btn = exp_frame.grid_slaves(row=0, column=1)[0]
        stop_btn = exp_frame.grid_slaves(row=0, column=2)[0]

        # 数据处理按钮状态
        process_btn = data_frame.grid_slaves(row=0, column=1)[0]

        # 更新按钮状态
        for btn in [start_btn, stop_btn]:
            btn["state"] = "normal" if serial_connected else "disabled"

        process_btn["state"] = "normal" if self.csv_file_paths else "disabled"

    def _find_named_frame(self, frame_name):
        """查找指定名称的框架"""
        for child in self.left_frame.winfo_children():
            if hasattr(child, "winfo_name") and child.winfo_name() == frame_name:
                return child
            for subchild in child.winfo_children():
                if (
                    hasattr(subchild, "winfo_name")
                    and subchild.winfo_name() == frame_name
                ):
                    return subchild
        return None

    # 重写串口操作方法
    def _open_serial(self, port, baudrate):
        try:
            super()._open_serial(port, baudrate)
            self._update_button_states()  # 更新按钮状态
            messagebox.showinfo("成功", f"串口 {port} 已连接")
        except Exception as e:
            self._handle_error("串口连接失败", e)

    def _close_serial(self):
        super()._close_serial()
        self._update_button_states()  # 更新按钮状态
        messagebox.showinfo("提示", "串口已断开")

    # 数据采集方法（保持基类实现）
    def start_data_acquisition(self):
        """实时数据采集（需连接串口）"""
        if not self.serial_connection or not self.serial_connection.is_open:
            messagebox.showwarning("警告", "请先打开串口！")
            return

        try:
            self.show_processing("实时采集中...")
            # TODO: 实现具体采集逻辑
            self.close_processing()
            messagebox.showinfo("成功", "数据采集完成")
        except Exception as e:
            self._handle_error("采集错误", e)

    def stop_data_acquisition(self):
        """停止采集"""
        if hasattr(self, "processing_win"):
            self.close_processing()
            messagebox.showinfo("提示", "已停止采集")

    # 文件数据处理方法
    def load_data(self):
        """加载CSV数据"""
        file_paths = filedialog.askopenfilenames(
            title="选择干燥实验CSV文件（需包含原始数据1和原始数据2）",
            filetypes=[("CSV Files", "*.csv")],
            initialdir="./",
        )

        if not file_paths:
            return

        try:
            data1_path, data2_path = self._validate_files(file_paths)
            df = pd.read_csv(data2_path, header=0, skiprows=[1])
            raw_data = df[
                ["累计时间τ/min", "总质量W1/g", "干球温度t_dry/℃", "湿球温度t_wet/℃"]
            ].values

            self.csv_file_paths = [data1_path, data2_path]
            self._update_raw_table(raw_data)
            self._update_button_states()  # 更新处理按钮状态
            messagebox.showinfo("成功", "文件加载完成！")
        except Exception as e:
            self._handle_error("数据加载错误", e)

    def _validate_files(self, file_paths):
        """验证文件命名规范"""
        data1_path = data2_path = None
        for path in file_paths:
            filename = os.path.basename(path).lower()
            if "原始数据1" in filename:
                data1_path = path
            elif "原始数据2" in filename:
                data2_path = path

        if not all([data1_path, data2_path]):
            raise ValueError("必须包含原始数据1和原始数据2文件")
        return data1_path, data2_path

    def _update_raw_table(self, data):
        """更新原始数据表格"""
        self.raw_table.clear()
        for row in data:
            formatted_row = [
                f"{x:.2f}" if isinstance(x, float) else str(x) for x in row
            ]
            self.raw_table.append(formatted_row)

    def process_data(self):
        """处理数据"""
        if not self.csv_file_paths:
            messagebox.showwarning("警告", "请先导入CSV数据！")
            return

        try:
            self.show_processing("数据计算中...")
            self.processor = Drying_Experiment_Processor(self.csv_file_paths)
            outputs = self.processor.process_experiment()

            self.results = self.processor.get_results()
            self.images_paths = [
                outputs["combined_plot"],
                outputs["combined_plot"].replace("combined_plots", "drying_curve"),
                outputs["combined_plot"].replace("combined_plots", "drying_rate_curve"),
            ]

            self._update_result_table()
            self.close_processing()
            messagebox.showinfo("成功", "数据处理完成！")
        except Exception as e:
            self._handle_error("数据处理错误", e)

    def _update_result_table(self):
        """更新结果表格"""
        self.result_table.clear()
        if hasattr(self.processor, "U_c") and hasattr(self.processor, "α"):
            results = [
                ("恒定干燥速率 U_c (kg/m²·h)", f"{self.processor.U_c:.4f}"),
                ("传热系数 α (kW/m²·K)", f"{self.processor.α.mean():.4f}"),
                ("初始体积流量 V_t0 (m³/s)", f"{self.processor.V_t0:.6f}"),
            ]
            for param, value in results:
                self.result_table.append([param, value])

    def plot_graph(self):
        """绘制图表"""
        if not hasattr(self, "processor"):
            messagebox.showwarning("警告", "请先处理数据！")
            return

        try:
            self.show_processing("生成图表中...")
            self.plot_frame.set_images_paths(self.images_paths)
            self.close_processing()
            messagebox.showinfo("成功", "图表生成完成！")
        except Exception as e:
            self._handle_error("图表生成错误", e)

    def _handle_error(self, context, error):
        """统一错误处理"""
        self.close_processing()
        messagebox.showerror("错误", f"{context}：{str(error)}")
        logging.error(f"{context}: {traceback.format_exc()}")
