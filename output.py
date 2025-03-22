import os

def append_or_create_file(filename, content="默认内容", type=""):
    """
    如果文件存在，则将内容追加到文件中；
    如果文件不存在，则创建文件并写入内容。

    :param filename: 要操作的文件名（包括路径）
    :param content: 要写入文件的内容，默认为 "默认内容"
    :param type: 内容类型，如果非空则在每一行内容前添加 "type: "
    :return: None
    """
    try:
        # 如果 type 不为空，则在每一行内容前添加 "type: "
        if type:
            # 将 content 按换行符分割成多行
            lines = content.splitlines()
            # 为每一行添加 "type: " 前缀
            content = "\n".join([f"{type}: {line}" for line in lines])
            # 确保 content 以换行符结尾
            if not content.endswith('\n'):
                content += '\n'
        else:
            # 如果 type 为空，确保 content 以换行符结尾
            if not content.endswith('\n'):
                content += '\n'

        # 检查文件是否存在
        if os.path.isfile(filename):
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(content)
            # 可选：取消注释以显示追加成功的消息
            # print(f"内容已追加到文件 '{filename}' 中。")
        else:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(content)
            # 可选：取消注释以显示文件创建成功的消息
            # print(f"文件 '{filename}' 已创建并写入内容。")
    except Exception as e:
        print(f"操作文件时发生错误: {e}")