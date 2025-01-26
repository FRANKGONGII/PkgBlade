import os
import subprocess
import sys

def process_directory(package_name, current_path):
    # 定义依赖源代码目录（使用绝对路径）
    source_dir = f"{current_path}/depends_source_code_{package_name}"

    # 检查目录是否存在
    if not os.path.isdir(source_dir):
        print(f"Error: Directory '{source_dir}' does not exist.")
        return

    # 遍历 source_dir 的第一层子文件夹
    for item in os.listdir(source_dir):
        full_path = os.path.join(source_dir, item)

        # 只处理子文件夹
        if os.path.isdir(full_path):
            print(f"Processing directory: {full_path}")

            # 判断是否存在 CMakeLists.txt 或 Makefile
            has_cmake = os.path.exists(os.path.join(full_path, "CMakeLists.txt"))
            has_makefile = os.path.exists(os.path.join(full_path, "Makefile"))

            if not has_cmake and not has_makefile:
                print(f"Directory '{full_path}' does not contain CMakeLists.txt or Makefile.")
                continue

            # 创建 build 目录
            build_dir = os.path.join(full_path, "build")
            os.makedirs(build_dir, exist_ok=True)

            # 进入 build 目录
            os.chdir(build_dir)

            if has_cmake:
                print(f"Processing CMake project in: {full_path}")
                try:
                    subprocess.run(["cmake", "-DCMAKE_BUILD_TYPE=Release", ".."], check=True)
                    subprocess.run(["make"], check=True)
                except subprocess.CalledProcessError:
                    print(f"Error: Failed to build project in {full_path} using CMake.")

            elif has_makefile:
                print(f"Processing Makefile project in: {full_path}")
                try:
                    subprocess.run(["make"], check=True)
                except subprocess.CalledProcessError:
                    print(f"Error: Failed to build project in {full_path} using Makefile.")

            # 回到 source_dir
            os.chdir(source_dir)
        else:
            print(f"Skipping non-directory item: {full_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_script.py <package_name>")
        sys.exit(1)

    package_name = sys.argv[1]
    current_path = os.getcwd()
    process_directory(package_name, current_path)
