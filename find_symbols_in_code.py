import os
import subprocess
import copy
import shutil
import re


# TODO：筛选的这些数据结构计划上是每一轮循环取并集
# 筛选需要的文件部分
need_files = []
now_handle_files = []
now_handle_files_depends = []
# 初始的符号
symbols = []

# 标记需要删除的文件里的符号
"""
file: [symbols]
"""
inneed_file_symbols = {}

# 记录导出符号和导入符号
file_import_symbols = {}
file_export_symbols = {}

# TODO：硬编码，后续需要删掉
target_package = "curl"

# 需要检查的符号文件和目标文件目录
symbols_file = 'symbols.txt'  # 符号列表文件
# 目标文件所在目录
target_dir = 'curl_o'  
# target_dir = "glibc_o"



def extract_imported_symbols_from_file(file_path):
    if file_path in file_import_symbols:
        return file_import_symbols[file_path]
    """
    使用nm提取目标文件的外部导入符号（未定义符号）。
    """
    try:
        # 使用nm获取符号表，-g表示只列出外部符号，-u表示只列出未定义符号（导入符号）
        result = subprocess.run(['nm', '-g', '-u', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error processing {file_path}: {result.stderr}")
            return []
        # print(result)
        
        # 解析nm的输出，提取外部导入符号名
        imported_symbols = []
        for line in result.stdout.splitlines():
            parts = line.split()
            # print(parts)
            if len(parts) >= 2 and parts[0] == 'U':  # 'U'表示未定义（导入的符号）
                symbol_name = parts[1]  # 符号名
                imported_symbols.append(symbol_name)

        file_import_symbols[file_path] = imported_symbols
        return imported_symbols
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []
    
def extract_exported_symbols_from_file(file_path):
    if file_path in file_export_symbols:
        return file_export_symbols[file_path]
    """
    使用nm提取目标文件的导出符号
    """
    try:
        # 使用nm获取符号表（只关注导出符号）
        result = subprocess.run(['nm', '-g', '--defined-only', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error processing {file_path}: {result.stderr}")
            return []
        
        # 解析nm的输出，提取符号名
        symbols = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                symbol_name = parts[2]  # 符号名
                symbols.append(symbol_name)
        # print(symbols)
        file_export_symbols[file_path] = symbols
        return symbols
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def find_symbols_in_files(symbols, target_dir):
    """
    查找所有符号在目标文件中的导出符号
    """
    for symbol in symbols:
        iffind = False
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.o') or file.endswith('.so'):
                    file_path = os.path.join(root, file)
                    # print(f"Checking file: {file_path}")
                    # 提取目标文件的导出符号
                    target_symbols = extract_exported_symbols_from_file(file_path)
                    if symbol in target_symbols:
                        print(f"Symbol '{symbol}' found in {file_path}")
                        iffind = True
                        # 不要重复添加
                        if file not in need_files and file not in now_handle_files_depends:
                            now_handle_files_depends.append(file)
        if iffind == False:
            print("cannot find symbol", symbol)

def load_symbols(symbols_file):
    """
    加载符号列表，符号按行存储
    """
    with open(symbols_file, 'r') as f:
        symbols = [line.strip() for line in f.readlines()]
    return symbols

def find_file(directory, target_name):
    """
    在指定目录及其子目录查找目标文件
    """
    for root, _, files in os.walk(directory):
        if target_name in files:
            return os.path.join(root, target_name)
    return None  # 未找到文件

def generate_need_object_file(target_dir, need_files):
    """
    复制需要的目标文件，对于不要的文件实现(.c)注释掉全部
    """
    new_dir = target_dir + "_needed"
    source_dir = "depends_source_code_" +  target_package + "/curl-7.81.0"
    inneed_files = []
    # 创建目标文件夹，如果不存在
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    for i in range(len(need_files)):
        file_path = target_dir + "/" + need_files[i]
        if os.path.exists(file_path):
            # 构造目标路径
            target_path = os.path.join(new_dir, os.path.basename(file_path))
            shutil.copy(file_path, target_path)
            print(f'Copied: {file_path} -> {target_path}')
        else:
            print(f'File not found: {file_path}')
    
    # 修改一下目标文件文件名为源文件文件名
    for i in range(len(need_files)):
        need_files[i] = need_files[i][:-2]

    # 构建不需要的文件名list
    for dirpath, _, filenames in os.walk(target_dir):
        for filename in filenames:
            if filename[:-2] in need_files:
                continue
            else:
                inneed_files.append(filename[:-2])
    print(inneed_files)

    # 把不需要的文件注释掉，不影响构建
    # 遍历依赖源文件夹
    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename in inneed_files:
                file_path = os.path.join(dirpath, filename)
                # 允许列表可以是完整路径，也可以是文件名
                if file_path in need_files or filename in need_files:
                    print(f"Skipping {file_path} (allowed)")
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # 注释掉所有行（避免重复注释已存在的注释行）
                commented_lines = ["// " + line if not line.lstrip().startswith("//") else line for line in lines]

                # 写回文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(commented_lines)

                print(f"Finished commenting {file_path}")

def functional_trimming(target_dir):
    """
    处理筛选出的需要的目标文件集合，找出其中没有被使用的符号
    """
    print("strat symbols check")
    print(symbols)
    need_dir = target_dir + "_needed"
    all_import_symbols = set()
    # 这里是把目标软件包的直接依赖也加进来
    for s in symbols:
        all_import_symbols.add(s)
    all_export_symbols = {}
    # 遍历所有需要的目标文件
    for root, dirs, files in os.walk(need_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # 这里要想一想，怎么构建这个需要的图比较好
            file_import_symbols = extract_imported_symbols_from_file(file_path)
            file_output_symbols = extract_exported_symbols_from_file(file_path)
            for symbol in file_output_symbols:
                # 记录每个符号是哪个文件提供的
                # TODO：提前这部分，可以优化
                if symbol not in all_export_symbols:
                    all_export_symbols[symbol] = []
                all_export_symbols[symbol].append(file)
            for symbol in file_import_symbols:
                # 记录每个引用符号
                all_import_symbols.add(symbol)
            print(file, file_import_symbols, file_output_symbols)
    # 处理不需要的符号
    for export_symbol in all_export_symbols:
        if export_symbol not in all_import_symbols:
            # 这个符号不在需要的import里面，就先标记
            # 所有相关的文件都要标记，可能有多个文件定义同名符号
            for file in all_export_symbols[export_symbol]:
                if file not in inneed_file_symbols:
                    inneed_file_symbols[file] = {}
                inneed_file_symbols[file][export_symbol] = {}
    print("finish unused symbols check: ", inneed_file_symbols)

    # 获取symbol的位置
    # TODO：考虑同名问题：符号&文件
    # TODO：修改tags文件名字
    with open("tags", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            # TODO: f代表只处理函数
            if len(parts) <= 3 or parts[3] != 'f':
                continue
            symbol = parts[0]
            file_path = parts[1]
            search_pattern = parts[2]

            file_name = file_path.split('/')[-1] + ".o"
            if file_name in inneed_file_symbols:
                # 有同名文件
                if symbol in inneed_file_symbols[file_name]:
                    # 找到了
                    inneed_file_symbols[file_name][symbol] = search_pattern[2:-4]
                    inneed_file_symbols[file_name][file_name + "_path"] = file_path
    print("finish unused symbols find: ", inneed_file_symbols)
    
    # 开始在文件中删除
    for file_name in inneed_file_symbols:
        # TODO: 这里是和前面一起的，我暂时只处理函数
        if file_name + "_path" not in inneed_file_symbols[file_name]:
            continue
        source_file_path = inneed_file_symbols[file_name][file_name + "_path"]
        to_comment_symbols = inneed_file_symbols[file_name]

        if not os.path.exists(source_file_path):
            print(f"文件 {source_file_path} 不存在.")
            return

        # 读取文件内容
        print(file_name, source_file_path)
        with open(source_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # print(lines)
        for to_match_symbol in to_comment_symbols:
            to_match_pattern = to_comment_symbols[to_match_symbol]
            # print(to_match_pattern)
            for i, line in enumerate(lines, start=1):
                # print(f"Checking pattern: {to_match_pattern}")
                # TODO:有一些pattern居然是空的
                if to_match_pattern == line.strip():
                    print(to_match_symbol, "||||" , to_match_pattern, "line: ", i)
                    break










            

            

            


if __name__ == "__main__":
    # 加载符号列表
    symbols = load_symbols(symbols_file)
    print("intial symbols:", symbols)

    # 查找符号在目标文件中的导出情况
    find_symbols_in_files(symbols, target_dir)
    need_files = copy.deepcopy(now_handle_files_depends)
    now_handle_files = copy.deepcopy(need_files)

    print("initial round ends, ", now_handle_files, now_handle_files_depends)

    # 目前now_handle_files就是需要的文件(第一轮)
    while now_handle_files:
        # 当前待处理文件
        current_files = copy.deepcopy(now_handle_files)
        print("current files. ",current_files)
        now_handle_files_depends.clear()
        # 对每个文件进行符号导入检查
        for file in current_files:
            print("now handle file,", file)
            file_path = os.path.join(target_dir, file)
            if os.path.exists(file_path):
                # 提取导入符号
                target_symbols = extract_imported_symbols_from_file(file_path)
                print("now handle file imports, ", target_symbols, file_path)
                # 查找导入符号的定义文件
                find_symbols_in_files(target_symbols, target_dir)
                print("found files: ", now_handle_files_depends)
            else:
                print("no such file:" + file_path)
        for file in now_handle_files_depends:
            if file not in need_files:
                need_files.append(file)
        now_handle_files = copy.deepcopy(now_handle_files_depends)
        print("a round ends!", need_files)


    print(need_files, len(need_files))
    generate_need_object_file(target_dir, need_files)
    functional_trimming(target_dir)
