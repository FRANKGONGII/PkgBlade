#!/bin/bash

# 检查是否传入包名
if [ -z "$1" ]; then
  echo "Usage: $0 <package_name>"
  exit 1
fi

PACKAGE=$1

# 创建新文件夹用于存放依赖源码
mkdir "depends_source_code_"$1
cd "depends_source_code_"$1

# 创建deps.txt（如果不存在）
touch deps.txt

# 调用 apt show 并提取 Depends 字段
apt show $PACKAGE 2>/dev/null | \
  grep -E '^Depends:' | \
  sed 's/^Depends: //; s/, /\n/g' | \
  awk '{print $1}' > deps.txt


# 下载依赖包源码到当前目录
while read -r dep; do
  apt source "$dep"
done < deps.txt

rm deps.txt
rm *.dsc *.orig.tar.* *.debian.tar.*

# 解释：
# 1. apt show $PACKAGE：获取包的详细信息
# 2. grep '^Depends:'：提取依赖字段
# 3. sed 's/^Depends: //'：去掉字段前缀
# 4. s/, /\n/g：将依赖用换行符分隔
# 5. apt source：下载每个依赖包远吗到当前目录，如果只是要deb包就是download

