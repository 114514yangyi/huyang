import os
import sys
import frontmatter
import traceback
import re # For pre-processing
import yaml # For specific YAML error types like yaml.reader.ReaderError

# YAMLError can come from ruamel.yaml or PyYAML used by frontmatter
# PyYAML's YAMLError is yaml.YAMLError
# frontmatter.handler.YAMLError tries to point to the correct one.
try:
    from frontmatter.handler import YAMLError
except ImportError:
    # Fallback if the above path changes or for direct use
    YAMLError = yaml.YAMLError # Base YAMLError from PyYAML

def preprocess_front_matter_content(fm_content_str: str) -> str:
    """
    Tries to clean up common non-standard YAML issues in front matter content.
    - Normalizes leading whitespace (NBSP to space, tabs to spaces).
    - Converts 'key = value' to 'key: value' for simple cases.
    - Removes problematic control characters.
    This is heuristic and might not cover all edge cases.
    """
    processed_lines = []
    # print(f"DEBUG: Original FM block to preprocess:\n{fm_content_str}") # For debugging
    for original_line in fm_content_str.splitlines():
        current_line = original_line

        # 1. Normalize leading whitespace
        leading_ws_match = re.match(r"^([\s\u00A0\t]+)(.*)$", current_line)
        if leading_ws_match:
            ws_original = leading_ws_match.group(1)
            content_part = leading_ws_match.group(2)
            ws_processed = ws_original.replace('\u00A0', ' ').replace('\t', '  ') # Tab to 2 spaces
            current_line = ws_processed + content_part
        
        # 2. Attempt to convert 'key = value' to 'key: value'
        transform_match = re.match(r"^(\s*)([^#=\n:]+?)\s*=\s*(.*)$", current_line)
        if transform_match:
            leading_ws = transform_match.group(1)
            key = transform_match.group(2).strip() 
            value = transform_match.group(3)
            if key: 
                current_line = f"{leading_ws}{key}: {value}"
        
        # 3. Remove problematic control characters from the (potentially transformed) line
        #    Allowed: \x09 (TAB), \x0A (LF), \x0D (CR).
        #    Removing C0 (U+0000-U+001F excluding TAB, LF, CR)
        #    and C1 (U+0080-U+009F). Character \x7F (DEL) is also removed.
        #    Regex removes chars in ranges: \x00-\x08, \x0B-\x0C (VT, FF), \x0E-\x1F, \x7F, \x80-\x9F
        current_line = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\x80-\x9F]', '', current_line)

        processed_lines.append(current_line)
    
    processed_fm_str = "\n".join(processed_lines)
    # if fm_content_str != processed_fm_str: # For debugging purposes
    #    print(f"DEBUG: Preprocessed FM block result:\n{processed_fm_str}")
    return processed_fm_str

