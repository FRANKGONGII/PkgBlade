import subprocess
import re
import json

# 目标可执行文件
# 暂时这样写，要不然用参数不好写，路径长
binary_file = "./examples/link_1_lib/example"

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
dynamic_symbols = []
for line in result.stdout.splitlines():
    # 匹配行：过滤出符号地址、库名称、符号名称
    match = re.match(r"^\S+\s+\S+\s+\S+\s+\S+\s+(\S+)\s+(\S+)$", line)
    if match:
        library, symbol = match.groups()
        if library != "UND":  # "UND" 表示未定义符号
            dynamic_symbols.append((symbol, library))

# 输出结果
libraries = []
if dynamic_symbols:
    print(f"{'Symbol':<30} {'Library'}")
    print("-" * 50)
    for symbol, library in dynamic_symbols:
        print(f"{symbol:<30} {library}")
        if library == "Base":
            libraries.append(symbol)
            # 先写入到json文件，等待后续查询
            with open("./output/record.json","w") as f:
                new_dict = {binary_file : libraries}
                json.dump(new_dict,f)
else:
    print("No dynamic symbols found.")
