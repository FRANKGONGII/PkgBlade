import sys
import subprocess
import re
import extract_symbols
import find_symbols_in_code


# 当前处理的package名
now_handle_package = set()
# 当前处理的package的依赖
now_handle_package_dependcies = set()
# 所有依赖的信息，格式:
"""

"""
all_dependcies_info = {}

def extract_depends(line: str) -> list:
    """
        从依赖关系字符串中提取软件包名称，去掉版本号要求
        例如 "libgcc-s1, libcrypt1 (>= 1:4.4.10-10ubuntu4)"
        ["libgcc-s1", "libcrypt1"]
        注意有可能有这种情况：Depends: libc6 (>= 2.34), debconf (>= 0.5) | debconf-2.0
    """
    if line.startswith("Depends"):
        line = line.removeprefix("Depends: ")
        clean_str = re.sub(r"\s*\([^)]*\)", "", line)
        dependcies = [pkg.strip() for pkg in clean_str.split(",")]
        for i in range(0, len(dependcies)):
            d = dependcies[i]
            if " | " in d:
                # 说明配置了多个可用的依赖，选一个就行了
                dependcies[i] = d.split(" | ")[0]
        return dependcies
    else:
        return []


if __name__ == "__main__":
    # 检查输入参数，这个后续再完善设计
    if len(sys.argv) < 0:
        print("Usage: python extract_symbol.py <symbol> <directory>")
        sys.exit(1)

    # 初始情况下只有一个依赖
    start_package_name = sys.argv[1]
    now_handle_package.add(start_package_name)

    try:
        output = subprocess.check_output(
            ['apt', 'show',  start_package_name],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except subprocess.CalledProcessError:
        print(f"Error: Failed to get package info for '{start_package_name}'.")
    
    # 找到依赖
    for line in output.splitlines():
        if line.startswith("Depends:"):
            now_handle_package_dependcies = extract_depends(line=line)

    # 开始处理
    # 获取源码&开始裁减
    # extract_symbols.run(start_package_name)
    # print("extract ends!")
    # find_symbols_in_code.run(start_package_name)
    # print("slimming ends!")


    # 对于每个依赖获取它们的仓库名字和依赖的依赖
    # TODO：如果没有Source那么需要特殊处理，可能只能用字符串相似度
    print(now_handle_package_dependcies)
    for depend in now_handle_package_dependcies:
        try:
            output = subprocess.check_output(
                ['apt', 'show',  depend],
                stderr=subprocess.DEVNULL,
                text=True
            )
        except subprocess.CalledProcessError:
            print(f"Error: Failed to get package info for '{depend}'.")
        if depend not in all_dependcies_info:
            all_dependcies_info[depend] = {}
        for line in output.splitlines():
            if line.startswith("Source"):
                line = line.removeprefix("Source: ")
                all_dependcies_info[depend]["Source"] = line
            if line.startswith("Depends"):
                all_dependcies_info[depend]["Depend"] = extract_depends(line=line)

    print(all_dependcies_info)
            






        