def update_markdown_file(file_path, new_category):
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    file_content_str = None
    detected_encoding = None
    load_error = None 

    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                file_content_str = f.read()
            detected_encoding = enc
            load_error = None 
            break 
        except UnicodeDecodeError:
            load_error = UnicodeDecodeError(enc, b'', 0, 0, f"Failed to decode with {enc}") 
            continue
        except Exception as e: 
            load_error = e
            detected_encoding = enc 
            break

    if load_error or file_content_str is None:
        if isinstance(load_error, UnicodeDecodeError) or (isinstance(load_error, Exception) and "UnicodeDecodeError" in str(load_error)):
            print(f"处理文件 {file_path} 时，尝试多种编码 ({', '.join(encodings_to_try)}) 均无法正确解码。")
            print(f"  请确认该文件的实际编码，或预先将其转换为 UTF-8 编码。")
        elif load_error:
            print(f"读取文件 {file_path} (尝试编码: {detected_encoding or 'N/A'}) 时发生错误:")
            traceback.print_exc()
        else: 
            print(f"无法读取文件 {file_path}，原因未知。")
        return 

    post = None
    content_for_parser = file_content_str 
    # This variable will hold the full content string (potentially with preprocessed FM) for frontmatter.loads()
    
    # Variable to track if front matter block was identified for targeted pre-processing
    fm_block_identified_for_preprocessing = False

    full_fm_match = re.match(r"^(---|\*\*\*)\r?\n(.*?)\r?\n^\1\r?\n(.*)", file_content_str, re.DOTALL | re.MULTILINE)

    if full_fm_match:
        fm_delimiter = full_fm_match.group(1)
        raw_fm_block_content = full_fm_match.group(2)
        main_doc_content = full_fm_match.group(3)
        fm_block_identified_for_preprocessing = True
        
        processed_fm_block_content = preprocess_front_matter_content(raw_fm_block_content)
        content_for_parser = f"{fm_delimiter}\n{processed_fm_block_content}\n{fm_delimiter}\n{main_doc_content}"
        
        # if raw_fm_block_content != processed_fm_block_content:
        #     print(f"  文件 {file_path}: Front Matter 已被预处理。")

    try:
        post = frontmatter.loads(content_for_parser)

    except YAMLError as e: # Catches all YAML-related errors, including ReaderError, ScannerError etc.
        original_encoding_info = f"(原文件编码: {detected_encoding or 'N/A'})"
        print(f"处理文件 {file_path} {original_encoding_info} 时发生 YAML 解析错误。")
        
        print(f"  错误类型: {type(e).__name__}")
        # str(e) is usually informative, especially for ReaderError/ScannerError including position
        print(f"  错误信息: {str(e)}") 

        # Optionally, try to print problem_mark if it exists and offers distinct line/col
        if hasattr(e, 'problem_mark') and e.problem_mark:
            try:
                mark_line = int(e.problem_mark.line) + 1
                mark_col = int(e.problem_mark.column) + 1
                # Check if this line/col info is already obvious from str(e)
                # This check is heuristic; str(e) for ReaderError often has "position X" rather than line/col.
                mark_details_in_str_e = (f"line {mark_line}" in str(e) or
                                         f"column {mark_col}" in str(e) or
                                         (hasattr(e.problem_mark, 'index') and f"position {e.problem_mark.index}" in str(e)))
                if not mark_details_in_str_e:
                    print(f"  问题标记位置: 第 {mark_line} 行, 第 {mark_col} 列 (相对于Front Matter块或解析内容)")
            except (TypeError, ValueError, AttributeError):
                 pass # problem_mark might be None or attributes non-numeric

        if fm_block_identified_for_preprocessing:
            print("  脚本已尝试对常见非标准格式 (如 'key = value', 非标准空格缩进, 及部分控制字符) 进行预处理。")
        print("  如果错误仍然存在，请手动检查文件头 (front matter) 部分是否存在更复杂的 YAML 格式问题，或预处理未能覆盖的情况。")
        print("  标准YAML要求: 1. 'key: value' (冒号分隔); 2. 标准半角空格缩进; 3. 无非法控制字符。")
        return 
    except Exception as e: 
        print(f"解析文件 {file_path} (原文件编码: {detected_encoding or 'N/A'}) 时发生预料之外的错误:")
        traceback.print_exc()
        return

    try:
        post.metadata['categories'] = [new_category]
        output_content_for_file = frontmatter.dumps(post)

        if not isinstance(output_content_for_file, str): 
            if isinstance(output_content_for_file, bytes):
                output_content_for_file = output_content_for_file.decode('utf-8')
            else: 
                raise TypeError(f"frontmatter.dumps() 返回了类型 {type(output_content_for_file)} 而不是预期的 str。")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(output_content_for_file)
        
        print(f"成功更新文件 (并以 UTF-8 保存): {file_path} (原编码: {detected_encoding or 'N/A'})")

    except Exception as e: 
        print(f"更新或写入文件 {file_path} (原编码: {detected_encoding or 'N/A'}) 时发生未知错误:")
        traceback.print_exc()

def process_directory(root_dir, new_category_type):
    if not os.path.isdir(root_dir):
        print(f"错误: 根目录 '{root_dir}' 不存在或不是一个有效的目录。")
        return

    print(f"开始处理目录: {root_dir}")
    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".md"):
                file_path = os.path.join(foldername, filename)
                print(f"正在处理文件: {file_path}")
                update_markdown_file(file_path, new_category_type)
    print(f"\n目录 {root_dir} 处理完成。")

def main():
    if len(sys.argv) != 3:
        print("使用方法: python type.py <根文件夹名称> <类型>") # Assuming script name is type.py based on user output
        print("例如: python type.py ./my_blog '技术'")
        sys.exit(1)

    root_folder_name = sys.argv[1]
    category_type = sys.argv[2]
    
    print("重要提示:")
    print("  - 此脚本会尝试预处理文件头中常见的非标准YAML格式 (如 'key = value', 非标准空格, 及部分控制字符)。")
    print("  - 此预处理功能是实验性的，可能无法覆盖所有情况，甚至可能引入错误。")
    print("  - 强烈建议在对重要文件操作前进行备份，并在小范围数据上测试。")
    print("  - 对于复杂的格式问题，仍需手动修正源文件。")
    print("  - 脚本将尝试用多种编码 (utf-8, gbk, gb2312, latin-1) 读取文件, 并统一以 UTF-8 保存。\n")

    process_directory(root_folder_name, category_type)
    print("\n所有处理已完成。")

if __name__ == "__main__":
    main()
