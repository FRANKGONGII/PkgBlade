import subprocess
import re
import json
import sys
import os
import glob

# 目标可执行文件
# 暂时这样写，要不然用参数不好写，路径长
binary_file = "./curl"
# 程序参数1 - 要处理的软件包名字
package_name = ""

# 用于记录符号所属于的库
dynamic_symbols = {}
# 用于记录ldd命令查出来的库和路径
dynamic_libraries = {}
# 用于记录这一轮要找的符号定义和声明的文件
symbols_related_files = {}
# 处理ctags文件，直接整理每个符号的信息
symbols_in_ctags_file = {}



def get_subfolders(path):
    try:
        # os.walk 的第一个返回值是当前路径，第二个是子文件夹列表
        _, subfolders, _ = next(os.walk(path))
        return subfolders
    except StopIteration:
        print(f"The path '{path}' does not contain any subfolders.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def get_dynamic_symbols():
    # 运行 objdump -T
    try:
        result = subprocess.run(
            ["objdump", "-T", binary_file],
            text=True,
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Error running objdump:", e)
        exit(1)

    # 提取动态符号和所属库
    for line in result.stdout.splitlines():
        # 匹配行：过滤出符号地址、库名称、符号名称
        # 注意这里不管是不是没有定义的符号，因为可能动态链接器还没找到库
        split_line = line.split()
        if len(split_line) > 0 and split_line[-2] != "文件格式" and split_line[-2] != "SYMBOL":
            library, symbol = split_line[-2].strip("()"), split_line[-1]
            dynamic_symbols[symbol] = library
    return dynamic_symbols;

def get_dynamic_libraries():
    try:
        # 执行 ldd 命令
        output = subprocess.check_output(['ldd', binary_file], text=True)
        # 解析输出
        libraries = {}
        for line in output.splitlines():
            parts = line.split("=>")
            if len(parts) == 2:
                # 动态库格式: libname => path (address)
                lib_name = parts[0].strip()
                lib_info = parts[1].strip()
                if "(" in lib_info:
                    lib_path = lib_info.split()[0]  # 提取路径部分
                else:
                    lib_path = lib_info
                libraries[lib_name] = lib_path
            elif len(parts) == 1:
                # vdso 格式: linux-vdso.so.1 (address)
                lib_name = parts[0].strip().split()[0]
                libraries[lib_name] = "(vdso)"
        print(libraries)
        return libraries
    except subprocess.CalledProcessError as e:
        print(f"Error running ldd: {e}")
        return {}
    except FileNotFoundError:
        print("Error: ldd command not found. Ensure it is installed.")
        return {}

def make_tags(search_dir):
    # 生成 ctags 索引
    # print("Generating ctags index...")
    # print(search_dir)
    if search_dir in symbols_in_ctags_file:
        return  
    try:
        # TODO：使用注释掉的这个命令，下面open的文件也是一样
        # subprocess.run(["ctags", "--c-kinds=+fp", "-R", "-f", "tags_" + search_dir, search_dir], check=True)
        subprocess.run(["ctags","--c-kinds=+fp", "-R", search_dir], check=True)
    except FileNotFoundError:
        print("Error: 'ctags' command not found. Please install ctags first.")
        return
    except subprocess.CalledProcessError as e:
        print(f"Error while running ctags: {e}")
        return
    try:
        symbols_in_ctags_file[search_dir] = {}
        with open("tags", "r", encoding="utf-8", errors="replace") as tags_file:
            for line in tags_file:
                split_line = line.split("\t")
                # print(split_line)
                if split_line[0] in symbols_in_ctags_file[search_dir]:
                    # 之前加入过
                    symbols_in_ctags_file[search_dir][split_line[0]].append(split_line[1])
                else:
                    symbols_in_ctags_file[search_dir][split_line[0]] = [split_line[1]]
    except FileNotFoundError:
        print("Error: 'tags' file not found. Ensure ctags ran successfully.")
        return
    
def get_exe(package):
    try:
        output = subprocess.check_output(
            ['dpkg', '-L',  package],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except subprocess.CalledProcessError:
        print(f"Error: Failed to get package info for '{package}'.")
    for line in output.splitlines():
        if (line.startswith("/usr/bin") or "bin" in line.split("/")) and line.split("/")[-1] != "bin":
            # 存在可执行的文件，line就是文件地址
            print("get line:", line)
            try: 
                output = subprocess.check_output(
                    ["cp", line, "./"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
            except subprocess.CalledProcessError:
                print(f"Error: Failed to copy exe_file for '{package}'.")
            print(f"sucessfully copy exe_file '{line}' ")


def get_depends(package):
    # 运行依赖脚本
    try:
        output = subprocess.check_output(
            ['./get_depends.sh', package],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except subprocess.CalledProcessError:
        print(f"Error: Failed to get package info for '{package}'.")
    
if __name__ == "__main__":
    # 检查输入参数，这个后续再完善设计
    if len(sys.argv) < 0:
        print("Usage: python extract_symbol.py <symbol> <directory>")
        sys.exit(1)

    # 获取参数，注意是1
    package_name = sys.argv[1]

    # 获取源码
    get_depends(package_name)

    # 找exe文件
    print("start get exe")
    get_exe(package_name)

    # 输出结果
    libraries = []
    dynamic_symbols = get_dynamic_symbols()
    dynamic_libraries = get_dynamic_libraries()

    # 首先预处理依赖库内的所有符号
    depends_library_floder = "depends_source_code_" + package_name
    subfolders = get_subfolders(depends_library_floder)
    for depends_library_subfloder in subfolders:
        make_tags(depends_library_floder + "/" + depends_library_subfloder)
    # for files in symbols_in_ctags_file:
    #     for symbol in symbols_in_ctags_file[files]:
    #         print(files, symbol, symbols_in_ctags_file[files][symbol])

    if dynamic_symbols:
        print(f"{'Symbol':<30} {'Library'}")
        print("-" * 50)
        for symbol in dynamic_symbols.keys():
            library = dynamic_symbols[symbol]
            print(f"{symbol:<30} {library}")
        # 符号
        for symbol in dynamic_symbols.keys():
            # 符号所属于的库
            for files in symbols_in_ctags_file:
                # 符号被定义和声明的文件
                if symbol in symbols_in_ctags_file[files]:
                    print(symbol, files, symbols_in_ctags_file[files][symbol]) 
        
        with open('symbols.txt', 'w') as f:
            for symbol in dynamic_symbols.keys():
                f.write(symbol + "\n")
    else:
        print("No dynamic symbols found.")