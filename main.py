# ChemLabX 实验数据采集与处理软件
# Author: 刘抗非
# 本软件参考 北京大学-物理化学溶解燃烧热中级实验项目（Author：赵泽华） 的设计进行架构的设计
# 该软件为非盈利软件，若分发参考请务必浏览 LICENSE 文件

"""
快速启动:
    运行"main-win.exe"或"main-mac.app"即可自动运行main.py
    如出现异常情况，尝试运行"requirements-win.exe"或"requirements-mac.app"安装或更新依赖库
    main-win/mac需要与main.py在同一目录下，requirements-win/mac需要与requirements.txt在同一目录下

可调参数:
    dx: 积分、绘图步长
    time_interval: 记录数据间隔，单位毫秒
    plot_max_points: 绘图最大点数
    port_timeout: 串口超时时间，单位秒
    std_limit: 自动寻找平台期的标准差阈值
    time_lower_limit: 自动寻找平台期的最小时间窗口
    time_upper_limit: 自动寻找平台期的最大时间窗口
    width_height_inches: 保存图片尺寸，单位英尺
    dpi: 保存图片DPI

内置库:
    csv
    os
    re
    sys
    shutil
    time
    tkinter
"""

# 内置库
import sys
import os
import shutil

# 动态获取路径
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_script_path))
sys.path.insert(0, project_root)

# 自建库
from gui.app import App

# 可调参数
dx = 0.1  # 积分、绘图步长
time_interval = 500  # 记录数据间隔，单位毫秒
plot_max_points = 500  # 绘图最大点数
port_timeout = 0.25  # 串口超时时间，单位秒
std_limit = 0.005  # 自动寻找平台期的标准差阈值
time_lower_limit = 30  # 自动寻找平台期的最小时间窗口
time_upper_limit = 40  # 自动寻找平台期的最大时间窗口
width_height_inches = (10, 6)  # 保存图片尺寸，单位英尺
dpi = 600  # 保存图片DPI

if __name__ == "__main__":
    # 获取当前路径
    # 如果是pyinstaller打包的exe文件，则获取可执行文件所在目录的绝对路径
    if getattr(sys, "frozen", False):
        py_path = os.path.dirname(os.path.abspath(sys.executable))
        # 如果是mac
        if sys.platform == "darwin":
            for i in range(3):
                py_path = os.path.dirname(py_path)
    # 如果是运行的py文件，则获取py文件所在目录的绝对路径
    else:
        py_path = os.path.dirname(os.path.abspath(__file__))
    App(
        dx,
        time_interval,
        plot_max_points,
        port_timeout,
        std_limit,
        time_lower_limit,
        time_upper_limit,
        width_height_inches,
        dpi,
        py_path,
    )
    # 清除缓存文件夹
    pycache_dir = py_path + "/__pycache__"
    if os.path.exists(pycache_dir):
        shutil.rmtree(pycache_dir)
