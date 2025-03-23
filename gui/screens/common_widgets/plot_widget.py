# plot_widget.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

from tkinter import ttk
from PIL import Image as pilImage, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.screens.utils.config import DATA_CONFIG


class PlotWidget(ttk.Frame):
    def __init__(self, master, **kwargs):
        """
        初始化绘图控件
        :param master: 父容器
        :param kwargs: ttk.Frame的其他配置参数
        """
        super().__init__(master, **kwargs)

        # 强制填满父容器
        self.pack_propagate(False)
        self.grid_propagate(False)

        # 创建Matplotlib图形（最小化边距）
        self.figure = Figure(dpi=100)
        self.figure.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)

        # 创建子图并配置样式
        self.ax = self.figure.add_subplot(111)
        self._set_plot_style()

        # 创建并布置画布
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 初始化图像相关属性
        self.images_paths = []
        self.current_page = 0

        # 创建分页控件
        self._create_pagination_controls()

        # 绑定窗口大小改变事件
        self.bind("<Configure>", self.resize_image)

    def _set_plot_style(self):
        """配置图表样式（无刻度、仅保留边框）"""
        # 隐藏所有刻度和标签
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.tick_params(axis="both", which="both", bottom=False, left=False, labelbottom=False, labelleft=False)

        # 设置边框样式
        for spine in self.ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(2)  # 加粗边框
            spine.set_color("black")  # 黑色边框

    def clear(self):
        """清除当前图表内容"""
        self.ax.clear()
        self._set_plot_style()
        self.canvas.draw()

    def plot(self, x, y, **kwargs):
        """绘制折线图"""
        self.ax.plot(x, y, **kwargs)
        self._adjust_plot_limits(x, y)

    def scatter(self, x, y, **kwargs):
        """绘制散点图"""
        self.ax.scatter(x, y, **kwargs)
        self._adjust_plot_limits(x, y)

    def _adjust_plot_limits(self, x, y):
        """自动调整坐标范围使图形填满绘图区"""
        if len(x) > 0 and len(y) > 0:
            x_padding = (max(x) - min(x)) * 0.05
            y_padding = (max(y) - min(y)) * 0.05
            self.ax.set_xlim(min(x) - x_padding, max(x) + x_padding)
            self.ax.set_ylim(min(y) - y_padding, max(y) + y_padding)
        self.canvas.draw()

    def show_current_image(self):
        """显示当前图像（填满整个绘图区）"""
        if not self.images_paths or self.current_page >= len(self.images_paths):
            return

        try:
            img = pilImage.open(self.images_paths[self.current_page])
            self.clear()

            # 直接填充整个坐标系
            self.ax.imshow(img, extent=[0, 1, 0, 1], aspect="auto")
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)

            self.canvas.draw()
            self._update_page_controls()
        except Exception as e:
            print(f"图像加载失败: {str(e)}")

    def resize_image(self, event):
        """响应窗口大小变化"""
        if event.width > 0 and event.height > 0:
            self.figure.set_size_inches(event.width / self.figure.dpi, event.height / self.figure.dpi)
            self.canvas.draw()

    # 保留其他原有方法（分页控制等）...
    def _create_pagination_controls(self):
        """创建分页控制按钮组件"""
        control_frame = ttk.Frame(self)
        control_frame.pack(side="bottom", fill="x", pady=2)

        self.prev_btn = ttk.Button(control_frame, text="上一页", command=self.prev_page, state="disabled")
        self.prev_btn.pack(side="left", padx=5)

        self.page_label = ttk.Label(control_frame, text="第1页/共0页")
        self.page_label.pack(side="left", padx=5)

        self.next_btn = ttk.Button(control_frame, text="下一页", command=self.next_page, state="disabled")
        self.next_btn.pack(side="left", padx=5)

    def set_images_paths(self, images_paths):
        self.images_paths = images_paths
        if self.images_paths:
            self.current_page = 0
            self.show_current_image()

    def _update_page_controls(self):
        total = len(self.images_paths)
        self.page_label.config(text=f"第{self.current_page+1}页/共{total}页")
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.config(state="normal" if self.current_page < len(self.images_paths) - 1 else "disabled")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_image()

    def next_page(self):
        if self.current_page < len(self.images_paths) - 1:
            self.current_page += 1
            self.show_current_image()
