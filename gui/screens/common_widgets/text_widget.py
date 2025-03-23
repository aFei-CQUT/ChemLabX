# text_widget.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class TextWidget(ttk.Frame):
    """带滚动条的多行文本框组件"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.textbox = self._create_textbox()

    def _create_textbox(self):
        """创建并配置滚动文本框"""
        textbox = ScrolledText(self)
        textbox.place(relx=0, rely=0, relwidth=1, relheight=1)
        textbox.config(state="disabled")  # 初始禁用编辑
        return textbox

    def _enable_textbox(self):
        """临时启用文本框编辑"""
        self.textbox.config(state="normal")

    def _disable_textbox(self):
        """完成操作后重新禁用编辑"""
        self.textbox.config(state="disabled")

    def append(self, s):
        """追加文本内容（线程安全）"""
        self._enable_textbox()
        self.textbox.insert("end", s)
        self._disable_textbox()

    def clear(self):
        """清空文本框内容"""
        self._enable_textbox()
        self.textbox.delete(1.0, "end")
        self._disable_textbox()

    def see(self, pos):
        """滚动到指定位置（如'end'表示底部）"""
        self.textbox.see(pos)
