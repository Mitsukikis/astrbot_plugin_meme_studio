#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "墙纸"


def generate_wallpaper(image_path: str, output_path: str):
    """生成墙纸动画GIF并保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户图片
        user_img = BuildImage.open(image_path).convert("RGBA")
        # 保持比例调整尺寸
        user_img = user_img.resize((515, 383), keep_ratio=True)

        frames: List[IMG] = []

        # 💡 保留原版逻辑：前 8 帧 (0-7) 只有背景
        for i in range(8):
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失背景帧: {i}.png")
            frames.append(BuildImage.open(frame_path).image)

        # 💡 保留原版逻辑：后 12 帧 (8-19) 合成用户图片
        for i in range(8, 20):
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失合成帧: {i}.png")

            frame = BuildImage.open(frame_path)
            # 精确粘贴位置，并垫在背景下方
            frame.paste(user_img, (176, -9), below=True)
            frames.append(frame.image)

        # 💡 核心修复：原生保存为 GIF，替代 save_gif
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=70,  # 0.07秒 = 70毫秒
            loop=0,
            disposal=2
        )
        return True

    except Exception as e:
        raise RuntimeError(f"生成失败: {str(e)}")


if __name__ == "__main__":
    try:
        # 接收外部传入的两个参数：输入图片路径 和 输出GIF路径
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])

            if not input_file.exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            generate_wallpaper(str(input_file), str(output_file))
            print(f"生成成功: {output_file}")
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)