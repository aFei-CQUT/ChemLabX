# smooth_resize_window.py

# 内置库
import sys
import os
import random
import tkinter as tk

import numpy as np

# 动态获取路径（保持不变）
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)


class Smooth_Resize_Window:
    def __init__(self, window):
        self.window = window
        self.window.update_idletasks()

        # 保存初始基准尺寸
        self.base_width = self.window.winfo_width()
        self.base_height = self.window.winfo_height()

        # 当前尺寸跟踪（使用浮点数保持精度）
        self.window_width = float(self.base_width)
        self.window_height = float(self.base_height)

        self.window.minsize(600, 400)

        # 抖动控制参数（调整为整数）
        self.max_jitter = 1  # 最大抖动幅度（整数像素）
        self.tolerance = 0.2  # 停止阈值（使用浮点判断）
        self.fixed_increment = 0.5  # 调整步长（浮点计算）

    def smooth_transition(self, current_size, target_size):
        """支持浮点数运算的过渡算法"""
        delta = target_size - current_size
        if abs(delta) <= self.fixed_increment:
            return target_size
        return current_size + np.sign(delta) * self.fixed_increment

    def start(self, interval=50, smooth_factor=10):
        """启动智能抖动调整"""
        # 生成基准尺寸附近的随机目标（保持整数最终值）
        target_width = self.base_width + random.randint(
            -self.max_jitter, self.max_jitter
        )
        target_height = self.base_height + random.randint(
            -self.max_jitter, self.max_jitter
        )

        # 使用浮点数进行平滑计算
        self.window_width = self.smooth_transition(
            float(self.window_width), float(target_width)
        )
        self.window_height = self.smooth_transition(
            float(self.window_height), float(target_height)
        )

        # 更新窗口尺寸时转换为整数
        self.window.geometry(
            f"{int(round(self.window_width))}x{int(round(self.window_height))}"
        )

        # 计算实际偏差量（基于浮点值）
        current_deviation = max(
            abs(self.window_width - target_width),
            abs(self.window_height - target_height),
        )

        # 动态间隔调整
        adaptive_interval = max(
            10, int(interval * (current_deviation / self.max_jitter))
        )

        # 持续调整直到达到目标范围
        if current_deviation > self.tolerance:
            self.window.after(adaptive_interval, self.start, interval, smooth_factor)


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")

    def simulate_resize():
        resizer = Smooth_Resize_Window(root)
        resizer.start()

    btn = tk.Button(root, text="模拟调整", command=simulate_resize)
    btn.pack(pady=20)

    root.mainloop()
