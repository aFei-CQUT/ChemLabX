# extraction_screen.py

# 内部库
import sys
import os

# 动态获取项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.insert(0, project_root)

import logging
import traceback
import tkinter as tk

from tkinter import ttk, Button, filedialog, Canvas, messagebox, Toplevel, Label
from PIL import Image, ImageTk
from pathlib import Path
import pandas as pd

# 配置日志和路径
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# 导入界面配置和小部件
from gui.screens.utils.config import MAIN_FRAME_CONFIG, SCREEN_CONFIG
from gui.screens.common_widgets.plot_widget import PlotWidget
from gui.screens.common_widgets.table_widget import TableWidget
from gui.screens.common_widgets.text_widget import TextWidget

# 导入萃取处理模块
from gui.screens.calculators.extraction_calculator import Extraction_Calculator
from gui.screens.plotters.extraction_plotter import Extraction_Plotter


class Extraction_Screen(ttk.Frame):
    """
    萃取实验界面类
    -------------------------
    功能：
    1. 数据导入与展示
    2. 实验数据处理
    3. 可视化结果展示
    4. 结果打包导出
    """

    RAW_COLS = ["实验项目", "项目一", "项目二"]
    RESULT_COLS = ["参数", "项目一", "项目二", "项目三", "项目四"]

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self._init_ui()
        self._setup_bindings()

        # 实验数据相关属性
        self.calculator = None
        self.plotter = None
        self.current_page = 0
        self.image_paths = []
        self.file_dict = {"main": None, "distribution": None}  # 初始化文件字典

    def _init_ui(self):
        """初始化用户界面"""
        self._create_main_panes()
        self._create_left_panel()
        self._create_right_panel()
        self._configure_styles()

    def _create_main_panes(self):
        """创建主布局面板"""
        self.main_pane = ttk.PanedWindow(self, orient="horizontal")
        self.main_pane.pack(fill="both", expand=True)

        # 左侧控制面板
        self.left_frame = ttk.Frame(self.main_pane, width=300)
        self.main_pane.add(self.left_frame, weight=1)

        # 右侧可视化面板
        self.right_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.right_frame, weight=3)

    def _create_left_panel(self):
        """创建左侧控制面板"""
        # 按钮区域
        btn_frame = ttk.Frame(self.left_frame)
        btn_frame.pack(pady=10, fill="x")

        Button(btn_frame, text="导入数据", command=self.load_data).pack(fill="x", pady=2)
        Button(btn_frame, text="计算参数", command=self.process_data).pack(fill="x", pady=2)
        Button(btn_frame, text="生成图表", command=self.generate_plots).pack(fill="x", pady=2)
        Button(btn_frame, text="导出结果", command=self.export_results).pack(fill="x", pady=2)

        # 原始数据表格
        self.raw_table = ttk.Treeview(self.left_frame, columns=self.RAW_COLS, show="headings", height=10)
        for col in self.RAW_COLS:
            self.raw_table.heading(col, text=col)
            self.raw_table.column(col, width=100, anchor="center")
        self.raw_table.pack(fill="both", expand=True, padx=5, pady=5)

        # 结果表格
        self.result_table = ttk.Treeview(self.left_frame, columns=self.RESULT_COLS, show="headings", height=5)
        for col in self.RESULT_COLS:
            self.result_table.heading(col, text=col)
            self.result_table.column(col, width=100, anchor="center")
        self.result_table.pack(fill="both", expand=True, padx=5, pady=5)

        # 文件状态显示
        self.file_status = ttk.Label(
            self.left_frame, text="已加载文件：\n主数据：无\n分配曲线：无", wraplength=280, anchor="w"
        )
        self.file_status.pack(fill="x", pady=5)

    def _create_right_panel(self):
        """创建右侧可视化面板"""
        # 画布区域
        self.canvas = Canvas(self.right_frame, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # 分页控制
        control_frame = ttk.Frame(self.right_frame)
        control_frame.pack(pady=10)

        self.prev_btn = Button(control_frame, text="上一页", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        self.page_label = ttk.Label(control_frame, text="第1页/共0页")
        self.page_label.pack(side="left", padx=5)
        self.next_btn = Button(control_frame, text="下一页", command=self.next_page)
        self.next_btn.pack(side="left", padx=5)

    def _configure_styles(self):
        """配置界面样式"""
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Treeview", rowheight=25)

    def _setup_bindings(self):
        """设置事件绑定"""
        self.canvas.bind("<Configure>", self._resize_image)

    def _identify_file_type(self, filename):
        """根据文件名识别文件类型（增强版）"""
        filename = filename.lower()
        patterns = {
            "main": ["原始数据", "main", "数据记录", "_m", "input"],
            "distribution": ["分配曲线", "distribution", "dataset", "_d", "curve"],
        }

        for file_type, keywords in patterns.items():
            if any(kw in filename for kw in keywords):
                return file_type
        return None

    def load_data(self):
        """加载CSV格式的实验数据"""
        file_paths = filedialog.askopenfilenames(title="选择CSV数据文件", filetypes=[("CSV Files", "*.csv")])

        if not file_paths:
            return

        # 清空旧数据
        self.file_dict = {"main": None, "distribution": None}
        self.image_paths = []
        self.current_page = 0
        self._update_page_info()

        # 识别文件类型
        unrecognized = []
        for path in file_paths:
            file_type = self._identify_file_type(os.path.basename(path))
            if file_type:
                if self.file_dict[file_type]:  # 已存在同类型文件
                    confirm = messagebox.askyesno("确认", f"已加载{file_type}文件，是否替换？")
                    if not confirm:
                        continue
                self.file_dict[file_type] = path
            else:
                unrecognized.append(os.path.basename(path))

        # 显示未识别文件警告
        if unrecognized:
            self.show_warning(
                f"以下文件未能识别：\n{', '.join(unrecognized)}\n请确保文件名包含'原始数据'或'分配曲线'关键词"
            )

        # 验证必要文件
        missing = [k for k, v in self.file_dict.items() if not v]
        if missing:
            self.show_error(f"缺少必要文件类型：{', '.join(missing)}")
            return

        # 状态更新
        self._update_file_status()

        try:
            # 加载主数据
            main_df = pd.read_csv(self.file_dict["main"])
            self._update_raw_table(main_df)

        except Exception as e:
            self.show_error(f"CSV文件读取失败: {str(e)}")
            logging.error(traceback.format_exc())

    def _update_file_status(self):
        """更新文件状态显示"""
        main_file = os.path.basename(self.file_dict["main"]) if self.file_dict["main"] else "无"
        dist_file = os.path.basename(self.file_dict["distribution"]) if self.file_dict["distribution"] else "无"
        self.file_status.config(text=f"已加载文件：\n主数据：{main_file}\n分配曲线：{dist_file}")

    def _update_raw_table(self, df):
        """更新原始数据表格"""
        # 验证数据列数
        if df.shape[1] != len(self.RAW_COLS):
            self.show_error(f"数据列数不匹配！需要{len(self.RAW_COLS)}列，实际{df.shape[1]}列")
            return

        self.raw_table.delete(*self.raw_table.get_children())
        for _, row in df.iterrows():
            self.raw_table.insert("", "end", values=row.tolist())

    def process_data(self):
        """执行数据处理（增加文件存在性检查）"""
        if not all(self.file_dict.values()):
            self.show_warning("请先导入完整的数据文件！")
            return

        # 检查文件是否存在
        missing_files = []
        for ft, path in self.file_dict.items():
            if not os.path.exists(path):
                missing_files.append(ft)
        if missing_files:
            self.show_error(f"文件已丢失：{', '.join(missing_files)}")
            return

        try:
            self.show_processing("正在计算...")

            # 初始化计算模块
            self.calculator = Extraction_Calculator(
                main_file=self.file_dict["main"], distribution_file=self.file_dict["distribution"]
            )
            self.calculator.run_calculations()

            # 更新结果表格
            self._update_result_table()
            self.close_processing()

        except Exception as e:
            self.close_processing()
            self.show_error(f"数据处理失败: {str(e)}")
            logging.error(traceback.format_exc())

    def _update_result_table(self):
        """更新结果表格（优化数值显示）"""
        # 确保系数列表有4个元素
        coefficients = self.calculator.coefficients
        if len(coefficients) != 4:
            self.show_error("拟合系数数量异常！")
            return

        results = [
            [
                "分配系数的拟合项系数",
                f"{coefficients[0]:.4f}",  # x³项
                f"{coefficients[1]:.4f}",  # x²项
                f"{coefficients[2]:.4f}",  # x项
                f"{coefficients[3]:.4f}",  # 常数项
            ],
            ["操作线斜率", f"{self.calculator.k1:.2f}", f"{self.calculator.k2:.2f}", "", ""],  # 空值留白  # 空值留白
            [
                "积分结果",
                f"{self.calculator.ans3[0]:.3e}",
                f"{self.calculator.ans3[1]:.3e}",
                "",  # 空值留白
                "",  # 空值留白
            ],
        ]
        self.result_table.delete(*self.result_table.get_children())
        for row in results:
            self.result_table.insert("", "end", values=row)

    def generate_plots(self):
        """生成可视化图表"""
        if self.calculator is None:
            self.show_warning("请先进行数据处理！")
            return

        try:
            self.show_processing("正在生成图表...")

            # 初始化绘图模块
            self.plotter = Extraction_Plotter(self.calculator)
            self.plotter.create_output_dir()
            self.plotter.plot_main_curves()
            self.plotter.plot_integration_curves()

            # 获取生成的图表路径
            self.image_paths = [
                os.path.join(self.plotter.output_dir, f)
                for f in os.listdir(self.plotter.output_dir)
                if f.endswith(".png")
            ]

            self.current_page = 0
            self._update_page_info()
            self.show_current_image()
            self.close_processing()

        except Exception as e:
            self.close_processing()
            self.show_error(f"图表生成失败: {str(e)}")
            logging.error(traceback.format_exc())

    def export_results(self):
        """导出结果文件"""
        if self.plotter is None:
            self.show_warning("请先生成图表！")
            return

        try:
            self.plotter.package_results("萃取实验结果.zip")
            messagebox.showinfo("导出成功", "结果文件已保存为：萃取实验结果.zip")
        except Exception as e:
            self.show_error(f"导出失败: {str(e)}")

    def show_current_image(self):
        """显示当前页图像"""
        self.canvas.delete("all")
        if self.image_paths:
            try:
                img_path = self.image_paths[self.current_page]
                img = Image.open(img_path)
                self._display_image(img)
            except Exception as e:
                self.show_error(f"图像加载失败: {str(e)}")

    def _display_image(self, img):
        """在画布上显示图像"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 保持宽高比缩放
        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(
            (canvas_width - new_width) // 2,
            (canvas_height - new_height) // 2,
            image=self.tk_img,
            anchor="nw",
        )

    def _resize_image(self, event):
        """响应画布尺寸变化"""
        self.show_current_image()

    def prev_page(self):
        """显示上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page_info()
            self.show_current_image()

    def next_page(self):
        """显示下一页"""
        if self.current_page < len(self.image_paths) - 1:
            self.current_page += 1
            self._update_page_info()
            self.show_current_image()

    def _update_page_info(self):
        """更新分页信息"""
        total = len(self.image_paths)
        current = self.current_page + 1
        self.page_label.config(text=f"第{current}页/共{total}页")

    def show_processing(self, msg="处理中..."):
        """显示处理中窗口"""
        self.processing_win = Toplevel(self.master)
        self.processing_win.title("请稍候")
        Label(self.processing_win, text=msg).pack(padx=20, pady=10)
        self.processing_win.grab_set()

    def close_processing(self):
        """关闭处理中窗口"""
        if hasattr(self, "processing_win"):
            self.processing_win.destroy()

    def show_error(self, msg):
        """显示错误提示"""
        messagebox.showerror("错误", msg)

    def show_warning(self, msg):
        """显示警告提示"""
        messagebox.showwarning("警告", msg)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("萃取实验分析系统")
    root.geometry("1200x800")
    Extraction_Screen(root).pack(fill="both", expand=True)
    root.mainloop()
