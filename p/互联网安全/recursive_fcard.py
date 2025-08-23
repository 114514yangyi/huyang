#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import subprocess
import sys
import re
import shutil
from pathlib import Path
from urllib.parse import quote


def find_all_index_md_files(start_dir="."):
    """
    递归查找当前目录及所有子目录中的 index.md 文件
    """
    index_files = []
    for root, dirs, files in os.walk(start_dir):
        if "index.md" in files:
            index_files.append(os.path.join(root, "index.md"))
    return index_files


def get_random_cover_image(cover_dir="~/tcardgen/cover"):
    """
    从封面目录中随机选择一个图片文件
    """
    # 扩展用户目录的 ~
    cover_path = os.path.expanduser(cover_dir)

    if not os.path.exists(cover_path):
        print(f"错误: 封面目录不存在: {cover_path}")
        return None

    # 获取所有图片文件
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    image_files = []

    for file in os.listdir(cover_path):
        if os.path.isfile(os.path.join(cover_path, file)):
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                image_files.append(file)

    if not image_files:
        print(f"错误: 在目录 {cover_path} 中没有找到图片文件")
        return None

    # 随机选择一个图片
    selected_image = random.choice(image_files)
    return os.path.join(cover_path, selected_image)


def extract_title_from_front_matter(content):
    """
    从 Front Matter 中提取 title 字段
    """
    lines = content.split('\n')
    in_front_matter = False
    
    for line in lines:
        if line.strip() == '---':
            if in_front_matter:
                break
            else:
                in_front_matter = True
                continue
        
        if in_front_matter:
            if line.strip().startswith('title:'):
                # 提取 title 值
                if ':' in line:
                    key, value = line.split(':', 1)
                    value = value.strip()
                    # 去除引号
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    return value
    
    return None


def sanitize_filename(title):
    """
    清理文件名，移除非法字符
    """
    # 移除特殊字符，只保留字母、数字、中文、下划线和连字符
    sanitized = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', title)
    # 移除连续的下划线
    sanitized = re.sub(r'_+', '_', sanitized)
    # 移除开头和结尾的下划线
    sanitized = sanitized.strip('_')
    # 限制文件名长度
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    return sanitized


def update_front_matter_fields(content, cover_filename=None):
    """
    更新 Front Matter 字段
    - 如果没有 author 字段，添加 author: "胡杨"
    - 如果 author 字段为空，修改为 author: "胡杨"
    - 如果没有 tags 字段，添加 tags: ["原创"]
    - 如果没有 cover 字段，添加 cover 字段
    """
    lines = content.split('\n')
    new_lines = lines.copy()
    in_front_matter = False
    front_matter_end = 0
    author_found = False
    tags_found = False
    cover_found = False
    updated = False
    
    # 第一次遍历：检查 Front Matter 范围和字段
    for i, line in enumerate(lines):
        if line.strip() == '---':
            if in_front_matter:
                front_matter_end = i
                break
            else:
                in_front_matter = True
                continue
        
        if in_front_matter:
            # 检查 author 字段
            if line.strip().startswith('author:'):
                author_found = True
                # 检查 author 是否为空
                if ':' in line:
                    key, value = line.split(':', 1)
                    value = value.strip()
                    if value == '""' or value == "''" or value == '':
                        new_lines[i] = 'author: "胡杨"'
                        updated = True
            
            # 检查 tags 字段
            elif line.strip().startswith('tags:'):
                tags_found = True
            
            # 检查 cover 字段
            elif line.strip().startswith('cover:'):
                cover_found = True
    
    # 如果没有找到 author 字段且在 Front Matter 中，添加它
    if not author_found and in_front_matter and front_matter_end > 0:
        # 在 Front Matter 结束前插入 author 字段
        insert_position = front_matter_end - 1
        while insert_position > 0 and not new_lines[insert_position].strip():
            insert_position -= 1
        
        new_lines.insert(insert_position + 1, 'author: "胡杨"')
        updated = True
        front_matter_end += 1  # 因为插入了一行，结束位置后移
    
    # 如果没有找到 tags 字段且在 Front Matter 中，添加它
    if not tags_found and in_front_matter and front_matter_end > 0:
        # 在 Front Matter 结束前插入 tags 字段
        insert_position = front_matter_end - 1
        while insert_position > 0 and not new_lines[insert_position].strip():
            insert_position -= 1
        
        new_lines.insert(insert_position + 1, 'tags: ["原创"]')
        updated = True
        front_matter_end += 1  # 因为插入了一行，结束位置后移
    
    # 如果没有找到 cover 字段且在 Front Matter 中，添加它
    if not cover_found and in_front_matter and front_matter_end > 0 and cover_filename:
        # 在 Front Matter 结束前插入 cover 字段
        insert_position = front_matter_end - 1
        while insert_position > 0 and not new_lines[insert_position].strip():
            insert_position -= 1
        
        # 插入多行 cover 字段
        cover_lines = [
            f'image: {cover_filename}',
        ]
        
        # 反向插入，保持正确顺序
        for cover_line in reversed(cover_lines):
            new_lines.insert(insert_position + 1, cover_line)
        
        updated = True
    
    return '\n'.join(new_lines), updated


