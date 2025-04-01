# ChemLabX 文档

**ChemLabX** 是一款用于化学实验数据处理与可视化的软件，专门设计用于化学实验中的数据分析。通过图形化界面，用户能够导入实验数据，执行数据清洗、异常值检测、拟合分析，并生成最终的图表结果。这款软件旨在帮助实验人员高效地进行数据分析和实验结果展示，提升工作效率和结果的准确性。

## 项目概述

**ChemLabX** 提供了多个实验模块，每个模块都针对特定的实验设计了专用的功能，支持数据的采集、处理、拟合与图表生成。当前版本支持以下几种实验类型，涵盖了化学实验中常见的数据处理需求：

- **精馏实验**：处理液体的分离实验数据，分析回流比、塔板数和分离效率等参数。
- **干燥实验**：分析不同湿度条件下的物质干燥过程，计算传热系数、干燥速率等。
- **过滤实验**：处理固液分离实验数据，分析滤面高度、时间差等影响因素。
- **流体流动实验**：研究液体或气体在管道中的流动特性，进行流速与压力的分析。
- **传热实验**：涉及热量的传递过程，计算传热系数、热流密度等参数。
- **萃取实验**：分析液-液萃取过程，处理分配曲线、分配系数等数据。
- **解吸实验**：涉及吸附与解吸过程的实验，计算解吸速率、吸附容量等。

每个实验模块都包含了数据导入、处理、计算和图表生成等功能，能够帮助用户轻松地从原始数据中提取有效信息并可视化。

### 核心功能

- **数据导入与处理**：支持从 CSV 文件导入实验数据，系统会自动进行数据清洗，包括缺失值处理和数据标准化，确保数据的准确性和一致性。
- **异常值检测**：自动检测并排除数据中的异常值，减少人为错误对结果的影响，确保数据分析的精确度。
- **数据拟合**：支持多种拟合方法，包括线性拟合、非线性拟合等，帮助用户获得实验数据的数学模型，并提供拟合结果的统计信息，如斜率、截距和拟合优度等。
- **图表生成与展示**：软件能够根据处理后的数据生成多种类型的图表，包括散点图、曲线图、柱状图等，帮助用户直观地理解数据趋势和规律。
- **结果导出**：处理结果和图表可以导出为图像文件和压缩包，便于存档和分享，确保实验结果的可追溯性和便于团队协作。

## 安装与运行

### 环境准备

1. 安装 Python 3.9.21 或更高版本。
2. 安装所需的依赖库：   
   将所有依赖库安装到您的虚拟环境或全局环境中：
    ```bash
    pip install -r requirements.txt
    ```

### 运行项目

1. 将项目克隆到本地：
    ```bash
    git clone https://github.com/aFei-CQUT/ChemLabX.git
    ```
2. 进入项目目录并运行主程序：
    ```bash
    python main.py
    ```

3. 打开 GUI 界面后，您可以选择需要分析的 CSV 数据文件，进行数据的导入、处理、拟合及图表生成。

4. 软件会自动在图形界面中展示处理结果，并提供图表保存和导出的功能。

## 项目结构

```
目录结构:
|-- 文件: .gitattributes
|-- 文件: .gitignore
|-- 文件夹: gui
|   |-- 文件: app.py
|   |-- 文件夹: screens
|   |   |-- 文件夹: calculators
|   |   |   |-- 文件: distillation_calculator.py
|   |   |   |-- 文件: drying_calculator.py
|   |   |   |-- 文件: extraction_calculator.py
|   |   |   |-- 文件: filteration_calculator.py
|   |   |   |-- 文件: fluid_flow_calculator.py
|   |   |   |-- 文件: heat_transfer_calculator.py
|   |   |   |-- 文件: oxygen_desorption_calculator.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件夹: common_screens
|   |   |   |-- 文件: base_screen.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件夹: common_widgets
|   |   |   |-- 文件: plot_widget.py
|   |   |   |-- 文件: string_entries_widget.py
|   |   |   |-- 文件: table_widget.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件: distillation_screen.py
|   |   |-- 文件: drying_screen.py
|   |   |-- 文件: extraction_screen.py
|   |   |-- 文件: filteration_screen.py
|   |   |-- 文件: fluid_flow_screen.py
|   |   |-- 文件: heat_transfer_screen.py
|   |   |-- 文件夹: maths
|   |   |   |-- 文件: common_maths.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件: oxygen_desorption_screen.py
|   |   |-- 文件夹: plotters
|   |   |   |-- 文件: distillation_plotter.py
|   |   |   |-- 文件: drying_plotter.py
|   |   |   |-- 文件: extraction_plotter.py
|   |   |   |-- 文件: filteration_plotter.py
|   |   |   |-- 文件: fluid_flow_plotter.py
|   |   |   |-- 文件: heat_transfer_plotter.py
|   |   |   |-- 文件: oxygen_desorption_plotter.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件夹: processors
|   |   |   |-- 文件: distillation_experiment_processor.py
|   |   |   |-- 文件: drying_experiment_processor.py
|   |   |   |-- 文件: extraction_expriment_processor.py
|   |   |   |-- 文件: filteration_experiment_processor.py
|   |   |   |-- 文件: fluid_flow_experiment_processor.py
|   |   |   |-- 文件: heat_transfer_experiment_processor.py
|   |   |   |-- 文件: oxygen_desorption_experiment_processor.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件夹: utils
|   |   |   |-- 文件: config.py
|   |   |   |-- 文件: expserial.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件夹: widgets
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件: __init__.py
|-- 文件: LICENSE
|-- 文件: main.py
|-- 文件夹: manual
|   |-- (空目录)
|-- 文件: README.md
|-- 文件: requirements.txt
|-- 文件: __init__.py
```

## 开发者

- **项目负责人**：Kangfei Liu
- **开发人员**：Kangfei Liu

## License

该项目遵循 GNU 许可证，详情请见 [LICENSE](LICENSE) 文件。

## 鸣谢

本项目参考了 [北京大学-化学与分子工程学院-中级物理化学实验项目](https://github.com/Zhao-Zehua/Dissolution-Combustion) 的设计。特别感谢 [Zehua Zhao](https://github.com/Zhao-Zehua)。