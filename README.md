# PkgBlade
The tool is designed to reduce the size and complexity of software packages by selectively removing unnecessary components, dependencies, and files. It aims to create leaner, more efficient distributions for embedded systems, containers, and minimalistic Linux environments.

## background materials
https://cqz7s0ibqo2.feishu.cn/docx/BF41dgmlwo1JOYxrlodcT1yNnoh?from=space_personal_filelist&pre_pathname=%2Fdrive%2Fme%2F&previous_navigation_time=1734935014338

## 脚本运行
+ get_depends: 参数是包名，运行后下载该包依赖源码到生成目录，注意包一定要存在，暂时没做这个判断
+ extract_symbols: 分析软件包，写入需要的符号到symbols.txt。
+ find_symbols_in_code: 需要symbols.txt，以及依赖的目标文件，在curl_o，一个制定文件夹