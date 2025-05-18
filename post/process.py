import os
import sys
from datetime import datetime
import shutil

def process_markdown_file(filepath):
    """
    处理单个 Markdown 文件：创建文件夹，移动文件，添加 Front Matter，重命名为 index.md。
    Args:
        filepath (str): Markdown 文件的完整路径。
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
    title = filename_without_ext.replace('-', ' ').title()
    date_str = datetime.now().strftime('%Y-%m-%d')

    frontmatter = f"""---
title: {title}
date: '{date_str}'
license: CC BY-NC-ND
lastmod: '{datetime.now().strftime('%Y-%m-%d')}'
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

def process_directory(directory):
    """
    遍历指定目录及其子目录下的所有 .md 文件并进行处理。
    Args:
        directory (str): 要遍历的目录路径。
    """
    for root, _, files in os.walk(directory):
        md_files_in_root = [os.path.join(root, file) for file in files if file.endswith(".md")]
        for filepath_to_process in md_files_in_root:
            process_markdown_file(filepath_to_process)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_directory = sys.argv[1]
        if os.path.isdir(start_directory):
            print(f"开始遍历并处理文件夹 '{start_directory}' 及其子文件夹中的 .md 文件...")
            process_directory(start_directory)
            print("处理完成。")
        else:
            print(f"错误: 指定的路径 '{start_directory}' 不是一个有效的文件夹。")
    else:
        print("请在运行脚本时提供要遍历的文件夹路径作为参数。例如: python script_name.py /path/to/your/markdown/files")
