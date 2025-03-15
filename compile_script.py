import os
import subprocess
import sys


has_compile = set()


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

def compile_with_cmake(folder_path):
    build_dir = os.path.join(folder_path, "build")
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    
    try:
        # 进入 build 目录并执行 cmake 和 make
        subprocess.check_call(["cmake", "..", "-DCMAKE_BUILD_TYPE=Release"], cwd=build_dir)
        subprocess.check_call(["make"], cwd=build_dir)
        return True
    except subprocess.CalledProcessError as e:
        print(f"CMake build failed in {folder_path}: {e}")
        return False
    
def compile_with_autotools_Configure(folder_path):
    try:
        # 运行 ./configure
        # 2025/3/13：这些参数还不是都支持的。。干脆改成全部默认算了。。。。
        # subprocess.check_call(["./configure", "CFLAGS=-O2", "CXXFLAGS=-O2", "--with-shared"], cwd=folder_path)
        # 目前只有Openssl是这样的，所有暂时加上shared这个Openssl的构建参数
        subprocess.check_call(["./Configure", "shared"], cwd=folder_path)
    except subprocess.CalledProcessError as e:
        print(f"./configure failed in {folder_path}: {e}")
        return False

    try:
        # 尝试运行 make
        subprocess.check_call(["make"], cwd=folder_path)
        return True
    except subprocess.CalledProcessError:
        print(f"make failed in {folder_path}, attempting to regenerate build files and retry...")
        try:
            # 如果 make 失败，运行 aclocal 和 automake
            subprocess.check_call(["aclocal"], cwd=folder_path)
            subprocess.check_call(["automake"], cwd=folder_path)
            # 再次尝试运行
            # subprocess.check_call(["./configure", "CFLAGS=-O2", "CXXFLAGS=-O2", "--with-shared"], cwd=folder_path)
            subprocess.check_call(["./Configure", "shared"], cwd=folder_path)
            subprocess.check_call(["make"], cwd=folder_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"make failed again in {folder_path}: {e}")
            return False

def compile_with_autotools(folder_path):
    try:
        # 运行 ./configure
        # 2025/3/13：这些参数还不是都支持的。。干脆改成全部默认算了。。。。
        # subprocess.check_call(["./configure", "CFLAGS=-O2", "CXXFLAGS=-O2", "--with-shared"], cwd=folder_path)
        subprocess.check_call(["./configure"], cwd=folder_path)
    except subprocess.CalledProcessError as e:
        print(f"./configure failed in {folder_path}: {e}")
        return False

    try:
        # 尝试运行 make
        subprocess.check_call(["make"], cwd=folder_path)
        return True
    except subprocess.CalledProcessError:
        print(f"make failed in {folder_path}, attempting to regenerate build files and retry...")
        try:
            # 如果 make 失败，运行 aclocal 和 automake
            subprocess.check_call(["aclocal"], cwd=folder_path)
            subprocess.check_call(["automake"], cwd=folder_path)
            # 再次尝试运行
            # subprocess.check_call(["./configure", "CFLAGS=-O2", "CXXFLAGS=-O2", "--with-shared"], cwd=folder_path)
            subprocess.check_call(["./configure"], cwd=folder_path)
            subprocess.check_call(["make"], cwd=folder_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"make failed again in {folder_path}: {e}")
            return False

def compile_with_makefile(folder_path):
    try:
        # 执行 make
        subprocess.check_call(["make"], cwd=folder_path)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Makefile build failed in {folder_path}: {e}")
        return False

def copy_object_files(folder_path, output_dir):
    # 如果输出目录不存在，则创建
    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)
    
    try:
        # 查找所有的 .o 文件并复制到输出目录
        subprocess.check_call(["find", ".", "-type", "f", "-name", "*.o", "-exec", "cp", "-t", output_dir, "{}", "+"], cwd=folder_path)
        print(f"Copied .o files from {folder_path} to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to copy object files from {folder_path}: {e}")

def compile_subfolders(package_name, isCompileAfterTrimming : bool, only_compile : bool):
    root_folder = os.getcwd() + "/depends_source_code_" + package_name
    if root_folder in has_compile:
        return
    has_compile.add(root_folder)
    if only_compile == False:
        get_depends(package_name)
    for subfolder in os.listdir(root_folder):
        # 如果不是最后编译而且已经存在_o的目标文件输出目录，就不用编译了，因为都相当于初始编译
        output_dir = os.path.join(root_folder + "/../", subfolder + "_o")
        if isCompileAfterTrimming == False and os.path.exists(output_dir):
            continue
        subfolder_path = os.path.join(root_folder, subfolder)
        # 写死了glibc不要编译
        if os.path.isdir(subfolder_path) and "glibc" not in subfolder_path:
            print(f"Processing {subfolder_path}...")
            # 2025/3/14：要不对某几个库的构建特殊判断一下？。。
            
            # 检查构建系统
            cmake_lists = os.path.join(subfolder_path, "CMakeLists.txt")
            configure_script = os.path.join(subfolder_path, "configure")
            Configure_script = os.path.join(subfolder_path, "Configure")
            configure_ac_script = os.path.join(subfolder_path, "configure.ac")
            makefile_script = os.path.join(subfolder_path, "Makefile")
            
            if os.path.exists(cmake_lists):
                print("Found CMakeLists.txt, building with CMake...")
                if compile_with_cmake(subfolder_path):
                    copy_object_files(subfolder_path, output_dir)
            elif os.path.exists(configure_script):
                print("Found configure script, building with Autotools...")
                if compile_with_autotools(subfolder_path):
                    copy_object_files(subfolder_path, output_dir)
            elif os.path.exists(Configure_script):
                print("Found Configure script, building with Autotools...")
                if compile_with_autotools_Configure(subfolder_path):
                    copy_object_files(subfolder_path, output_dir)
            elif os.path.exists(configure_ac_script):
                print("Found configure.ac script, building with Autotools...")
                try:
                    # 执行 make
                    subprocess.check_call(["autoreconf", "-i"], cwd=subfolder_path)
                except subprocess.CalledProcessError as e:
                    print("error while building configure")
                if compile_with_autotools(subfolder_path):
                    copy_object_files(subfolder_path, output_dir)
                    
                        
            elif os.path.exists(makefile_script):
                print("Found Makefile script, building with Autotools...")
                if compile_with_makefile(subfolder_path):
                    copy_object_files(subfolder_path, output_dir)
            else:
                print("No build script found!! please check!!")
                
                
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compile_packages.py <folder_path>")
        sys.exit(1)
    
    package_name = sys.argv[1]
    # if not os.path.isdir(folder_path):
    #     print(f"Error: {folder_path} is not a valid directory.")
    #     sys.exit(1)
        
    # 是否要下载自己决定，如果是main跑完后获取产物就不用了--这个情况下面是两个true
    # get_depends(package_name)
    
    compile_subfolders(package_name, True, only_compile=True)