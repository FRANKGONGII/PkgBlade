import os
import subprocess
import copy
import shutil
import re
import sys


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
target_package = "wget"

# 需要检查的符号文件和目标文件目录
symbols_file = 'symbols.txt'  # 符号列表文件
# 目标文件所在目录
# target_dir = 'pcre_o'  
# target_dir = "glibc_o"
# dependency_real_name = 'pcre2-10.39'  

# 为了把符号裁剪移到最后保存一些东西
trimming_record = {}



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
    # 修改一下，首先构建文件的符号
    # print("find symbols in files: ", now_handle_files_depends, target_dir)
    # print("file export symbols: ", file_export_symbols)
    for symbol in symbols:
        iffind = False
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.o') or file.endswith('.so'):
                    file_path = os.path.join(root, file)
                    # print(f"Checking file: {file_path}")
                    # 提取目标文件的导出符号
                    target_symbols = extract_exported_symbols_from_file(file_path)
                    # print("file symbols: ",target_symbols)
                    if symbol in target_symbols:
                        # print(f"Symbol '{symbol}' found in {file_path}")
                        iffind = True
                        # 不要重复添加
                        if file not in need_files and file not in now_handle_files_depends:
                            now_handle_files_depends.append(file)
        if iffind == False:
            # print("cannot find symbol", symbol)
            a = 1
    # print("find symbols in files end: ", now_handle_files_depends)
    
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



def check_file_exists(directory: str, filename: str) -> bool:
    """
    检查指定目录下是否存在指定名称的文件。
    
    :param directory: 目录路径
    :param filename: 要检查的文件名
    :return: 如果存在返回 True，否则返回 False
    """
    file_path = os.path.join(directory, filename)
    return os.path.isfile(file_path)




def generate_need_object_file(target_dir, need_files):

    """
    TODO： 2025/2/27：把注释文件这一步提取出来，先不要注释，等到整个循环都完成了再去处理
    """
    """
    复制需要的目标文件，对于不要的文件实现(.c)注释掉全部
    """
    new_dir = target_dir + "_needed"
    # -2是_o
    source_dir = "depends_source_code_" +  target_package + "/" + target_dir[:-2]
    print(source_dir, "------")
    inneed_files = []
    # 创建目标文件夹，如果不存在
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    for i in range(len(need_files)):
        file_path = target_dir + "/" + need_files[i]
        if os.path.exists(file_path):
            # 构造目标路径
            target_path = os.path.join(new_dir, os.path.basename(file_path))
            print("check if file already exits: ", check_file_exists(new_dir, need_files[i]))
            shutil.copy(file_path, target_path)
            print(f'Copied: {file_path} -> {target_path}')
        else:
            print(f'File not found: {file_path}')
    
    # 修改一下目标文件文件名为源文件文件名
    for i in range(len(need_files)):
        need_files[i] = need_files[i][:-2]
        if need_files[i].endswith(".c") == False:
            need_files[i] = need_files[i] + ".c"


    # need_files内保证以.c结尾
    print("need files," ,target_dir ,need_files, len(need_files))

    # 构建不需要的文件名list
    # 注意有.c.o和.c两种可能的文件名字结尾
    for dirpath, _, filenames in os.walk(target_dir):
        for filename in filenames:
            # 如果是.c.o, 那么用.c判断
            if filename.endswith(".c.o") and filename[:-2] in need_files:
                continue
            # 如果是.o，那么去掉之后加上.c判断
            elif filename.endswith(".o") and filename[:-2] + ".c" in need_files:
                continue
            else:
                if filename.endswith(".o"):
                    filename = filename[:-2]
                if filename.endswith(".c") == False:
                    filename = filename + ".c"
                inneed_files.append(filename)
    print("inneed files to delete: ", target_dir, inneed_files, len(inneed_files))


    """
    TODO：2027/2/27：这块抽象为一个函数后续在main调用
    """
    # 把不需要的文件注释掉，不影响构建
    # 遍历依赖源文件夹
    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename in inneed_files:
                file_path = os.path.join(dirpath, filename)
                print("delete file path: ", file_path)
                # 允许列表可以是完整路径，也可以是文件名
                if file_path in need_files or filename in need_files:
                    print(f"Skipping {file_path} (allowed)")
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                has_main_func = False
                # 注释掉所有行（避免重复注释已存在的注释行）
                # -2是去掉.c
                if (target_dir + "/" + filename[:-2] +  ".o" in file_export_symbols):
                    if "main" in file_export_symbols[target_dir + "/" + filename[:-2] +  ".o"]:
                        has_main_func = True
                if (target_dir + "/" + filename[:-2] +  ".c.o" in file_export_symbols):
                    if "main" in file_export_symbols[target_dir + "/" + filename[:-2] +  ".c.o"]:
                        has_main_func = True
                    
                commented_lines = ["// " + line if not line.lstrip().startswith("//") else line for line in lines]
                
                
                # 这种判断方法不太准确。。
                # # 考虑原本有main函数的情况，不能全部注释掉，否则会报错
                # for line in lines:
                #     # 还有可能有这种鬼东西，所以单main()前面得有个空格判断一下
                #     # tinytest_main(int c, const char **v, struct testgroup_t *groups)
                #     if " main (" in line or " main(" in line or line.startswith("main("):
                #         has_main_func = True
                
                if has_main_func:
                    commented_lines.append("int main(){return 0;}")
                         

                # 写回文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(commented_lines)

                print(f"Finished commenting {file_path}")

