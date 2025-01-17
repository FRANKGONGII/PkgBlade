import subprocess
import re
import json

# 目标可执行文件
# 暂时这样写，要不然用参数不好写，路径长
binary_file = "./curl"

# 用于记录符号所属于的库
dynamic_symbols = {}
# 用于记录ldd命令查出来的库和路径
dynamic_libraries = {}

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
        # 在每个库里面去找
        for depend_library in dynamic_libraries.keys():
            if dynamic_libraries[depend_library] == "(vdso)":
                # 暂时不处理这个情况
                continue
            elif dynamic_libraries[depend_library] == "not found":
                # 没找到，需要在当前目录找
                # 首先得到动态库的位置
                depend_library_path = "./examples/library" + depend_library
                # print(symbol, depend_library, depend_library_path)
            else:
                depend_library_path = dynamic_libraries[depend_library]
                
                # print(depend_library, dynamic_libraries[depend_library])
                # print("lib has installed")
                # 判断在不在



else:
    print("No dynamic symbols found.")