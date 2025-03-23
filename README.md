# Chem-Filter 🧪

**重庆理工大学化学化工学院化工实验设计大赛参赛项目**

## 项目简介

Chem-Filter 是一个实验数据处理与可视化的工具，专为化学实验中的数据分析而设计。该工具通过图形化界面，支持导入数据、数据处理、异常值检测及拟合分析，最终输出处理结果并生成图表，以帮助实验人员更加高效地进行实验数据分析。

## 功能概述

- **数据加载与处理**：支持从 CSV 文件中导入实验数据，进行数据清洗、标准化处理。
- **异常值检测**：自动检测并排除数据中的异常值，以提高拟合结果的准确性。
- **数据拟合**：支持线性拟合，并提供拟合结果的斜率、截距等信息。
- **图表生成与展示**：生成包含数据拟合曲线、异常值检测图、数据分布等的各类图表。
- **结果压缩与导出**：将生成的图表和数据结果压缩成 ZIP 文件，便于分发和存储。

## 技术栈

- **Python**：主要编程语言
- **Tkinter**：用于构建图形界面
- **Matplotlib**：用于绘制图表和可视化数据
- **Pandas**：用于处理实验数据
- **NumPy**：用于科学计算
- **Scikit-learn**：用于数据拟合和异常值检测

## 安装指南

### 环境准备

1. 安装 Python 3.9 或更高版本。
2. 安装所需的依赖库：

```bash
pip install -r requirements.txt
```

### 运行项目

1. 将项目克隆到本地：

```bash
git clone https://github.com/your-username/Chem-Filter.git
```

2. 进入项目目录并运行主程序：

```bash
python main.py
```

3. 打开 GUI 界面后，选择需要分析的 CSV 数据文件，进行数据处理、拟合及图表生成。

## 使用说明

1. **导入数据**：点击“导入数据”按钮，选择需要分析的 CSV 文件。支持的数据格式为标准的 CSV 文件。
2. **处理数据**：点击“处理数据”按钮，系统会自动对数据进行清洗、拟合，并检测异常值。
3. **绘制图形**：处理完数据后，点击“绘制图形”按钮，生成数据拟合曲线和异常值检测图。
4. **导出结果**：所有结果图表会保存在项目文件夹的“拟合图结果”中，并自动压缩成 ZIP 文件，便于分享和存档。

## 项目结构

```
目录结构:
|-- 文件: .gitattributes
|-- 文件: .gitignore
|-- 文件夹: .vscode
|   |-- (空目录)
|-- 文件夹: gui
|   |-- 文件: app.py
|   |-- 文件夹: logos
|   |   |-- 文件: chem.icns
|   |   |-- 文件: chem.ico
|   |   |-- 文件: chem.png
|   |-- 文件夹: screens
|   |   |-- 文件夹: common_screens
|   |   |   |-- 文件: base_record_data_screen.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件: filteration_calculator.py
|   |   |-- 文件: filteration_experiment_processor.py
|   |   |-- 文件: filteration_plotter.py
|   |   |-- 文件: filteration_screen.py
|   |   |-- 文件: __init__.py
|   |-- 文件夹: utils
|   |   |-- 文件: config.py
|   |   |-- 文件: expserial.py
|   |   |-- 文件夹: funcs
|   |   |   |-- 文件: dct2cols.py
|   |   |   |-- 文件: file_name_extension.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件夹: maths
|   |   |   |-- 文件: common_maths.py
|   |   |   |-- 文件: maths_filteration.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件: __init__.py
|   |-- 文件夹: widgets
|   |   |-- 文件夹: common_widgets
|   |   |   |-- 文件: plot_widget.py
|   |   |   |-- 文件: spin_entries_widget.py
|   |   |   |-- 文件: string_entries_widget.py
|   |   |   |-- 文件: table_widget.py
|   |   |   |-- 文件: text_widget.py
|   |   |   |-- 文件: __init__.py
|   |   |-- 文件: filteration_spin_entries_widget.py
|   |   |-- 文件: __init__.py
|   |-- 文件: __init__.py
|-- 文件: LICENSE
|-- 文件: main.py
|-- 文件夹: manual
|   |-- (空目录)
|-- 文件: README.md
|-- 文件: requirements.txt
|-- 文件: __init__.py
|-- 文件夹: 拟合图结果
|   |-- 文件: 1.png
|   |-- 文件: 2.png
|   |-- 文件: 3.png
|   |-- 文件: 4.png
|   |-- 文件: 5.png
|   |-- 文件: 6.png
|   |-- 文件: 7.png
|   |-- 文件: 8.png
|   |-- 文件: 拟合图整合图.png
|-- 文件: 拟合图结果.zip
|-- 文件: 过滤原始数据记录表(非).csv
```

## 开发者

- **项目负责人**：刘抗非
- **开发人员**：刘抗非

## License

该项目遵循 GNU 许可证，详情请见 [LICENSE](LICENSE) 文件。

## 鸣谢

本项目是受到 [北京大学-化学与分子工程学院-中级物理化学实验项目](https://github.com/Zhao-Zehua/Dissolution-Combustion) 的启发，参考其中的逻辑重新设计结构后编写的。在此要特别鸣谢[Zehua Zhao同学](https://github.com/Zhao-Zehua)。
