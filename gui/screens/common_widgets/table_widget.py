# table_widget.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

import queue
import threading
from tkinter import ttk


class TableWidget(ttk.Frame):
    """通用表格数据显示组件，支持动态列配置、多线程安全操作和数据格式化"""

    def __init__(self, master, cols, widths=None, **kwargs):
        super().__init__(master, **kwargs)
        self.cols = cols
        self.widths = widths or [100] * len(cols)  # 默认宽度为100
        self.table = self._create_table()
        self.scrollbar = self._create_scrollbar()
        self.buffer = queue.Queue()  # 用于线程安全的缓冲区
        self.lock = threading.Lock()  # 用于线程安全的锁
        self.style = ttk.Style()  # 创建样式对象

    def _create_table(self):
        """创建表格核心逻辑"""
        table = ttk.Treeview(self, show="headings", columns=self.cols)
        for col, width in zip(self.cols, self.widths):
            table.column(col, width=width, anchor="center")
            table.heading(col, text=col, command=lambda c=col: self.sort_column(c))
        table.place(relx=0, rely=0, relwidth=0.95, relheight=1)
        return table

    def _create_scrollbar(self):
        """构建滚动条系统"""
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.table.yview)
        scrollbar.place(relx=0.95, rely=0, relwidth=0.05, relheight=1)
        self.table.configure(yscrollcommand=scrollbar.set)
        return scrollbar

    def update_columns(self, cols, widths=None):
        """
        动态更新表格列配置
        :param cols: 列名列表
        :param widths: 列宽列表（默认为100）
        """
        if not cols:
            return

        widths = widths or [100] * len(cols)
        self.cols = cols
        self.widths = widths

        # 清空原有列
        self.table["columns"] = cols
        for col in self.table["columns"]:
            self.table.heading(col, text="")
            self.table.column(col, width=0)

        # 重新配置新列
        for col, width in zip(cols, widths):
            self.table.column(col, width=width, anchor="center")
            self.table.heading(col, text=col, command=lambda c=col: self.sort_column(c))

    def append(self, values, auto_scroll=True):
        """
        动态添加数据行（自动滚动到底部）
        :param values: 要添加的行数据
        :param auto_scroll: 是否自动滚动到底部
        """
        with self.lock:  # 确保线程安全
            item_id = self.table.insert("", "end", values=values)
            if auto_scroll:
                self.table.yview_moveto(1)
            return item_id

    def append_thread_safe(self, values, auto_scroll=True):
        """
        在多线程环境下安全地添加数据行
        :param values: 要添加的行数据
        :param auto_scroll: 是否自动滚动到底部
        """
        self.buffer.put((values, auto_scroll))
        self.after(100, self._process_buffer)  # 每100毫秒处理一次缓冲区

    def _process_buffer(self):
        """处理缓冲区中的数据"""
        while not self.buffer.empty():
            values, auto_scroll = self.buffer.get()
            self.append(values, auto_scroll)

    def clear(self):
        """清空表格所有数据"""
        self.table.delete(*self.table.get_children())

    def set_cell_value(self, item_id, column, value):
        """
        设置单元格的值
        :param item_id: 行的ID
        :param column: 列名
        :param value: 要设置的值
        """
        self.table.set(item_id, column, value)

    def get_cell_value(self, item_id, column):
        """
        获取单元格的值
        :param item_id: 行的ID
        :param column: 列名
        :return: 单元格的值
        """
        return self.table.set(item_id, column)

    def sort_column(self, column, reverse=False):
        """
        按列排序表格数据
        :param column: 列名
        :param reverse: 是否降序排序
        """
        # 获取所有行的数据
        data = [
            (self.table.set(item, column), item) for item in self.table.get_children("")
        ]
        # 排序
        data.sort(reverse=reverse, key=lambda x: x[0])
        # 重新排列行
        for index, (_, item) in enumerate(data):
            self.table.move(item, "", index)
        # 设置排序箭头
        self.table.heading(
            column, command=lambda: self.sort_column(column, not reverse)
        )
        # 更新列标题显示排序状态
        for col in self.cols:
            if col == column:
                self.table.heading(col, text=f"{col} {'↓' if not reverse else '↑'}")
            else:
                self.table.heading(col, text=col)

    def set_font(self, font):
        """
        设置表格字体
        :param font: 字体配置（如 ("Arial", 10)）
        """
        # 创建样式
        self.style.configure("Custom.Treeview", font=font)
        self.style.configure("Custom.Treeview.Heading", font=font)  # 设置标题行字体
        self.table.configure(style="Custom.Treeview")

    def set_foreground(self, color):
        """
        设置表格前景色
        :param color: 前景色（如 "black"）
        """
        self.style.configure("Custom.Treeview", foreground=color)

    def set_background(self, color):
        """
        设置表格背景色
        :param color: 背景色（如 "white"）
        """
        self.style.configure("Custom.Treeview", background=color)

    def set_row_colors(self, even_color=None, odd_color=None):
        """
        设置行的交替颜色
        :param even_color: 偶数行颜色
        :param odd_color: 奇数行颜色
        """
        for i, item in enumerate(
            self.table.get_children(""), start=1
        ):  # 从1开始计数，确保偶数行和奇数行正确
            color = even_color if i % 2 == 0 else odd_color
            if color:
                self.table.tag_configure(f"row_{i}", background=color)
                self.table.item(item, tags=(f"row_{i}",))

    def auto_resize_columns(self):
        """自动调整列宽以适应内容"""
        for col in self.cols:
            max_width = max(
                self.table.column(col, "width"),
                len(col) * 10,  # 列名的宽度
                max(
                    (
                        len(str(self.table.set(item, col))) * 10
                        for item in self.table.get_children("")
                    ),
                    default=0,
                ),  # 内容的宽度
            )
            self.table.column(col, width=max_width)