def process_front_matter_fields(index_files):
    """
    处理所有 index.md 文件的 Front Matter 字段
    """
    print("\n正在检查并更新 Front Matter 字段...")
    updated_count = 0
    
    for index_file in index_files:
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有 Front Matter
            if content.startswith('---'):
                # 提取 title 用于生成封面文件名
                title = extract_title_from_front_matter(content)
                cover_filename = None
                
                if title:
                    # 生成封面文件名
                    sanitized_title = sanitize_filename(title)
                    cover_filename = f"img/{sanitized_title}_cover.png"
                
                new_content, updated = update_front_matter_fields(content, cover_filename)
                
                if updated:
                    with open(index_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✓ 更新 Front Matter 字段: {index_file}")
                    updated_count += 1
                else:
                    print(f"✓ Front Matter 字段已正确设置: {index_file}")
            else:
                print(f"⚠️  没有 Front Matter，跳过: {index_file}")
                
        except Exception as e:
            print(f"✗ 处理文件时出错 {index_file}: {e}")
    
    print(f"Front Matter 字段处理完成: 更新了 {updated_count} 个文件")


def generate_cover_for_post(index_md_path, cover_image_path):
    """
    为指定的 index.md 文件生成封面并保存到指定目录
    """
    try:
        # 读取文件内容
        with open(index_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取 title
        title = extract_title_from_front_matter(content)
        if not title:
            print(f"✗ 无法提取 title 字段: {index_md_path}")
            return False
        
        # 清理文件名
        sanitized_title = sanitize_filename(title)
        cover_filename = f"{sanitized_title}_cover.png"
        
        # 目标目录
        target_dir = "/Users/mac/study/HyBlog/static/img"
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, cover_filename)
        
        # 创建临时目录用于生成封面
        post_dir = os.path.dirname(index_md_path)
        temp_cover_path = os.path.join(post_dir, "temp_cover.png")
        
        # 构建 tcardgen 命令
        font_dir = os.path.expanduser("~/tcardgen/font")

        cmd = [
            "tcardgen",
            "-c",
            "/Users/mac/tcardgen/config.yaml",
            "-f",
            font_dir,
            "-o",
            temp_cover_path,
            "-t",
            cover_image_path,
            index_md_path,
        ]

        print(f"正在为 '{title}' 生成封面...")
        print(f"使用模板: {cover_image_path}")
        print(f"输出到: {target_path}")

        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            # 移动封面到目标目录
            if os.path.exists(temp_cover_path):
                shutil.move(temp_cover_path, target_path)
                print(f"✓ 封面生成成功: {target_path}")
                
                # 更新 Front Matter 中的 cover 字段
                cover_filename_in_fm = f"img/{cover_filename}"
                new_content, updated = update_front_matter_fields(content, cover_filename_in_fm)
                
                if updated:
                    with open(index_md_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✓ 更新 cover 字段: {cover_filename_in_fm}")
                
                return True
            else:
                print(f"✗ 封面文件未生成: {temp_cover_path}")
                return False
        else:
            print(f"✗ 封面生成失败:")
            print(f"错误输出: {result.stderr}")
            # 清理临时文件
            if os.path.exists(temp_cover_path):
                os.remove(temp_cover_path)
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ 命令执行超时: {' '.join(cmd)}")
        return False
    except FileNotFoundError:
        print("✗ 找不到 tcardgen 命令，请确保已安装 tcardgen")
        return False
    except Exception as e:
        print(f"✗ 执行命令时发生错误: {e}")
        # 清理临时文件
        if 'temp_cover_path' in locals() and os.path.exists(temp_cover_path):
            os.remove(temp_cover_path)
        return False


def main():
    """
    主函数
    """
    print("=" * 50)
    print("Hugo 文章封面生成工具")
    print("=" * 50)

    # 1. 查找所有 index.md 文件
    print("正在查找所有 index.md 文件...")
    index_files = find_all_index_md_files()

    if not index_files:
        print("没有找到任何 index.md 文件")
        return

    print(f"找到 {len(index_files)} 个 index.md 文件:")
    for i, file_path in enumerate(index_files, 1):
        print(f"  {i}. {file_path}")

    # 2. 处理 Front Matter 字段（先不包含 cover）
    process_front_matter_fields(index_files)

    # 3. 随机选择封面图片
    print("\n正在选择随机封面...")
    cover_image = get_random_cover_image()

    if not cover_image:
        return

    print(f"选择的封面模板: {cover_image}")

    # 4. 为每个 index.md 生成封面
    print("\n开始生成封面...")
    success_count = 0

    for index_file in index_files:
        if generate_cover_for_post(index_file, cover_image):
            success_count += 1

    print("\n" + "=" * 50)
    print(f"处理完成!")
    print(f"成功生成封面: {success_count}/{len(index_files)}")
    print("=" * 50)


if __name__ == "__main__":
    # 检查是否直接运行
    if len(sys.argv) == 1:
        main()
    else:
        # 支持命令行参数
        if sys.argv[1] in ["-h", "--help"]:
            print("""
Hugo 文章封面生成工具

使用方法:
  python posthugo.py          # 处理所有 index.md 文件
  python posthugo.py --help   # 显示帮助信息

功能:
  1. 递归查找当前目录下的所有 index.md 文件
  2. 检查并更新 Front Matter 字段:
     - 如果没有 author 字段或为空，设置为 "胡杨"
     - 如果没有 tags 字段，设置为 ["原创"]
     - 根据 title 生成封面文件名并设置 cover 字段
  3. 从 ~/tcardgen/cover 随机选择封面模板
  4. 使用 tcardgen 为每篇文章生成封面并保存到指定目录

注意: 需要提前安装 tcardgen
            """)
        elif sys.argv[1] == "--frontmatter-only":
            # 只处理 Front Matter 字段，不生成封面
            index_files = find_all_index_md_files()
            if index_files:
                process_front_matter_fields(index_files)
            else:
                print("没有找到任何 index.md 文件")
        else:
            print("未知参数，使用 -h 或 --help 查看帮助")

