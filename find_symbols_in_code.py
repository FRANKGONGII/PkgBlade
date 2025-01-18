import os
import subprocess
import sys
import re

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
    symbol_define_file = ""
    print(f"Searching for symbol '{symbol}' in ctags index...")
    try:
        with open("tags", "r") as tags_file:
            found_in_tags = False
            for line in tags_file:
                if symbol in line.split("\t"):
                    print(f"Found in ctags index:\n{line.strip()}")
                    found_in_tags = True
                    # 这里的换行符是\t....
                    symbol_define_file = line.strip().split("\t")[1]
            if not found_in_tags:
                print(f"Symbol '{symbol}' not found in ctags index.")
    except FileNotFoundError:
        print("Error: 'tags' file not found. Ensure ctags ran successfully.")
        return

    # 使用 grep -rnw 查找符号的使用，这里就找到了声明的地方(头文件)
    symbol_declare_file = set()
    print(f"\nUsing 'grep -rnw' to search for symbol '{symbol}' in '{search_dir}'...")
    try:
        result = subprocess.run(["grep", "-rnw", symbol, search_dir], 
                                text=True, capture_output=True, check=False)
        if result.stdout:
            print("Results from 'grep -rnw':\n" + result.stdout)
            lines = result.stdout.splitlines()
            # 使用正则匹配 .h 文件的结果，前面已经有了定义的位置，这里是声明
            pattern = re.compile(r'\.h:\d+:')
            h_file_results = [line for line in lines if pattern.search(line)]
            print("\nFiltered results in .h files:")
            print(len(h_file_results))
            if len(h_file_results) != 0:
                for result in h_file_results:
                    # print(result)
                    split_h_result = result.split(":")
                    symbol_declare_file.add(split_h_result[0])
            print(symbol_declare_file)
        else:
            print(f"No results found using 'grep -rnw' for symbol '{symbol}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running grep -rnw: {e}")
        return
    return symbol_define_file, symbol_declare_file


if __name__ == "__main__":
    # 检查输入参数
    if len(sys.argv) != 3:
        print("Usage: python find_symbol.py <symbol> <directory>")
        sys.exit(1)

    # 获取参数
    symbol_to_find = sys.argv[1]
    directory_to_search = sys.argv[2]

    # 查找符号
    symbol_define_file, symbol_declare_file =  find_symbol(symbol_to_find, directory_to_search)
    print(symbol_define_file, symbol_declare_file)
