import os
import sys
import shutil
from datetime import datetime

def process_markdown_file(filepath, article_type):
    """
    处理单个 Markdown 文件：创建文件夹，移动文件，添加 Front Matter，重命名为 index.md。
    Args:
        filepath (str): Markdown 文件的完整路径。
        article_type (str): 文章类型，用于设置 categories。
    """
    directory = os.path.dirname(filepath)
    filename_without_ext = os.path.splitext(os.path.basename(filepath))[0]
    new_directory_name = filename_without_ext
    new_directory_path = os.path.join(directory, new_directory_name)
    new_filepath = os.path.join(new_directory_path, "index.md")

    # 1. 创建新的文件夹
    try:
        os.makedirs(new_directory_path, exist_ok=True)
        print(f"已创建文件夹: {new_directory_path}")
    except Exception as e:
        print(f"创建文件夹 {new_directory_path} 时发生错误: {e}")
        return

    # 2. 移动 Markdown 文件到新的文件夹
    try:
        shutil.move(filepath, new_filepath)
        print(f"已将文件移动到: {new_filepath}")
    except Exception as e:
        print(f"移动文件 {filepath} 到 {new_filepath} 时发生错误: {e}")
        return

    # 3. 在移动后的文件中添加 Front Matter 并重命名为 index.md
    title = filename_without_ext.replace('-', ' ').title()  # 标题处理，更友好

    frontmatter = f"""---
date : '{datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')}'
draft : false
title : '{title}'
categories:
    - {article_type}
---
"""

    try:
        with open(new_filepath, 'r+', encoding='utf-8') as f:
            content = f.read()
            if not content.startswith("---"):
                f.seek(0)
                f.write(frontmatter + content)
                print(f"已给文件添加 Front Matter: {new_filepath}")
            else:
                print(f"文件 {new_filepath} 已存在 Front Matter，跳过。")
    except Exception as e:
        print(f"处理文件 {new_filepath} 时发生错误: {e}")

def process_directory(directory, article_type):
    """
    遍历指定目录及其子目录下的所有 .md 文件并进行处理。
    Args:
        directory (str): 要遍历的根目录路径。
        article_type (str): 文章类型，用于设置 categories。
    """
    for root, _, files in os.walk(directory):
        md_files_in_root = [os.path.join(root, file) for file in files if file.endswith(".md")]
        for filepath_to_process in md_files_in_root:
            process_markdown_file(filepath_to_process, article_type)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        start_directory = sys.argv[1]
        article_type = sys.argv[2]  # 获取文章类型
        if os.path.isdir(start_directory):
            print(f"开始遍历并处理文件夹 '{start_directory}' 及其子文件夹中的 .md 文件...")
            print(f"文章类型设置为: {article_type}")
            process_directory(start_directory, article_type)
            print("处理完成。")
        else:
            print(f"错误: 指定的路径 '{start_directory}' 不是一个有效的文件夹。")
    else:
        print("请在运行脚本时提供根目录路径和文章类型作为参数。例如: python main.py /path/to/your/markdown/files 教程")

