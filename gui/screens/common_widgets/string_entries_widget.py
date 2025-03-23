# string_entries_widget.py

# 内置库
import logging
import sys
import os
import re

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

from tkinter import ttk, StringVar

# 导入配置
from gui.screens.utils.config import ENTRY_LABEL_CONFIG


class StringEntriesWidget(ttk.Frame):
    """动态输入框集合组件（支持数值验证和依赖关系）"""

    class CachedStringEntryWidget(ttk.Frame):
        def __init__(self, master, name, default="", text=None, **kwargs):
            super().__init__(master, **kwargs)
            self.name = name
            self.text = name if text is None else text

            # 标签布局
            self.label = ttk.Label(self, text=self.text, **ENTRY_LABEL_CONFIG)
            self.label.place(relx=0, rely=0, relwidth=0.5, relheight=1)

            # 输入值缓存系统
            self.cached = StringVar(value=default)
            self.var = StringVar(value=default)

            # 输入框构建
            self.entry = ttk.Entry(self, textvariable=self.var)
            self.entry.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
            self._bind_focus_events()

        def _bind_focus_events(self):
            """管理焦点事件绑定"""
            self.entry.bind("<FocusIn>", lambda *args: self._bind_return())
            self.entry.bind("<FocusOut>", lambda *args: self._unbind_return())

        def _bind_return(self):
            """绑定回车验证"""
            self.bind("<Return>", self.validate_input)

        def _unbind_return(self):
            """解绑并触发验证"""
            self.unbind("<Return>")
            self.validate_input()

        def validate_input(self):
            """通用输入验证逻辑"""

            def is_number(s):
                try:
                    float(s)
                    return True
                except ValueError:
                    return False

            # 保留数字和基础运算符
            raw_value = re.sub(r"[^\d+*/().-]+", "", self.var.get())
            self.var.set(raw_value)

            # 算式解析逻辑
            if raw_value != self.cached.get():
                if not is_number(raw_value):
                    try:
                        calculated = str(eval(raw_value))
                        self.var.set(calculated)
                        self.cached.set(calculated)
                        self.master.change()  # 触发全局更新
                    except:
                        self.var.set(self.cached.get())
                else:
                    self.cached.set(raw_value)
                    self.master.change()

        def set_state(self, state):
            """控件状态管理"""
            self.entry.config(state=state)

        def set_var(self, value):
            """直接设置变量值"""
            self.var.set(value)
            self.cached.set(value)

    def __init__(
        self,
        master,
        names: list,
        defaults: dict = {},
        dependences=[],
        texts: dict = {},
        cols: int = 2,
        validate_types: dict = None,  # 显式声明参数
        **kwargs,
    ):
        # 过滤掉自定义参数后再传给父类
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["validate_types"]}
        super().__init__(master, **filtered_kwargs)

        # 存储验证类型配置
        self.validate_types = validate_types if validate_types is not None else {}

        self.entries = [self.CachedStringEntryWidget(self, name, default=defaults.get(name, "")) for name in names]
        self.entries_table = {entry.name: entry for entry in self.entries}
        self._setup_dependencies(dependences)
        self._layout_entries(cols)

    def get_validated_values(self):
        """获取经过类型验证的输入值字典"""
        validated = {}
        for entry in self.entries:
            name = entry.name
            raw_value = entry.cached.get()
            val_type = self.validate_types.get(name, str)  # 默认为字符串类型

            try:
                # 处理空字符串的情况
                if raw_value.strip() == "":
                    validated[name] = None
                    continue

                # 类型转换
                validated[name] = val_type(raw_value)
            except (ValueError, TypeError) as e:
                logging.error(f"值转换失败: {name}={raw_value} ({val_type}): {str(e)}")
                validated[name] = None  # 或根据需求抛出异常
        return validated

    def _setup_dependencies(self, dependences):
        """设置字段间依赖关系"""

        def create_trace(affected, func, args):
            def update_affected(*_):
                result = func(*[self.entries_table[arg].cached.get() for arg in args])
                self.entries_table[affected].var.set(result)
                self.entries_table[affected].cached.set(result)

            return update_affected

        for source, target, func, args in dependences:
            self.entries_table[source].cached.trace_add("write", create_trace(target, func, args))

    def _layout_entries(self, cols):
        """动态网格布局"""
        rows = (len(self.entries) + cols - 1) // cols
        for idx, entry in enumerate(self.entries):
            entry.place(relx=(idx % cols) / cols, rely=(idx // cols) / rows, relwidth=1 / cols, relheight=1 / rows)

    def clear(self):
        """清空所有条目的值"""
        for entry in self.entries:
            entry.set_var("")

    def dump(self):
        """返回所有条目的值"""
        return {entry.name: entry.cached.get() for entry in self.entries}

    def set_states(self, state, names):
        """设置特定条目的状态"""
        for name in names:
            self.entries_table[name].set_state(state)

    def set_all_states(self, state):
        """设置所有条目的状态"""
        for entry in self.entries:
            entry.set_state(state)

    def set_value(self, key, value):
        """设置特定条目的值"""
        if key in self.entries_table:
            self.entries_table[key].set_var(value)
