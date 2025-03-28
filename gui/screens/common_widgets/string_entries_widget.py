# string_entries_widget.py

# 内置库
import logging
import sys
import os
import re
import tkinter as tk

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)

from tkinter import ttk, StringVar


class StringEntriesWidget(ttk.Frame):
    """统一输入框宽度的输入组件"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.entries = []
        self.vars = []
        self.entries_config = []

        # 主容器使用网格布局
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        # 配置网格列权重
        self.main_frame.columnconfigure(0, weight=1)  # 标签列
        self.main_frame.columnconfigure(1, weight=1)  # 输入框列

    def update_entries(self, entries_config):
        """更新输入框配置"""
        # 清空现有组件
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # 创建输入行
        for row_idx, config in enumerate(entries_config):
            # 标签（居中）
            label = ttk.Label(
                self.main_frame, text=config.get("label", ""), anchor="center"
            )
            label.grid(row=row_idx, column=0, padx=5, pady=3, sticky="ew")

            # 输入框（右对齐）
            var = StringVar(value=config.get("default", ""))
            entry = ttk.Entry(self.main_frame, textvariable=var)
            entry.grid(row=row_idx, column=1, padx=5, pady=3, sticky="ew")

            # 验证绑定
            if pattern := config.get("validation_pattern"):
                entry.bind(
                    "<FocusOut>", lambda e, p=pattern, v=var: self._validate_input(p, v)
                )

            self.entries.append(entry)
            self.vars.append(var)

        # 添加空行撑开布局
        self.main_frame.rowconfigure(len(entries_config), weight=1)

    def _validate_input(self, pattern, var):
        value = var.get()
        if pattern and value and not re.match(pattern, value):
            logging.warning(f"输入验证失败: '{value}' 不符合正则表达式 '{pattern}'")
            self.event_generate("<<ValidationFailed>>")  # 验证失败事件
            return False
        self.event_generate("<<ParameterChange>>")  # 验证成功事件
        return True

    def get_values(self):
        return [var.get() for var in self.vars]

    def set_values(self, values):
        if len(values) != len(self.vars):
            logging.error("值数量不匹配")
            return False
        for var, val in zip(self.vars, values):
            var.set(val)
        return True

    def clear(self):
        [var.set("") for var in self.vars]

    def validate_all(self):
        return all(
            self._validate_input(c.get("validation_pattern"), v)
            for c, v in zip(self.entries_config, self.vars)
        )
