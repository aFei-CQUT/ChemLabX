import sys
import os
import random
import tkinter as tk
import time

# 获取当前脚本的路径和项目根路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)


class Smooth_Resize_Window:
    """
    Smooth_Resize_Window类实现了一个平滑调整窗口尺寸的动画效果。

    Attributes:
        window: Tkinter的窗口对象。
        base_width: 基准窗口宽度。
        base_height: 基准窗口高度。
        current_width: 当前窗口宽度。
        current_height: 当前窗口高度。
        max_jitter: 最大的尺寸抖动幅度。
        duration: 抖动持续时间。
        return_speed: 回归基准尺寸的速度（像素/帧）。
        start_time: 动画开始时间。
    """

    def __init__(self, window):
        """
        初始化Smooth_Resize_Window类的实例。

        Args:
            window (tk.Tk): Tkinter的窗口对象，用于调整大小。
        """
        self.window = window
        self.window.update_idletasks()

        # 基准尺寸
        self.base_width = self.window.winfo_width()
        self.base_height = self.window.winfo_height()

        # 当前浮动尺寸
        self.current_width = float(self.base_width)
        self.current_height = float(self.base_height)

        # 控制参数
        self.max_jitter = 2  # 最大抖动幅度
        self.duration = 0.05  # 总抖动时间（秒）
        self.start_time = None  # 动画开始时间
        self.return_speed = 10  # 回归基准速度（像素/帧）

    def _generate_jitter_target(self):
        """
        生成基准附近的抖动目标。

        Returns:
            tuple: 包含随机生成的目标宽度和目标高度。
        """
        return (
            self.base_width + random.randint(-self.max_jitter, self.max_jitter),
            self.base_height + random.randint(-self.max_jitter, self.max_jitter),
        )

    def _smooth_step(self, current, target, speed):
        """
        带速度限制的平滑移动。

        Args:
            current (float): 当前值。
            target (float): 目标值。
            speed (float): 移动速度。

        Returns:
            float: 移动后的新值。
        """
        delta = target - current
        if abs(delta) <= speed:
            return target
        return current + (delta / abs(delta)) * speed

    def update_size(self):
        """
        更新窗口大小，执行平滑调整逻辑。

        在抖动阶段，窗口尺寸向随机目标移动；在回归阶段，窗口尺寸返回基准值。
        """
        # 计算已过时间
        elapsed = time.time() - self.start_time

        # 判断当前阶段：抖动或回归
        if elapsed < self.duration:
            # 抖动阶段：向随机目标移动
            target_width, target_height = self._generate_jitter_target()
        else:
            # 回归阶段：回到基准尺寸
            target_width, target_height = self.base_width, self.base_height

        # 平滑移动
        self.current_width = self._smooth_step(
            self.current_width, target_width, self.return_speed
        )
        self.current_height = self._smooth_step(
            self.current_height, target_height, self.return_speed
        )

        # 更新窗口
        self.window.geometry(f"{int(self.current_width)}x{int(self.current_height)}")

        # 停止条件：抖动结束且已回到基准
        if (
            elapsed >= self.duration
            and int(self.current_width) == self.base_width
            and int(self.current_height) == self.base_height
        ):
            return
        # 定时器：16毫秒后继续更新
        self.window.after(16, self.update_size)

    def start(self):
        """
        启动抖动动画。

        该方法初始化动画状态并开始更新窗口大小。
        """
        self.start_time = time.time()
        self.current_width = float(self.base_width)
        self.current_height = float(self.base_height)
        self.update_size()


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")

    def simulate_resize():
        """
        模拟调整窗口尺寸的函数，用于触发抖动动画。
        """
        resizer = Smooth_Resize_Window(root)
        resizer.start()

    # 添加模拟按钮
    btn = tk.Button(root, text="模拟调整", command=simulate_resize)
    btn.pack(pady=20)

    root.mainloop()