def functional_trimming(target_dir):
    """
    处理筛选出的需要的目标文件集合，找出其中没有被使用的符号
    """
    print("start symbols check: ", target_dir)
    print("trimming record: ", trimming_record)
    # print(symbols)
    # 不处理libc，保证key存在
    if "glibc" in target_dir.split("-") or target_dir not in trimming_record:
        return 
    need_dir = target_dir + "_needed"
    all_import_symbols = set()
    # 这里是把目标软件包的直接依赖也加进来
    # trimming_record[target] 里面是 symbol
    for s in trimming_record[target_dir]:
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
                if symbol not in all_export_symbols:
                    all_export_symbols[symbol] = []
                all_export_symbols[symbol].append(file)
            for symbol in file_import_symbols:
                # 记录每个引用符号
                all_import_symbols.add(symbol)
            # print(file, file_import_symbols, file_output_symbols)
    # 处理不需要的符号
    # TODO: 一个问题估计是内部有用的怎么办。。也就是其他文件没有用，但是自己用了
    for export_symbol in all_export_symbols:
        if export_symbol not in all_import_symbols:            
            # 所有相关的文件都要标记，可能有多个文件定义同名符号
            for file in all_export_symbols[export_symbol]:
                if file not in inneed_file_symbols:
                    inneed_file_symbols[file] = {}
                inneed_file_symbols[file][export_symbol] = {}
    # print("finish unused symbols check: ", inneed_file_symbols)


        
    # 通过tags文件获取symbol的位置
    # TODO：考虑同名问题：符号&文件
    with open("tags_" + target_dir[:-2], "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            # TODO: f代表只处理函数，暂时现就这样
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
        # 没有获取到地址就跳过
        if file_name + "_path" not in inneed_file_symbols[file_name]:
            continue
        source_file_path = inneed_file_symbols[file_name][file_name + "_path"]
        to_comment_symbols = inneed_file_symbols[file_name]

        if not os.path.exists(source_file_path):
            print(f"文件 {source_file_path} 不存在.")
            return

        # 读取文件内容
        # print(file_name, source_file_path)
        with open(source_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # print(lines)
        for to_match_symbol in to_comment_symbols:
            
            # 检查这个符号在定义它的文件内出现的次数，如果大于1就有可能有别的引用，可以不删除
            occurrences = sum(line.count(to_match_symbol) for line in lines)
            print("symbol: ", to_match_symbol,  occurrences)
            if occurrences > 1:
                print("symbol ", to_match_symbol, " may use in ", file_name, " skip symbol delete")
                continue
            
            to_match_pattern = to_comment_symbols[to_match_symbol]
            # print(to_match_pattern)
            for i, line in enumerate(lines, start=1):
                if line[0] == '#':
                    continue
                # print(f"Checking pattern: {to_match_pattern}")
                # TODO:有一些pattern居然是空的
                if to_match_pattern == line.strip():
                    print(to_match_symbol, "||||" , to_match_pattern, "line: ", i)
                    # 开始统计
                    left_count = 0
                    right_count = 0
                    end_line = i
                    # 2025/3/10：这里有一个问题，i是行数，从下标i开始会忽略起始行to_match_pattern，但是这里也可能有括号。。
                    # 所以从i-1开始，也就是从函数名所在行开始计算
                    for j in range(i - 1, len(lines)):
                        line_j = lines[j]
                        for ch in line_j:
                            # print(line_j)
                            if ch == '{':
                                left_count += 1
                                # print("found { :", j, line_j)
                            elif ch == '}':
                                right_count += 1
                                # print("found } :", j, line_j)
                        if left_count == right_count and left_count != 0:
                            end_line = j + 1
                            break
                    # 注释掉[i,end_line]内的全部内容，写回文件， 注意这两个都是在文件内的行数目，不是下标（要-1）
                    # print(i ,end_line)
                    # 确认开始行，防止函数返回值和函数名称不在同一行的情况，以(为检查点
                    # 满足一下两种情况说明是不用前移的
                    # 1. xx foo( : (前面有东西，而且在整个行内至少是第二个
                    # 2. xx foo ( : (前面没有东西，而且在整个行内至少是第三个
                    line_start = lines[i-1]
                    line_start_split = line_start.split(" ")
                    check_point = -1
                    for s in range(0, len(line_start_split)):
                        if '(' in line_start_split[s]:
                            check_point = s
                            break;
                    # print("========", line_start_split, check_point)
                    if (lines[check_point][0] == '(' and check_point <= 1) or (lines[check_point][0] != '(' and check_point == 0):
                        i -= 1 
                    for k in range(i - 1, end_line):
                        lines[k] = "// " + lines[k]
                    #print(i ,end_line)
        # 写回
        with open(source_file_path, "w") as f:
            f.writelines(lines)
            
    inneed_file_symbols.clear()

                    

def handle_each_depend(now_target_dir):
    global need_files
    global now_handle_files
    global now_handle_files_depends
    """
    以每个文件夹为单位处理依赖
    """
    print("now target: ", now_target_dir, "symbols:", symbols)
    # 查找符号在目标文件中的导出情况
    find_symbols_in_files(symbols, now_target_dir)
    # print("now_handle_files_depends: ", now_handle_files_depends)
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
            # print("now handle file,", file)
            file_path = os.path.join(now_target_dir, file)
            if os.path.exists(file_path):
                # 提取导入符号
                target_symbols = extract_imported_symbols_from_file(file_path)
                # print("now handle file imports, ", target_symbols, file_path)
                # 查找导入符号的定义文件
                find_symbols_in_files(target_symbols, now_target_dir)
                # print("found files: ", now_handle_files_depends)
            else:
                print("no such file:" + file_path)
        # 通过有没有新的来判断
        ifNewFile = False
        for file in now_handle_files_depends:
            if file not in need_files:
                need_files.append(file)
                ifNewFile = True
        if ifNewFile == False:
            break;
        now_handle_files = copy.deepcopy(now_handle_files_depends)
        # print("now handle files: ", len(now_handle_files), now_handle_files)
        print("a round ends!", len(need_files))


    print(len(need_files), need_files)
    generate_need_object_file(now_target_dir, need_files)
    
    # 本来是直接trimming的，但是现在要延后。。
    # 这里要考虑一个情况
    # A - C， B - C，多个包依赖同一个
    # 所以每次都是往里面加符号就行
    if now_target_dir not in trimming_record:
        trimming_record[now_target_dir] = set()
    for s in symbols:
        trimming_record[now_target_dir].add(s)
    


def run(target_package_name : str) -> map:
    """
        裁减的入口，返回值是每个依赖是否被处理了
    """
    # 这里要直接修改全局的symbols。。
    global symbols
    global target_package
    symbols = load_symbols(symbols_file)
    target_package = target_package_name
    print("intial symbols:", symbols)
    folder_path = "./depends_source_code_" + target_package_name

    dependencies_source_code = [entry.name for entry in os.scandir(folder_path) if entry.is_dir()]

    print("package dependencies: ", dependencies_source_code)    
    if_handle_dependency = {}

    for depends in dependencies_source_code:
        print(depends)
        sys.stdout.flush()
        command = input("print y to handle this dependency...\n")
        if command == "y":
            handle_each_depend(depends + "_o")
            if_handle_dependency[depends] = "yes"
        else:
            if_handle_dependency[depends] = "no"

    # 结束run前清空数据结构
    need_files.clear()
    now_handle_files.clear()
    now_handle_files_depends.clear()
    symbols.clear()
    inneed_file_symbols.clear()
    file_import_symbols.clear()
    file_export_symbols.clear()
    return if_handle_dependency


if __name__ == "__main__":

    # 检查输入参数，这个后续再完善设计
    if len(sys.argv) < 0:
        print("Usage: python extract_symbol.py <symbol> <directory>")
        sys.exit(1)

    target_package = sys.argv[1]

    run(target_package)

    
    # handle_each_depend("pcre2-10.39_o")

    # handle_each_depend("libidn2-2.3.2_o")

    # handle_each_depend("glibc-2.35_o")

    
