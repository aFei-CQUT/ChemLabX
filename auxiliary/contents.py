import sys
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

# 定义需要忽略的文件扩展名
IGNORE_EXTENSIONS = [
    ".pyc",
    ".png",
    ".idx",
    ".pack",
    ".rev",
    ".sample",
    ".jpg",
    ".xmind",
    ".pdf",
    ".docx",
    ".zip",
    ".xlsx",
    ".pyc",
    ".csv",
    ".jpg",
    ".icns",
    ".ico",
]

# 定义需要忽略的文件
IGNORE_FILES = [".gitattributes", ".ignore", "LICENSE"]


def generate_directory_structure(startpath, indent="", exclude_folders=None):
    """
    生成目录结构的字符串表示
    :param startpath: 要扫描的起始目录路径
    :param indent: 缩进字符，用于显示目录层级
    :param exclude_folders: 要排除的文件夹列表
    :return: 目录结构字符串
    """
    structure = ""
    path = Path(startpath)

    if not any(path.iterdir()):  # 如果目录为空
        structure += f"{indent}|-- (空目录)\n"
    else:
        for item in path.iterdir():
            if item.is_dir():
                # 如果该文件夹在排除列表中，则跳过
                if exclude_folders and item.name in exclude_folders:
                    continue
                structure += f"{indent}|-- 文件夹: {item.name}\n"
                structure += generate_directory_structure(item, indent + "|   ", exclude_folders)
            else:
                structure += f"{indent}|-- 文件: {item.name}\n"
    return structure


def clean_content(content):
    """
    清理文本内容: 不再删除任何内容
    :param content: 要处理的文本内容
    :return: 原样返回内容
    """
    return content


def write_directory_contents_to_file(scan_directory, output_directory, output_file_name, exclude_folders=None):
    """
    将目录内容和文件内容写入到指定的输出文件
    :param scan_directory: 要扫描的目录路径
    :param output_directory: 输出文件夹路径
    :param output_file_name: 输出文件名
    :param exclude_folders: 要排除的文件夹列表
    """
    # 获取当前脚本所在的目录
    current_dir = Path(scan_directory)

    if not current_dir.is_dir():
        print(f"错误: 指定的扫描目录 {scan_directory} 不存在或不是目录.")
        return

    # 确保输出目录存在
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 构建输出文件路径
    output_file_path = output_dir / output_file_name

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        # 写入目录结构
        directory_structure = generate_directory_structure(current_dir, exclude_folders=exclude_folders)
        output_file.write("目录结构:\n")
        output_file.write(directory_structure)
        output_file.write("\n\n")

        # 遍历当前目录
        for root, dirs, files in os.walk(current_dir):
            # 排除特定的文件夹
            dirs[:] = [d for d in dirs if d not in exclude_folders]
            dirs[:] = [d for d in dirs if d != ".git"]  # 忽略 .git 文件夹

            # 过滤掉忽略的文件
            files = [f for f in files if not (any(f.endswith(ext) for ext in IGNORE_EXTENSIONS) or f in IGNORE_FILES)]

            # 处理文件
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except (UnicodeDecodeError, IsADirectoryError):
                    try:
                        with open(file_path, "r", encoding="latin1") as f:
                            content = f.read()
                    except (UnicodeDecodeError, IsADirectoryError):
                        continue

                # 不再清理内容
                cleaned_content = clean_content(content)

                # 写入文件并分割
                marker = "=" * 80
                output_file.write(f"{marker}\n")
                output_file.write(f"{file_path} 的内容:\n")
                output_file.write(f"{marker}\n")
                output_file.write(cleaned_content)
                output_file.write("\n\n")


def choose_directory(title="选择目录"):
    """
    打开一个目录选择对话框，允许用户选择目录
    :param title: 对话框的标题
    :return: 用户选择的目录路径
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    selected_directory = filedialog.askdirectory(title=title)
    return selected_directory


if __name__ == "__main__":
    # 选择要扫描的目录
    scan_directory = choose_directory("选择要扫描的目录")
    if not scan_directory:
        print("未选择目录，程序退出。")
        sys.exit(0)

    output_directory = "./auxiliary/"  # 输出路径
    output_file_name = "contents.txt"  # 输出文件名

    # 排除的文件夹列表
    exclude_folders = [
        ".git",
        "auxiliary",
        "docs",
        "__pycache__",
    ]

    # 将目录内容写入文件
    write_directory_contents_to_file(scan_directory, output_directory, output_file_name, exclude_folders)
