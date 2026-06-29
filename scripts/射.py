#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image


def resize_cover(img, target_size):
    """保持比例调整图片尺寸，居中裁剪"""
    img_width, img_height = img.size
    target_width, target_height = target_size

    img_ratio = img_width / img_height
    target_ratio = target_width / target_height

    if target_ratio > img_ratio:
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        new_width = target_width
        new_height = int(target_width / img_ratio)

    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = left + target_width
    bottom = top + target_height

    return resized.crop((left, top, right, bottom))


def process_image(input_path, output_path):
    # 💡 核心修复：指向标准的 images 文件夹
    script_dir = Path(__file__).parent.resolve()
    # 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
    frame_dir = script_dir.parent / "data" / "射"

    if not frame_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {frame_dir}")

    frame_files = [frame_dir / f"{i:02d}.png" for i in range(13)]  # 00-12

    # 检查帧文件是否存在
    for frame_file in frame_files:
        if not frame_file.exists():
            raise FileNotFoundError(f"缺少必要的帧文件: {frame_file.name}")

    try:
        # 加载用户图片
        user_img = Image.open(input_path).convert("RGB")
    except Exception as e:
        raise RuntimeError(f"图片加载失败: {e}")

    # 处理每一帧
    frames = []
    for frame_file in frame_files:
        # 加载帧并转换为RGBA
        frame = Image.open(frame_file).convert("RGBA")

        # 调整用户图片尺寸
        resized_user = resize_cover(user_img, frame.size)

        # 创建合成图像
        composite = Image.new("RGBA", frame.size)
        composite.paste(resized_user, (0, 0))  # 用户图片作为背景
        composite.alpha_composite(frame)  # 叠加帧图像

        # 转换为RGB格式
        frames.append(composite.convert("RGB"))

    # 💡 核心修复：使用原生的 PIL.Image 保存动图，脱离 imageio 依赖
    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=150,  # 毫秒
        loop=0,
        disposal=2
    )


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出GIF路径
        if len(sys.argv) >= 3:
            input_file = sys.argv[1]
            output_file = sys.argv[2]

            if not Path(input_file).exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            process_image(input_file, output_file)
            print(f"成功生成GIF文件: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)