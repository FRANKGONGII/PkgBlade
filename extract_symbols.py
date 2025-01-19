import subprocess
import re
import json
import sys
import os

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

def find_symbol(symbol, search_dir):
    if not os.path.isdir(search_dir):
        print(f"Error: Directory '{search_dir}' does not exist.")
        return

    # 生成 ctags 索引
    print("Generating ctags index...")
    try:
        subprocess.run(["ctags", "-R", search_dir], check=True)
    except FileNotFoundError:
        print("Error: 'ctags' command not found. Please install ctags first.")
        return
    except subprocess.CalledProcessError as e:
        print(f"Error while running ctags: {e}")
        return

    # 在 tags 文件中精确查找符号，这里等于查找到了符号定义的地方
    symbol_define_file = set()
    print(f"Searching for symbol '{symbol}' in ctags index...")
    try:
        with open("tags", "r", encoding="utf-8", errors="replace") as tags_file:
            found_in_tags = False
            for line in tags_file:
                if symbol in line.split("\t"):
                    # print(f"Found in ctags index:\n{line.strip()}")
                    found_in_tags = True
                    # 这里的换行符是\t....
                    symbol_define_file.add(line.strip().split("\t")[1])
            if not found_in_tags:
                print(f"Symbol '{symbol}' not found in ctags index.")
    except FileNotFoundError:
        print("Error: 'tags' file not found. Ensure ctags ran successfully.")
        return

    # 使用 grep -rnw 查找符号的使用，这里就找到了声明的地方(头文件)
    # 这里直接打印是set()。。。
    symbol_declare_file = set()
    print(f"\nUsing 'grep -rnw' to search for symbol '{symbol}' in '{search_dir}'...")
    try:
        result = subprocess.run(["grep", "-rnw", symbol, search_dir], 
                                text=True, capture_output=True, check=False)
        if result.stdout:
            # print("Results from 'grep -rnw':\n" + result.stdout)
            lines = result.stdout.splitlines()
            # 使用正则匹配 .h 文件的结果，前面已经有了定义的位置，这里是声明
            pattern = re.compile(r'\.h:\d+:')
            h_file_results = [line for line in lines if pattern.search(line)]
            # print("\nFiltered results in .h files:")
            if len(h_file_results) != 0:
                for result in h_file_results:
                    # print(result)
                    split_h_result = result.split(":")
                    symbol_declare_file.add(split_h_result[0])
            # print(symbol_declare_file)
        else:
            print(f"No results found using 'grep -rnw' for symbol '{symbol}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running grep -rnw: {e}")
        return
    return {} if symbol_define_file == set() else symbol_define_file, {} if symbol_declare_file == set() else symbol_declare_file

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


if __name__ == "__main__":
    # 检查输入参数，这个后续再完善设计
    if len(sys.argv) < 0:
        print("Usage: python extract_symbol.py <symbol> <directory>")
        sys.exit(1)

    # 获取参数，注意是1
    package_name = sys.argv[1]

    # 输出结果
    libraries = []
    dynamic_symbols = get_dynamic_symbols()
    dynamic_libraries = get_dynamic_libraries()
    if dynamic_symbols:
        print(f"{'Symbol':<30} {'Library'}")
        print("-" * 50)
        for symbol in dynamic_symbols.keys():
            library = dynamic_symbols[symbol]
            print(f"{symbol:<30} {library}")
            # 现在开始找
                # libraries.append(symbol)
                # # 先写入到json文件，等待后续查询
                # with open("./output/record.json","w") as f:
                #     new_dict = {binary_file : libraries}
                #     json.dump(new_dict,f)
        for symbol in dynamic_symbols.keys():
            # 在每个库里面去找，源码在"depends_source_code_“ + 包名字文件夹
            depends_library_floder = "depends_source_code_" + package_name
            subfolders = get_subfolders(depends_library_floder)
            for depends_library_subfloder in subfolders:
                symbol_define_file, symbol_declare_file = find_symbol(symbol, depends_library_subfloder)
                if len(symbol_declare_file) != 0 and len(symbol_define_file) != 0:
                    # print("---------------", symbol, "||", symbol_declare_file, "||", symbol_define_file)
                    symbols_related_files[symbol] = (symbol_define_file, symbol_declare_file)
            # for depend_library in dynamic_libraries.keys():
            #     if dynamic_libraries[depend_library] == "(vdso)":
            #         # 暂时不处理这个情况
            #         continue
            #     elif dynamic_libraries[depend_library] == "not found":
            #         # 没找到，需要在当前目录找
            #         # 首先得到动态库的位置
            #         depend_library_path = "./examples/library" + depend_library
            #         # print(symbol, depend_library, depend_library_path)
            #     else:
            #         depend_library_path = dynamic_libraries[depend_library]
            #         symbol_define_file, symbol_declare_file = find_symbol(symbol, "curl-7.81.0")
            #         if symbol_declare_file != "":
            #             print(symbol, symbol_declare_file, symbol_define_file)
        print(symbols_related_files)
    else:
        print("No dynamic symbols found.")