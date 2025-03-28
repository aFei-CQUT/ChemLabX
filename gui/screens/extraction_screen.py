# extraction_screen.py

# 内部库
import sys
import os
import logging
import traceback
from tkinter import filedialog, messagebox, Canvas, Toplevel
from tkinter import ttk
from PIL import Image, ImageTk
import pandas as pd

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

# 导入基类和组件
from gui.screens.common_screens.base_screen import Base_Screen
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.processors.extraction_expriment_processor import (
    ExtractionExperimentProcessor,
)


class Extraction_Screen(Base_Screen):
    """萃取实验界面（继承自Base_Screen基类）"""

    RAW_COLS = ["实验项目", "项目一", "项目二"]
    RESULT_COLS = ["参数", "项目一", "项目二", "项目三", "项目四"]

    def __init__(self, window):
        super().__init__(window)
        self.processor = None
        self.file_dict = {"origin": None, "distribution": None}
        self.images_paths = []

        # 初始化组件调整
        self._adjust_components()
        self._update_button_states()

    def _adjust_components(self):
        """调整基类组件布局"""
        # 调整表格高度
        self.raw_table.pack_forget()
        self.result_table.pack_forget()
        self.raw_table = TableWidget(
            self.left_frame, self.RAW_COLS, [150, 120, 120], height=15
        )
        self.result_table = TableWidget(
            self.left_frame, self.RESULT_COLS, [150, 100, 100, 100, 100], height=8
        )
        self.raw_table.pack(fill="both", expand=True, padx=5, pady=5)
        self.result_table.pack(fill="both", expand=True, padx=5, pady=5)

    def _update_button_states(self):
        """更新按钮状态（继承基类功能）"""
        data_loaded = all(self.file_dict.values())
        btn = self._find_button("data_btn_frame", 1)
        btn["state"] = "normal" if data_loaded else "disabled"

    def _find_button(self, frame_name, column):
        """查找指定按钮（增强容错）"""
        frame = self.left_frame.nametowidget(frame_name)
        return frame.grid_slaves(row=0, column=column)[0]

    # ---------------------------- 核心方法重写 ----------------------------
    def load_data(self):
        """加载双CSV文件数据"""
        file_paths = filedialog.askopenfilenames(
            title="选择萃取实验文件", filetypes=[("CSV文件", "*.csv")]
        )

        if not file_paths:
            return

        try:
            self.file_dict = self._classify_files(file_paths)
            self._validate_files()

            # 更新原始数据表格
            origin_df = pd.read_csv(self.file_dict["origin"])
            self.raw_table.clear()
            for idx, row in origin_df.iterrows():
                self.raw_table.append([idx + 1, *row.values.tolist()])

            self._update_button_states()

        except Exception as e:
            messagebox.showerror("错误", f"文件加载失败: {str(e)}")
            self.logger.error(f"文件加载异常: {traceback.format_exc()}")

    def _classify_files(self, paths):
        """智能分类文件"""
        file_dict = {"origin": None, "distribution": None}
        key_patterns = {
            "origin": ["原始数据", "origin", "_m"],
            "distribution": ["分配曲线", "distribution", "_d"],
        }

        for path in paths:
            fname = os.path.basename(path).lower()
            for key, patterns in key_patterns.items():
                if any(p in fname for p in patterns) and not file_dict[key]:
                    file_dict[key] = path
                    break
        return file_dict

    def _validate_files(self):
        """验证文件完整性"""
        missing = [k for k, v in self.file_dict.items() if not v]
        if missing:
            raise ValueError(
                f"缺少必需文件: {', '.join(missing)}\n"
                "命名应包含以下关键词:\n"
                "- 原始数据文件: 原始数据/origin/_m\n"
                "- 分配曲线文件: 分配曲线/distribution/_d"
            )

    def process_data(self):
        """执行数据处理流程"""
        if not all(self.file_dict.values()):
            messagebox.showwarning("警告", "请先完整加载原始数据和分配曲线文件")
            return

        try:
            self.show_processing("数据处理中...")
            self.processor = ExtractionExperimentProcessor(
                origin_file=self.file_dict["origin"],
                distribution_file=self.file_dict["distribution"],
            )
            self.processor.run()
            self._update_result_table()

        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")
            self.logger.error(f"处理异常: {traceback.format_exc()}")
        finally:
            self.close_processing()

    def _update_result_table(self):
        """更新结果表格数据"""
        if not self.processor.calculator:
            return

        calc = self.processor.calculator
        self.result_table.clear()
        results = [
            ["分配系数", *[f"{x:.4f}" for x in calc.coefficients]],
            ["操作线斜率", f"{calc.k1:.2f}", f"{calc.k2:.2f}", "", ""],
            ["积分结果", *[f"{x:.3e}" for x in calc.ans3], "", ""],
        ]
        for row in results:
            self.result_table.append(row)

    def plot_graph(self):
        """显示生成的图表"""
        if not self.processor or not self.processor.output_dir:
            messagebox.showwarning("警告", "请先完成数据处理")
            return

        try:
            self.show_processing("加载图表中...")
            output_dir = self.processor.output_dir
            self.images_paths = [
                os.path.join(output_dir, f)
                for f in sorted(os.listdir(output_dir))  # 添加排序保证显示顺序
                if f.lower().endswith(".png")
            ]

            # 添加路径验证
            if not self.images_paths:
                raise FileNotFoundError("输出目录中未找到PNG文件")

            # 直接调用基类方法
            self.plot_frame.set_images_paths(self.images_paths)
            self.plot_frame.show_current_image()  # 主动触发显示

        except Exception as e:
            messagebox.showerror("错误", f"图表加载失败: {str(e)}")
            self.logger.error(f"图表异常: {traceback.format_exc()}")
        finally:
            self.close_processing()

    def _safe_close(self):
        """安全关闭资源"""
        if hasattr(self, "processor"):
            del self.processor
        super()._safe_close()
