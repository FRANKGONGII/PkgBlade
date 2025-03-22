import subprocess
import re
import json
import sys
import os
import glob

from output import append_or_create_file

# 目标可执行文件
# 暂时这样写，要不然用参数不好写，路径长
package_exe_file = "./NO_EXE_FILE_FOUND"
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
        append_or_create_file('FILE_CUTTING.txt', f"The path '{path}' does not contain any subfolders.")
        return []
    except Exception as e:
        append_or_create_file('FILE_CUTTING.txt', f"An error occurred: {e}", "Wrong")
        return []


def get_dynamic_symbols(ifInit: bool, package_name_2_version: set):
    # 运行 objdump -T
    # 如果是第一次运行，那么是应该从可执行文件中获取符号表
    append_or_create_file('FILE_CUTTING.txt',
                          "check point: get dynamic symbols" + str(ifInit) + str(package_name_2_version) + str(
                              package_name), "Comand")
    if ifInit == True:
        append_or_create_file('FILE_CUTTING.txt', "run objdump for: " + str(package_exe_file), "Command")
        try:
            result = subprocess.run(
                ["objdump", "-T", package_exe_file],
                text=True,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            append_or_create_file('FILE_CUTTING.txt', "Error running objdump: " + e, "Wrong")
            exit(1)

        # 提取动态符号和所属库
        for line in result.stdout.splitlines():
            # 匹配行：过滤出符号地址、库名称、符号名称
            # 注意这里不管是不是没有定义的符号，因为可能动态链接器还没找到库
            split_line = line.split()
            if len(split_line) > 0 and split_line[-2] != "文件格式" and split_line[-2] != "SYMBOL":
                library, symbol = split_line[-2].strip("()"), split_line[-1]
                dynamic_symbols[symbol] = library

    # 如果不是第一次执行，那么应该从_need文件夹中获取，详细见TODO
    # 这里选择nm -g -u命令
    else:
        append_or_create_file('FILE_CUTTING.txt',
                              "check point: " + str(package_name_2_version) + " " + str(package_name))

        need_o_folder_name = package_name_2_version[package_name] + "_o_needed"
        append_or_create_file('FILE_CUTTING.txt', "check point 2/27 not init" + str(need_o_folder_name))
        for root, _, files in os.walk(need_o_folder_name):
            for file in files:
                if file.endswith(".o"):
                    file_path = os.path.join(root, file)
                    # append_or_create_file('FILE_CUTTING.txt', f"Processing: {file_path}")
                    try:
                        # 使用nm获取符号表，-g表示只列出外部符号，-u表示只列出未定义符号（导入符号）
                        result = subprocess.run(['nm', '-g', '-u', file_path], stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE, text=True)
                        if result.returncode != 0:
                            append_or_create_file('FILE_CUTTING.txt', f"Error processing {file_path}: {result.stderr}",
                                                  "Wrong")
                            return []

                        # 解析nm的输出，提取外部导入符号名
                        for line in result.stdout.splitlines():
                            parts = line.split()
                            if len(parts) >= 2 and parts[0] == 'U':  # 'U'表示未定义（导入的符号）
                                # here: symbol = parts[1]
                                # 只要key，value用不上
                                dynamic_symbols[parts[1]] = {}

                    except Exception as e:
                        append_or_create_file('FILE_CUTTING.txt', f"Error processing {file_path}: {e}")
                        return []
    return dynamic_symbols;


def get_dynamic_libraries():
    try:
        # 执行 ldd 命令
        output = subprocess.check_output(['ldd', package_exe_file], text=True)
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
        # append_or_create_file('FILE_CUTTING.txt', "ldd result: ", libraries)
        return libraries
    except subprocess.CalledProcessError as e:
        append_or_create_file('FILE_CUTTING.txt', f"Error running ldd: {e}", "Wrong")
        return {}
    except FileNotFoundError:
        append_or_create_file('FILE_CUTTING.txt', "Error: ldd command not found. Ensure it is installed.", "Wrong")
        return {}


def make_tags(search_dir):
    # 如果tags文件存在就不要再生成一次了
    if os.path.isfile("tags_" + search_dir.split("/")[-1]):
        append_or_create_file('FILE_CUTTING.txt',
                              f"tags file: " + "tags_" + str(search_dir.split("/")[-1]) + "already exists")
        return
        # 生成 ctags 索引
    # append_or_create_file('FILE_CUTTING.txt', "Generating ctags index...")
    # append_or_create_file('FILE_CUTTING.txt', search_dir)
    if search_dir in symbols_in_ctags_file:
        return
    try:
        subprocess.run(["ctags", "--c-kinds=+fp", "-R", search_dir], check=True)
    except FileNotFoundError:
        append_or_create_file('FILE_CUTTING.txt', "Error: 'ctags' command not found. Please install ctags first.",
                              "Wrong")
        return
    except subprocess.CalledProcessError as e:
        append_or_create_file('FILE_CUTTING.txt', f"Error while running ctags: {e}", "Wrong")
        return
    # 修改tags文件名，不知道为什么ctags命令指定名字有点问题
    try:
        append_or_create_file('FILE_CUTTING.txt', "tags_" + search_dir.split("/")[-1])
        subprocess.run(["mv", "tags", "tags_" + search_dir.split("/")[-1]])
    except FileNotFoundError:
        append_or_create_file('FILE_CUTTING.txt', "Error: tags file not found, check if ctags successfully finished",
                              "Wrong")
        return
    try:
        symbols_in_ctags_file[search_dir] = {}
        with open("tags_" + search_dir.split("/")[-1], "r", encoding="utf-8", errors="replace") as tags_file:
            for line in tags_file:
                split_line = line.split("\t")
                # append_or_create_file('FILE_CUTTING.txt', split_line)
                if split_line[0] in symbols_in_ctags_file[search_dir]:
                    # 之前加入过
                    symbols_in_ctags_file[search_dir][split_line[0]].append(split_line[1])
                else:
                    symbols_in_ctags_file[search_dir][split_line[0]] = [split_line[1]]
    except FileNotFoundError:
        append_or_create_file('FILE_CUTTING.txt', "Error: 'tags' file not found. Ensure ctags ran successfully.",
                              "Wrong")
        return


def get_exe(package):
    global package_exe_file
    append_or_create_file('FILE_CUTTING.txt', "get exe or so for: " + str(package), "Command")
    try:
        output = subprocess.check_output(
            ['dpkg', '-L', package],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except subprocess.CalledProcessError:
        append_or_create_file('FILE_CUTTING.txt', f"Error: error occur while running script for getting package info'.",
                              "Wrong")
    if_find_exe = False
    for line in output.splitlines():
        """
        TODO: 2025/2/26: 
        有的软件包可能就没有可执行文件，例如libpcre2-8-0，因此so文件也是处理的对象。
        或者说除了第一轮循环，都应该以so为优先的处理对象！！这点可以后续再看看要不要实现，如果要就是函数多加上一个参数
        """
        if (line.startswith("/usr/bin") or "bin" in line.split("/")) and line.split("/")[-1] != "bin":
            # 存在可执行的文件，line就是文件地址
            # append_or_create_file('FILE_CUTTING.txt', "get line:", line)
            try:
                output = subprocess.check_output(
                    ["cp", line, "./"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
            except subprocess.CalledProcessError:
                append_or_create_file('FILE_CUTTING.txt', f"Error: Failed to copy exe_file for '{package}'.", "Wrong")
            package_exe_file = line.split('/')[-1]
            if_find_exe = True
            append_or_create_file('FILE_CUTTING.txt', f"sucessfully copy exe_file '{line}' ")

    if if_find_exe == False:
        for line in output.splitlines():
            # 现在暂时设计成没有exe才来获取so，后续必须改动
            if (line.startswith("/usr/lib") or line.startswith("/lib")) and line.split("/")[-1] != "lib" and any(
                    ".so" in s for s in line.split("/")):
                try:
                    output = subprocess.check_output(
                        ["cp", line, "./"],
                        stderr=subprocess.DEVNULL,
                        text=True
                    )
                except subprocess.CalledProcessError:
                    append_or_create_file('FILE_CUTTING.txt', f"Error: Failed to copy so_file for '{package}'.",
                                          "Wrong")
                package_exe_file = line.split('/')[-1]
                append_or_create_file('FILE_CUTTING.txt', f"sucessfully copy so_file '{line}' ")
                break


def get_depends(package):
    # 运行依赖脚本
    try:
        output = subprocess.check_output(
            ['./get_depends.sh', package],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except subprocess.CalledProcessError:
        append_or_create_file('FILE_CUTTING.txt', f"Error: Failed to get package info for '{package}'.", "Wrong")


def run(now_handle_package_name: str, ifInit: bool, package_name_2_version: set):
    global dynamic_symbols
    global package_name
    package_name = now_handle_package_name

    # 清空数据结构
    dynamic_symbols = {}
    dynamic_libraries = {}
    symbols_related_files = {}
    symbols_in_ctags_file = {}

    folder_name = "depends_source_code_" + package_name
    # if os.path.isdir(folder_name):
    #     append_or_create_file('FILE_CUTTING.txt', f"folder '{folder_name}' exists, this package has been handled")
    #     return
    # 获取源码
    append_or_create_file('FILE_CUTTING.txt', "downloading dependencies...", "Command")
    get_depends(package_name)

    # 找exe文件
    append_or_create_file('FILE_CUTTING.txt', "copying executable file...", "Command")
    if ifInit:
        get_exe(package_name)

    # 输出结果
    libraries = []
    """
    TODO：2025/2/27
    1：每次提取符号表应该从_need中提取，而不是.so或者.exe，除了开始的起点
    2：优化为只从上次刚刚放入这个_need文件夹中的.o文件中提取
    """
    dynamic_symbols = get_dynamic_symbols(ifInit=ifInit,
                                          package_name_2_version=package_name_2_version)
    dynamic_libraries = get_dynamic_libraries()

    # 首先预处理依赖库内的所有符号
    depends_library_floder = "depends_source_code_" + package_name
    subfolders = get_subfolders(depends_library_floder)
    for depends_library_subfloder in subfolders:
        make_tags(depends_library_floder + "/" + depends_library_subfloder)
    # for files in symbols_in_ctags_file:
    #     for symbol in symbols_in_ctags_file[files]:
    #         append_or_create_file('FILE_CUTTING.txt', files, symbol, symbols_in_ctags_file[files][symbol])

    if dynamic_symbols:
        # append_or_create_file('FILE_CUTTING.txt', f"{'Symbol':<30} {'Library'}")
        # append_or_create_file('FILE_CUTTING.txt', "-" * 50)
        # for symbol in dynamic_symbols.keys():
        #     library = dynamic_symbols[symbol]
        #     append_or_create_file('FILE_CUTTING.txt', f"{symbol:<30} {library}")
        # # 符号
        # for symbol in dynamic_symbols.keys():
        #     # 符号所属于的库
        #     for files in symbols_in_ctags_file:
        #         # 符号被定义和声明的文件
        #         if symbol in symbols_in_ctags_file[files]:
        #             append_or_create_file('FILE_CUTTING.txt', symbol, files, symbols_in_ctags_file[files][symbol])

        append_or_create_file('FILE_CUTTING.txt', "Symbols Table: ", "Command")
        append_or_create_file('FILE_CUTTING.txt', str(dynamic_symbols))
        with open('symbols.txt', 'w') as f:
            for symbol in dynamic_symbols.keys():
                f.write(symbol + "\n")
    else:
        append_or_create_file('FILE_CUTTING.txt', "No dynamic symbols found.")


if __name__ == "__main__":
    # 检查输入参数，这个后续再完善设计
    if len(sys.argv) < 0:
        append_or_create_file('FILE_CUTTING.txt', "Usage: python extract_symbol.py <symbol> <directory>")
        sys.exit(1)

    # 获取参数，注意是1
    package_name = sys.argv[1]
    run(package_name)
