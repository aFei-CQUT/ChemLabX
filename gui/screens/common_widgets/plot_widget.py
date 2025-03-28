# plot_widget.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
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

        # 主容器采用 grid 布局
        self.grid_rowconfigure(0, weight=1)  # 绘图区域占主要空间
        self.grid_rowconfigure(1, weight=0)  # 分页控件固定高度
        self.grid_columnconfigure(0, weight=1)

        # 创建绘图区域容器
        self.plot_container = ttk.Frame(self)
        self.plot_container.grid(row=0, column=0, sticky="nsew")

        # 初始化Matplotlib画布（放在plot_container中）
        self.figure = Figure(dpi=100)
        self.figure.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        self.ax = self.figure.add_subplot(111)
        self._set_plot_style()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 创建分页控件（单独容器，放在主容器底部）
        self._create_pagination_controls()

        # 绑定窗口大小改变事件
        self.bind("<Configure>", self.resize_image)

    def _set_plot_style(self):
        """配置图表样式（无刻度、仅保留边框）"""
        # 隐藏所有刻度和标签
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.tick_params(
            axis="both",
            which="both",
            bottom=False,
            left=False,
            labelbottom=False,
            labelleft=False,
        )

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

            # 直接填充整个坐标系，使用自动调整范围
            self.ax.imshow(img, aspect="auto")
            self.ax.autoscale()  # 自动调整坐标轴范围

            self._set_plot_style()  # 确保spines样式应用
            self.canvas.draw()
            self._update_page_controls()
        except Exception as e:
            print(f"图像加载失败: {str(e)}")

    def resize_image(self, event):
        """响应窗口大小变化"""
        if event.width > 0 and event.height > 0:
            self.figure.set_size_inches(
                event.width / self.figure.dpi, event.height / self.figure.dpi
            )
            # 重新设置spines样式并调整坐标轴范围
            self._set_plot_style()
            self.ax.set_xlim(self.ax.get_xlim())  # 保持当前范围或自动调整
            self.ax.set_ylim(self.ax.get_ylim())
            self.canvas.draw()

    def _create_pagination_controls(self):
        """分页控件居中布局 + 页码美化"""
        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", pady=5)

        # 配置分页控件的样式
        self._configure_pagination_style()

        # 主容器使用 Pack 布局实现居中
        inner_frame = ttk.Frame(control_frame)
        inner_frame.pack(expand=True, anchor="center")  # 关键：让内部框架居中

        # 按钮和页码使用 Grid 布局
        inner_frame.columnconfigure(0, weight=1)
        inner_frame.columnconfigure(1, weight=0)
        inner_frame.columnconfigure(2, weight=1)

        # 上一页按钮（左侧弹性空间）
        left_space = ttk.Frame(inner_frame, width=10)
        left_space.grid(row=0, column=0, sticky="ew")

        # 按钮组
        btn_frame = ttk.Frame(inner_frame)
        btn_frame.grid(row=0, column=1, padx=5)

        self.prev_btn = ttk.Button(
            btn_frame,
            text="◀ 上一页",
            command=self.prev_page,
            style="Pagination.TButton",
        )
        self.prev_btn.pack(side="left", padx=2)

        self.page_label = ttk.Label(
            btn_frame, text="第1页/共0页", style="Pagination.TLabel", padding=(10, 0)
        )
        self.page_label.pack(side="left", padx=2)

        self.next_btn = ttk.Button(
            btn_frame,
            text="下一页 ▶",
            command=self.next_page,
            style="Pagination.TButton",
        )
        self.next_btn.pack(side="left", padx=2)

        # 右侧弹性空间
        right_space = ttk.Frame(inner_frame, width=10)
        right_space.grid(row=0, column=2, sticky="ew")

    def _configure_pagination_style(self):
        """配置分页控件样式"""
        style = ttk.Style()

        # 按钮样式：扁平化设计
        style.configure(
            "Pagination.TButton",
            font=("微软雅黑", 9),
            borderwidth=0,
            relief="flat",
            foreground="#666666",
        )
        style.map(
            "Pagination.TButton",
            foreground=[("disabled", "#CCCCCC"), ("active", "#2C7BE5")],
            background=[("disabled", "white"), ("active", "white")],
        )

        # 页码标签样式：现代感设计
        style.configure(
            "Pagination.TLabel",
            font=("微软雅黑", 10, "bold"),
            foreground="#2C7BE5",
            background="white",
            padding=(10, 2),
            bordercolor="#E5E9F2",
            relief="solid",
            anchor="center",
        )

    def set_images_paths(self, images_paths):
        self.images_paths = images_paths
        if self.images_paths:
            self.current_page = 0
            self.show_current_image()

    def _update_page_controls(self):
        total = len(self.images_paths)
        self.page_label.config(text=f"第{self.current_page+1}页/共{total}页")
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.config(
            state=(
                "normal"
                if self.current_page < len(self.images_paths) - 1
                else "disabled"
            )
        )

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_image()

    def next_page(self):
        if self.current_page < len(self.images_paths) - 1:
            self.current_page += 1
            self.show_current_image()
