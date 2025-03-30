# smooth_resize_window.py

# 内置库
import sys
import os
import random
import tkinter as tk
import math
import time

# 动态获取路径（保持不变）
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
)
sys.path.insert(0, project_root)


# 物理引擎类
class Physics_Engine:
    def __init__(self, spring_stiffness=0.3, damping=0.2, max_jitter=5.0, duration=3.0):
        """物理引擎，使用弹簧-阻尼系统模拟平滑过渡"""
        self.spring_stiffness = spring_stiffness  # 弹簧刚度系数
        self.damping = damping  # 阻尼系数
        self.max_jitter = max_jitter  # 最大抖动幅度
        self.velocity = (0.0, 0.0)  # 速度向量 (vx, vy)
        self.width_offset = 0.0
        self.height_offset = 0.0
        self.total_time = duration  # 抖动持续时间
        self.elapsed_time = 0.0  # 已经过的时间

    def update(self, dt):
        """基于物理模型更新窗口尺寸"""
        # 计算弹性力（胡克定律）
        width_force = -self.spring_stiffness * self.width_offset
        height_force = -self.spring_stiffness * self.height_offset

        # 应用阻尼力
        width_force -= self.damping * self.velocity[0]
        height_force -= self.damping * self.velocity[1]

        # 数值积分（欧拉方法）
        new_vx = self.velocity[0] + width_force * dt
        new_vy = self.velocity[1] + height_force * dt

        # 更新偏移量
        self.width_offset += self.velocity[0] * dt
        self.height_offset += self.velocity[1] * dt

        # 更新速度
        self.velocity = (new_vx, new_vy)

        # 更新已过时间
        self.elapsed_time += dt

        # 强制在接近结束时稳定
        if self.elapsed_time >= self.total_time:
            self.width_offset = 0.0
            self.height_offset = 0.0
            self.velocity = (0.0, 0.0)

    def apply_random_force(self):
        """施加随机驱动力（幅度减小）"""
        self.velocity = (
            self.velocity[0] + random.uniform(-0.3, 0.3),
            self.velocity[1] + random.uniform(-0.3, 0.3),
        )

    def get_offsets(self):
        """获取当前的偏移量"""
        return self.width_offset, self.height_offset

    def is_done(self):
        """检查是否已完成抖动"""
        return self.elapsed_time >= self.total_time

    def reset(self):
        """重置物理引擎状态"""
        self.width_offset = 0.0
        self.height_offset = 0.0
        self.velocity = (0.0, 0.0)
        self.elapsed_time = 0.0


# 平滑过渡窗口类
class Smooth_Resize_Window:
    def __init__(
        self,
        window,
        spring_stiffness=0.3,
        damping=0.7,
        max_jitter=5.0,
        duration=2.0,
        random_force_prob=0.3,  # 降低随机力概率
    ):
        self.window = window
        self.window.update_idletasks()

        self.base_width = self.window.winfo_width()
        self.base_height = self.window.winfo_height()

        # 创建物理引擎实例
        self.physics = Physics_Engine(spring_stiffness, damping, max_jitter, duration)
        self.max_jitter = max_jitter
        self.random_force_prob = random_force_prob

        # 动画控制
        self.animation_id = None
        self.last_update = time.time()

    def update_window_size(self):
        """更新窗口尺寸"""
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time

        # 更新物理系统
        self.physics.update(dt)

        # 在前半段时间施加随机力
        if (
            self.physics.elapsed_time < self.physics.total_time * 0.5
            and random.random() < self.random_force_prob
        ):
            self.physics.apply_random_force()

        # 获取当前的偏移量
        width_offset, height_offset = self.physics.get_offsets()

        # 计算目标尺寸（直接使用物理引擎计算的偏移量）
        target_width = self.base_width + int(round(width_offset))
        target_height = self.base_height + int(round(height_offset))

        # 更新窗口尺寸
        self.window.geometry(f"{target_width}x{target_height}")

        # 如果抖动时间已到，停止动画并恢复尺寸
        if self.physics.is_done():
            self.stop()
        else:
            self.animation_id = self.window.after(16, self.update_window_size)

    def start(self):
        """启动动画"""
        self.physics.reset()  # 重置物理引擎
        self.last_update = time.time()
        if not self.animation_id:
            self.update_window_size()

    def stop(self):
        """停止动画并恢复原始尺寸"""
        if self.animation_id:
            self.window.after_cancel(self.animation_id)
            self.animation_id = None
        # 确保恢复原始尺寸
        self.window.geometry(f"{self.base_width}x{self.base_height}")


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
