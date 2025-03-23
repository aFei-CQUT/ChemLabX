# common_maths.py

import numpy as np
from scipy import optimize
from scipy.integrate import simps


# 寻找初始起止点
def find_start_end_point(csv, code: str, time_lower_limit: int or float, time_upper_limit: int or float, std_limit: float):  # type: ignore # 建议时间下限30s，时间上限40s，标准差上限0.01
    # 第一列为index，第二列为标准差
    standard_deviation = []
    points = []
    count = 4 if code == "燃烧热" else 6
    platform = True
    start_index = 0
    end_index = 1
    if csv is None:
        return
    while end_index < len(csv):
        time_range = csv[end_index][0] - csv[start_index][0]
        if time_range > time_upper_limit:
            start_index += 1
        elif time_range < time_lower_limit:
            end_index += 1
        else:
            standard_deviation.append([end_index, np.std(csv[start_index:end_index, 1])])
            end_index += 1
    # 寻找起止点
    points.append(0)
    for i in standard_deviation:
        index, std = i
        if std <= std_limit and platform == False:
            points.append(index)
            platform = True
            count -= 1
        elif std > std_limit and platform == True:
            """
            # 会导致非正常数据无法显示图象，暂时删除
            # 排除延后效应的影响
            time_now = csv[index][0]
            while time_now - csv[index][0] < time_lower_limit / 1.0:    # 1.0可调节，越大对延后的校正越弱
                index -= 1
            """
            points.append(index)
            platform = False
            count -= 1
        if count == 2:
            break
    points.append(len(csv) - 1)
    return points
