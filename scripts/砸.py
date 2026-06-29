#!/usr/bin/env python3
import sys
import io
from pathlib import Path
from pil_utils import BuildImage
from _gif_utils import make_jpg_or_gif

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "砸"

def generate_smash(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    # 加载模板帧
    frame_path = img_dir / "0.png"
    if not frame_path.exists():
        raise FileNotFoundError(f"缺失模板图: {frame_path}")
    frame = BuildImage.open(frame_path)

    user_img = BuildImage.open(image_path)

    # 💡 真正的修复：必须用列表接收，并取出第一张图
    def make(imgs: list) -> BuildImage:
        img = imgs[0]
        points = ((1, 237), (826, 1), (832, 508), (160, 732))
        screen = (
            img
            .convert("RGBA")
            .resize((800, 500), keep_ratio=True)
            .perspective(points)
        )
        return frame.copy().paste(screen, (-136, -81), below=True)

    # 💡 真正的修复：必须把 user_img 用中括号 [] 包成列表传进去！
    result = make_jpg_or_gif([user_img], make)

    # 保存结果
    if isinstance(result, BuildImage):
        result.image.save(output_path)
    else:
        # 处理字节数据或BytesIO
        with open(output_path, "wb") as f:
            if isinstance(result, io.BytesIO):
                f.write(result.getvalue())
            else:
                f.write(result)


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出图片路径
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])

            if not input_file.exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_smash(str(input_file), str(output_file))
            print(f"生成成功！保存至: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)
