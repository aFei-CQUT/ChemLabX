# 内置库
import sys
import os
import time
import csv

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.insert(0, project_root)

from tkinter import ttk
from tkinter import *
import tkinter.filedialog as filedialog
from tkinter.messagebox import showinfo, showwarning

# from tkinter.scrolledtext import ScrolledText

# 根据不同的实验这里为不同的文件，根据不同的实验这里为不同的类
# 这里以过滤实验为例，具体的，应该让用户一开始选择进入的实验界面，用if判断选择
from gui.screens.filteration_screen import Filteration_Screen
from gui.screens.utils.config import (
    DATA_CONFIG,
    DEFAULT_DATA_VALUE,
    FLAT_SUBFRAME_CONFIG,
    MAIN_FRAME_CONFIG,
)
from gui.screens.utils.expserial import EasySerial, getComPorts

from gui.screens.common_widgets.string_entries_widget import StringEntriesWidget


class Data_Record_Screen:
    """
    通用数据记录界面基类
    用于记录从串口接收到的数据并保存到CSV文件或者人为导入csv文件获取数据（不过导入csv文件这一点在各个实验数据处理界面实现即可，
    因为实验数据结构的不同，这里不必实现）。

    相应的组件、按钮、快捷键、分区应该有一些基本的，不像现在是个白板。
    """

    def __init__(self):
        # 通用设置
        self.comport = None
        self.comport_name = None
        self.all_comports = []
        self.start_time = 0
        self.end_time = 0
        self.temp_Delta_t = []
        self.temp_Delta_T = []
        self.temp_file_name = "tempfile.tmp"
        self.temp_file = None
        self.during_measuring = False
        self.csv_data = []
        self.csv_path = ""
        self.t1 = "0.000"
        self.t2 = "0.000"

    def init_states(self):
        """
        初始化状态，禁用一些按钮
        """
        self.button_data_start.config(state="disabled")
        self.button_data_stop.config(state="disabled")
        self.button_save.config(state="disabled")

    def get_comports(self):
        """
        获取可用的串口并选择其中一个打开。
        """
        self.all_comports = getComPorts(select=True, timeout=DATA_CONFIG["port_timeout"])

        # 更新串口选择菜单
        if self.all_comports:
            if self.comport_name.get() not in self.all_comports:
                self.comport_name.set(self.all_comports[0])
            self.change_port(self.comport_name.get())
        else:
            self.comport_name.set("请刷新串口")
            if self.comport:
                self.comport.close()
            self.comport = None

    def change_port(self, event):
        """
        切换串口
        """
        self.comport.close() if self.comport else None
        self.comport = None
        self.comport_name.set(event)
        self.comport = EasySerial(event)

        try:
            # 打开串口并写入临时文件
            self.temp_file = open(
                os.path.join(DATA_CONFIG["py_path"], self.temp_file_name),
                "w",
                encoding="UTF-8",
            )
            self.temp_file.write("time(s),Delta_T(K)\n")
            self.temp_file.flush()
            self.start_time = time.time()
            self.comport.open()
        except Exception as e:
            showwarning("串口错误", f"串口打开失败: {str(e)}")
            self.comport.close()

    def data_start(self):
        """
        开始记录数据
        """
        self.temp_file.close()
        self.temp_file = open(
            os.path.join(DATA_CONFIG["py_path"], self.temp_file_name),
            "w",
            encoding="UTF-8",
        )
        self.temp_file.write("time(s),Delta_T(K)\n")
        self.temp_file.flush()

        self.start_time = time.time()

        # 初始化数据
        self.csv_data = [
            ["time(s)", "Delta_T(K)"],
        ]

        self.during_measuring = True

        self.text_frame.append(f"{time.strftime('%Y.%m.%d %H:%M:%S', time.localtime())} 开始记录\n")
        self.text_frame.see("end")

    def data_end(self):
        """
        停止记录数据
        """
        self.temp_file.write("stop recording\n")
        self.temp_file.flush()
        self.csv_state = False
        self.text_frame.append(f"{time.strftime('%Y.%m.%d %H:%M:%S', time.localtime())} 停止记录\n")
        self.text_frame.see("end")
        self.button_data_stop.config(state="disabled")
        self.button_save.config(state="normal")

    def data_save(self):
        """
        保存数据到CSV文件
        """
        self.csv_path = filedialog.asksaveasfilename(
            title="保存数据",
            initialfile=f"{time.strftime('%Y%m%d%H%M%S', time.localtime())}data.csv",
            filetypes=[("CSV", ".csv")],
        )

        if not self.csv_path:
            return

        with open(self.csv_path, "w", encoding="UTF-8", newline="") as f:
            csv.writer(f).writerows(self.csv_data)

        showinfo(title="提示", message=f"数据成功保存至{self.csv_path}")

        self.text_frame.append(f"{time.strftime('%Y.%m.%d %H:%M:%S', time.localtime())} 数据保存成功\n")
        self.text_frame.see("end")

    def read_comport(self):
        """
        从串口读取数据
        """
        try:
            # 读取串口数据
            Delta_T = self.comport.read()
            self.end_time = time.time()
            Delta_t = self.end_time - self.start_time

            # 将数据写入临时文件和csv文件
            self.temp_file.write(f"{Delta_t:.3f},{Delta_T:.3f}\n")
            self.temp_file.flush()

            self.csv_data.append([f"{Delta_t:.3f}", f"{Delta_T:.3f}"])

            # 更新UI表格
            self.table_frame.append((f"{Delta_t:.3f}", f"{Delta_T:.3f}"))

            # 更新数据存储
            self.temp_Delta_t.append(Delta_t)
            self.temp_Delta_T.append(Delta_T)

            # 绘图更新
            self.plot_frame.clear()
            self.plot_frame.plot(self.temp_Delta_t, self.temp_Delta_T, color="#1F77B4")
            self.plot_frame.show()

        except Exception as e:
            showwarning("串口读取错误", f"串口读取数据失败: {str(e)}")
