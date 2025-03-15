import sys
import subprocess
import re
import extract_symbols
import find_symbols_in_code
import compile_script
import os


# 当前处理的package名
now_handle_package = set()
# 当前处理的package的依赖
now_handle_package_dependcies = set()
# 所有依赖的信息，格式:
"""
包名package_name : {}
"""
all_dependcies_info = {}

# 记录下载的源码的文件夹名称和包名的联系
"""
libpcre2-8-10 - Source:pcre2 - Folder Name:pcre2-10.39
"""
package_name_2_version = {}

def extract_depends(line: str) -> list:
    """
        从依赖关系字符串中提取软件包名称，去掉版本号要求
        例如 "libgcc-s1, libcrypt1 (>= 1:4.4.10-10ubuntu4)"
        ["libgcc-s1", "libcrypt1"]
        注意有可能有这种情况：Depends: libc6 (>= 2.34), debconf (>= 0.5) | debconf-2.0
    """
    if line.startswith("Depends"):
        ret = set()
        line = line.removeprefix("Depends: ")
        clean_str = re.sub(r"\s*\([^)]*\)", "", line)
        dependcies = [pkg.strip() for pkg in clean_str.split(",")]
        for i in range(0, len(dependcies)):
            d = dependcies[i]
            if " | " in d:
                # 说明配置了多个可用的依赖，选一个就行了
                dependcies[i] = d.split(" | ")[0]
        for d in dependcies:
            ret.add(d)
        return ret
    else:
        return ret
    

def ifEnd():
    """
        检查是否能结束循环
    """
    return len(now_handle_package) >= 1


def get_o_folders():
    """获取当前目录下所有以 '_o' 结尾的文件夹名称"""
    o_folders = [
        entry
        for entry in os.listdir('.')
        if os.path.isdir(entry) and entry.endswith('_o')
    ]
    return o_folders

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


    iter_cnt = 0
    
    ifInit = True
    while ifEnd():
        # 开始处理
        # 获取源码&开始裁减
        print("now come to iter: ", iter_cnt)
        iter_cnt += 1
        handle_result = {}
        for package_name in now_handle_package:
            print("now handle dependencies of package: ", package_name)
            compile_script.compile_subfolders(package_name, False, False)
            
            print("==================================================================================")
            print("compile ends!")
            extract_symbols.run(package_name, ifInit=ifInit, package_name_2_version=package_name_2_version)
            print("==================================================================================")
            print("extract ends!")
            handle_result.update(find_symbols_in_code.run(package_name))
            print("==================================================================================")
            print("slimming ends!", handle_result)

        # 对于每个依赖获取它们的仓库名字和依赖的依赖
        # TODO：如果没有Source那么需要特殊处理，可能只能用字符串相似度
        print("now_handle_package: ", now_handle_package)
        print("now_handle_dependency: ", now_handle_package_dependcies)
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
        
        # 重新处理handle_result，现在才处理的原因是裁减函数不知道depend的包名
        # 看处理情况
        print("handle result: ", handle_result)
        for depend in all_dependcies_info:
            # debconf直接没有Source，跳过
            if "Source" not in all_dependcies_info[depend]:
                all_dependcies_info[depend]["IfHandle"] = "no"
                continue
            depend_source = all_dependcies_info[depend]["Source"]
            for depend_source_detail in handle_result:
                # 2025/3/12：右边第一个-好像也不对，可能还得是左边第一个，不然右边第一个-前面可能还有版本号。。。
                # 例如：libevent-2.1.12-stable
                if depend_source_detail.split("-")[0] == depend_source:
                    # 这里要额外考虑一种情况，就是以前已经确定是不处理的情况
                    if "IfHandle" in all_dependcies_info[depend] and all_dependcies_info[depend]["IfHandle"] == "no":
                        break
                    all_dependcies_info[depend]["IfHandle"] = handle_result[depend_source_detail]
                    package_name_2_version[depend] = depend_source_detail
                    break

        print("all_dependency_info: ", all_dependcies_info)
        
        # # 2025/3/13：干脆直接全部都编译一下算了
        # # TODO：如果声明了不要编译，感觉最好的办法还是通过相似度判断一下要不要编译，compile加一个参数
        # # difflib.SequenceMatcher 可以计算两个字符串的相似度（基于编辑距离的改进算法）
        # # 目前是写死了glibc不要编译
        # for package_name in now_handle_package:
        #     print("now rehandle dependencies of package: ", package_name)
        #     compile_script.compile_subfolders(package_name, True)
        #     print("compile after trimming ends!")
        #     folder_path = os.getcwd()
        #     output_dir = "./" + package_name + "_so"
        #     if not os.path.exists(output_dir):
        #         os.makedirs(output_dir)
        #     try: 
        #         subprocess.check_call(["find", ".", "-type", "f", "-name", "*.so*", "-exec", "cp", "-t", output_dir, "{}", "+"], cwd=folder_path)
        #         print(f"Copied .o files from {folder_path} to {output_dir}")
        #     except subprocess.CalledProcessError as e:
        #         print(f"Failed to copy object files from {folder_path}: {e}")
            


        now_handle_package.clear()
        for package in now_handle_package_dependcies:
            if "IfHandle" in all_dependcies_info[package] and all_dependcies_info[package]["IfHandle"] == "yes":
                now_handle_package.add(package)
            else:
                print("package: ", package ," has been assigned not to slim")

        now_handle_package_dependcies.clear()

        for package in now_handle_package:
            # 如果这个包被标记为no了，就不用处理了
            if all_dependcies_info[package]["IfHandle"] == "yes":
                for package_depend in all_dependcies_info[package]["Depend"]:
                    now_handle_package_dependcies.add(package_depend)
            else:
                print("package: ", package_name ," has been assigned not to slim")

        ifInit = False
        handle_result.clear()


    # 最后再执行函数级别的裁剪
    print("==================================================================================")
    o_folders = get_o_folders()
    for o_folder in o_folders:
        find_symbols_in_code.functional_trimming(o_folder)
    print("==================================================================================")