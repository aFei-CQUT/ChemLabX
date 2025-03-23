# spin_entries_widget.py

# 内置库
import sys
import os

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

from tkinter import ttk, StringVar

# 导入配置和通用数学工具
from gui.screens.utils.config import DATA_CONFIG, FLAT_SUBFRAME_CONFIG
from gui.screens.maths.common_maths import find_start_end_point


class SpinEntriesWidget(ttk.Frame):
    """数值输入框集合组件（支持起始点/终止点配置）"""

    class SpinEntry(ttk.Frame):
        def __init__(self, master, name, default="0", **kwargs):
            """初始化数值输入框组件"""
            super().__init__(master, **kwargs)
            self.name = name
            self.label = ttk.Label(self, text=name)
            self.label.place(relx=0, rely=0, relwidth=0.5, relheight=1)

            # 数值存储变量
            self.cached = StringVar()
            self.cached.set(default)
            self.var = StringVar()
            self.var.set(default)

            # 构建Spinbox控件
            self.entry = ttk.Spinbox(
                self,
                textvariable=self.var,
                from_=0,
                to=0,
                increment=1,
                command=self.check_memory,
            )
            self.entry.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
            self._bind_entry_events()

        def _bind_entry_events(self):
            """绑定焦点事件"""
            self.entry.bind("<FocusIn>", lambda *args: self._bind_return())
            self.entry.bind("<FocusOut>", lambda *args: self._unbind_return())

        def _bind_return(self):
            """绑定回车键验证"""
            self.bind("<Return>", self.check_memory)

        def _unbind_return(self):
            """解绑回车键并触发验证"""
            self.unbind("<Return>")
            self.check_memory()

        def check_memory(self):
            """数值合法性验证与状态更新"""
            if not self.var.get().isdigit():
                self.var.set(self.cached.get())
            elif hasattr(DATA_CONFIG["screen"], "spinEntries") and not DATA_CONFIG["screen"].spinEntries.check_memory():
                self.var.set(self.cached.get())
            else:
                self.cached.set(self.var.get())
                # 触发全局更新
                DATA_CONFIG["screen"].change_entry()
                DATA_CONFIG["screen"].calc_regression()
                DATA_CONFIG["screen"].plot_regression()
                DATA_CONFIG["screen"].plot_frame.show()

        def set_state(self, state):
            """设置控件状态"""
            self.entry.config(state=state)

        def set_var(self, val):
            """直接设置变量值"""
            self.var.set(val)
            self.cached.set(val)

        def set_from_to(self, from_, to):
            """更新数值范围限制"""
            self.entry.config(from_=from_, to=to)

    def __init__(self, master, pairs, labels=None, **kwargs):
        """初始化数值输入框集合
        :param pairs: 输入框对的数量
        :param labels: 每对输入框的标签列表，如["起始点", "终点"]
        """
        super().__init__(master, **kwargs)
        self.entries = []
        self.entries_table = {}
        self.labels = labels or ["Start", "End"]  # 默认标签
        self.PAIRS = pairs  # 初始化PAIRS属性

        self._create_spin_entries(pairs)
        self._create_buttons(pairs)

    def _create_spin_entries(self, pairs):
        """构建成对输入框布局"""
        for i in range(pairs):
            row_frame = ttk.Frame(self)
            row_frame.place(relx=0, rely=i * 0.25, relwidth=1, relheight=0.25)

            # 使用自定义标签或默认标签
            start_label = f"{self.labels[0]} {i+1}" if len(self.labels) >= 1 else f"Start {i+1}"
            end_label = f"{self.labels[1]} {i+1}" if len(self.labels) >= 2 else f"End {i+1}"

            # 创建成对输入框
            self.entries.append(self.SpinEntry(row_frame, start_label))
            self.entries[-1].place(relx=0, rely=0, relwidth=0.5, relheight=1)
            self.entries.append(self.SpinEntry(row_frame, end_label))
            self.entries[-1].place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

        # 建立名称索引
        for entry in self.entries:
            self.entries_table[entry.name] = entry

    def _create_buttons(self, pairs):
        """构建操作按钮区域"""
        buttons = ttk.Frame(self)
        buttons.place(relx=0, rely=pairs * 0.25, relwidth=1, relheight=0.25)

        # 重置按钮
        button_left = ttk.Frame(buttons, **FLAT_SUBFRAME_CONFIG)
        button_left.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        self.button_remake = ttk.Button(button_left, text="重置(Ctrl-Z)", command=self.remake_file)
        self.button_remake.place(relx=0, rely=0, relwidth=1, relheight=1)

        # 计算按钮
        button_right = ttk.Frame(buttons, **FLAT_SUBFRAME_CONFIG)
        button_right.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        self.button_integrate = ttk.Button(button_right, text="计算(Ctrl-D)", command=self.calc)
        self.button_integrate.place(relx=0, rely=0, relwidth=1, relheight=1)

    def check_memory(self):
        """全局数值关系验证"""
        if int(self.entries[0].var.get()) < 0:
            return False
        if "csv_len" in DATA_CONFIG and DATA_CONFIG["csv_len"] != -1:
            if DATA_CONFIG["csv_len"] <= int(self.entries[-1].var.get()):
                return False
        for i in range(1, len(self.entries)):
            if int(self.entries[i - 1].var.get()) >= int(self.entries[i].var.get()):
                return False
        return True

    def dump(self):
        """返回所有条目的值"""
        return {entry.name: int(entry.cached.get()) for entry in self.entries}

    def set_var(self, key, value):
        """设置特定条目的值"""
        self.entries_table[key].set_var(value)

    def set_states(self, state):
        """设置所有条目的状态"""
        for entry in self.entries:
            entry.set_state(state)

    def set_from_to(self, name, from_, to):
        """设置条目的上下限"""
        self.entries_table[name].set_from_to(from_, to)

    def remake_file(self):
        """重置文件数据并进行计算"""

        # 调用maths_filteration中的函数，获取起点和终点列表
        # 该函数基于传入的CSV数据、模式、时间范围和标准限制计算数据的起点和终点位置
        self.start_end_points_list = find_start_end_point(
            DATA_CONFIG["csv"],  # CSV数据
            DATA_CONFIG["mode"].get(),  # 获取当前模式
            DATA_CONFIG["time_lower_limit"],  # 时间下限
            DATA_CONFIG["time_upper_limit"],  # 时间上限
            DATA_CONFIG["std_limit"],  # 标准差限制
        )

        # 如果未找到有效的起点和终点数据，则返回
        if self.start_end_points_list is None:
            return

        # 初始化一个空字典，用于存储起点和终点的映射关系
        self.start_end_points_dict = {}

        # 将该字典存储到全局配置中，方便其他地方访问
        DATA_CONFIG["screen"].start_end_points_dict = self.start_end_points_dict

        # 遍历起点和终点的列表，将它们存储到字典中
        # 如果索引是偶数则是“Start”，奇数是“End”
        for i, point in enumerate(self.start_end_points_list):
            self.start_end_points_dict[f"{'End' if i & 1 else 'Start'} {(i >> 1) + 1}"] = (  # 使用位运算计算每组的编号
                point
            )

        # 更新起点和终点的数据
        self._update_start_end_points()

        # 线性回归计算
        # 触发界面更新，进行回归分析
        DATA_CONFIG["screen"].change_entry()  # 更新输入框内容
        DATA_CONFIG["screen"].calc_regression()  # 进行回归计算
        DATA_CONFIG["screen"].plot_regression()  # 绘制回归结果
        DATA_CONFIG["screen"].plot_frame.show()  # 显示图表

    def _update_start_end_points(self):
        """更新起终点字典（适配自定义标签）"""
        # 获取配置的标签，如果没有配置则使用默认"Start"/"End"
        start_label = self.labels[0] if len(self.labels) >= 1 else "Start"
        end_label = self.labels[1] if len(self.labels) >= 2 else "End"

        # 生成键名模板函数
        def start_key(i):
            return f"{start_label} {i}"

        def end_key(i):
            return f"{end_label} {i}"

        # 填充缺失的键值
        for i in range(self.PAIRS + 1):
            if not end_key(i) in self.start_end_points_dict:
                self.start_end_points_dict[end_key(i)] = self._calculate_end(i)
            if not start_key(i + 1) in self.start_end_points_dict:
                self.start_end_points_dict[start_key(i + 1)] = self._calculate_start(i)

        # 更新界面组件值及范围限制
        for i in range(1, self.PAIRS + 1):
            # 设置输入框数值
            self.set_var(start_key(i), str(self.start_end_points_dict[start_key(i)]))
            self.set_var(end_key(i), str(self.start_end_points_dict[end_key(i)]))

            # 设置范围限制
            self.set_from_to(
                start_key(i), self.start_end_points_dict[end_key(i - 1)] + 1, self.start_end_points_dict[end_key(i)] - 1
            )
            self.set_from_to(
                end_key(i),
                self.start_end_points_dict[start_key(i)] + 1,
                self.start_end_points_dict[start_key(i + 1)] - 1,
            )

        # 解锁按钮
        self.button_remake.config(state="normal")
        self.button_integrate.config(state="normal")

    def _calculate_end(self, i):
        """计算终点"""
        if i == 0:
            return -1
        elif i == self.PAIRS:
            return DATA_CONFIG["csv_len"] - 1
        else:
            return int(DATA_CONFIG["csv_len"] * (i * 2 - 1) / (self.PAIRS * 2 - 1))

    def _calculate_start(self, i):
        """计算起点"""
        if i == self.PAIRS:
            return DATA_CONFIG["csv_len"]
        else:
            return int(DATA_CONFIG["csv_len"] * (i * 2) / (self.PAIRS * 2 - 1))

    def calc(self):
        """积分与其他值计算"""
        DATA_CONFIG["screen"].calc_integration()
        DATA_CONFIG["screen"].plot_regression()
        DATA_CONFIG["screen"].plot_integration()
        DATA_CONFIG["screen"].plot_frame.show()
        DATA_CONFIG["screen"].calc_result()
