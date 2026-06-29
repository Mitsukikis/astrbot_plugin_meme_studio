#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage, Text2Image


def convert_to_charpic(image_path: str, output_path: str):
    str_map = "@@$$&B88QMMGW##EE93SPPDOOU**==()+^,\"--''.  "
    num = len(str_map)

    # 计算字符长宽比例
    t2m = Text2Image.from_text("@", 15)
    # 💡 核心修复：将已经被淘汰的 longest_line 直接改为 width
    ratio = t2m.width / t2m.height

    # 加载并处理图片
    img = BuildImage.open(image_path).convert("RGBA").resize_width(150).convert("L")
    img = img.resize((img.width, round(img.height * ratio)))

    # 生成字符画文本
    lines = []
    for y in range(img.height):
        line = []
        for x in range(img.width):
            gray = img.image.getpixel((x, y))
            line.append(str_map[int(num * gray / 256)] if gray != 0 else " ")
        lines.append("".join(line))
    text = "\n".join(lines)

    # 创建字符画图片并保存
    char_image = Text2Image.from_text(text, 15).to_image(bg_color="white")
    char_image.save(output_path)
    print(f"字符画已保存至: {output_path}")


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出图片路径
        if len(sys.argv) >= 3:
            input_file = sys.argv[1]
            output_file = sys.argv[2]

            if not Path(input_file).exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            convert_to_charpic(input_file, output_file)
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)