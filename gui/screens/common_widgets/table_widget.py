# table_widget.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

from tkinter import ttk


class TableWidget(ttk.Frame):
    """通用表格数据显示组件"""

    def __init__(self, master, cols, widths, **kwargs):
        super().__init__(master, **kwargs)
        self.table = self._create_table(cols, widths)
        self.scrollbar = self._create_scrollbar()

    def update_columns(self, cols, widths=None):
        """动态更新表格列配置"""
        # 清空原有列
        self.table["columns"] = cols
        for col in self.table["columns"]:
            self.table.heading(col, text="")
            self.table.column(col, width=0)

        # 重新配置新列
        widths = widths or [100] * len(cols)  # 默认宽度为100
        for col, width in zip(cols, widths):
            self.table.column(col, width=width, anchor="center")
            self.table.heading(col, text=col)

    def _create_table(self, cols, widths):
        """创建表格核心逻辑"""
        table = ttk.Treeview(self, show="headings", columns=cols)
        for col, width in zip(cols, widths):
            table.column(col, width=width, anchor="center")
            table.heading(col, text=col)
        table.place(relx=0, rely=0, relwidth=0.95, relheight=1)
        return table

    def _create_scrollbar(self):
        """构建滚动条系统"""
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.table.yview)
        scrollbar.place(relx=0.95, rely=0, relwidth=0.05, relheight=1)
        self.table.configure(yscrollcommand=scrollbar.set)
        return scrollbar

    def append(self, args):
        """动态添加数据行（自动滚动到底部）"""
        self.table.insert("", "end", values=args)
        self.table.yview_moveto(1)

    def clear(self):
        """清空表格所有数据"""
        self.table.delete(*self.table.get_children())
