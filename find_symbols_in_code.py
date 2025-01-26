import os
import subprocess
import copy

need_files = []
now_handle_files = []
now_handle_files_depends = []


def extract_imported_symbols_from_file(file_path):
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
        
        return imported_symbols
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []
    

def extract_symbols_from_file(file_path):
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
        return symbols
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def find_symbols_in_files(symbols, target_dir):
    """
    查找所有符号在目标文件中的导出符号
    """
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.o') or file.endswith('.so'):
                file_path = os.path.join(root, file)
                # print(f"Checking file: {file_path}")
                
                # 提取目标文件的导出符号
                target_symbols = extract_symbols_from_file(file_path)
                
                # 查找每个符号是否在导出符号中
                for symbol in symbols:
                    if symbol in target_symbols:
                        print(f"Symbol '{symbol}' found in {file_path}")
                        # 不要重复添加
                        if file not in need_files and file not in now_handle_files_depends:
                            now_handle_files_depends.append(file)

def load_symbols(symbols_file):
    """
    加载符号列表，符号按行存储
    """
    with open(symbols_file, 'r') as f:
        symbols = [line.strip() for line in f.readlines()]
    return symbols


def generate_need_object_file():
    new_dir = target_dir + "_needed"
    # 创建目标文件夹，如果不存在
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    

if __name__ == "__main__":
    # 需要检查的符号文件和目标文件目录
    symbols_file = 'symbols.txt'  # 符号列表文件
    target_dir = './curl_o'  # 目标文件所在目录

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
            print("now handel file,", file)
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
